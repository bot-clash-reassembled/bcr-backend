import logging
import math
import os

from datetime import datetime, timedelta

import geoip2.database
import geoip2.errors
import jwt

from anyio.to_thread import run_sync
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.user import User
from patch.pyjwt import BcrPyJWKClient
from repositories.user import UserRepository

logger = logging.getLogger(__name__)

SESSION_TOKEN_USER_ID_CLAIM = "user_id"
SESSION_TOKEN_ALGORITHM = "HS256"
SESSION_TOKEN_ISSUER = "https://bcr.local"

TELEGRAM_ID_TOKEN_USER_ID_CLAIM = "id"

GEOIP_DB_FILE_NAME = "GeoLite2-Country.mmdb"

_geoip_reader = None

if os.path.exists(GEOIP_DB_FILE_NAME):
    _geoip_reader = geoip2.database.Reader(GEOIP_DB_FILE_NAME)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)

    async def get_user_by_session_token(self, token: str) -> User | None:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[SESSION_TOKEN_ALGORITHM],
                issuer=SESSION_TOKEN_ISSUER,
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Session token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid session token: {str(e)}")
            return None

        return await self.users.get_by_id(payload[SESSION_TOKEN_USER_ID_CLAIM])

    async def get_user_by_telegram_id_token(self, id_token: str):
        # Fetch public keys and verify token
        jwks_client = BcrPyJWKClient(
            "https://oauth.telegram.org/.well-known/jwks.json",
            # This should ensure we don't get compressed response, but it doesn't always work
            headers={"Accept-Encoding": "identity"},
        )

        try:
            signing_key = await run_sync(
                jwks_client.get_signing_key_from_jwt,
                id_token,
            )
            payload = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.telegram_bot_id,
                issuer="https://oauth.telegram.org",
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Telegram ID token has expired")
            return None, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid Telegram ID token: {str(e)}")
            return None, None

        user_by_token = await self.users.get_by_telegram_id(
            payload[TELEGRAM_ID_TOKEN_USER_ID_CLAIM]
        )
        return user_by_token, payload

    async def register_new_user_via_telegram(
        self, id_token_payload, user_ip
    ) -> User | None:
        new_user = await self.users.create(
            id_token_payload["name"],
            id_token_payload[TELEGRAM_ID_TOKEN_USER_ID_CLAIM],
            id_token_payload["preferred_username"],
        )
        new_user.country_code = self._lookup_country_code(user_ip)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    def create_user_session_token(self, user: User) -> tuple[str, int]:
        token_lifespan = timedelta(days=30)
        payload = {
            SESSION_TOKEN_USER_ID_CLAIM: user.id,
            "exp": datetime.utcnow() + token_lifespan,
            "iss": SESSION_TOKEN_ISSUER,
        }
        session_token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=SESSION_TOKEN_ALGORITHM,
        )
        return session_token, math.floor(token_lifespan.total_seconds())

    @staticmethod
    def _lookup_country_code(ip_address):
        if ip_address is None or _geoip_reader is None:
            return None

        try:
            response = _geoip_reader.country(ip_address)
            return response.country.iso_code
        except geoip2.errors.AddressNotFoundError:
            return None
