import argparse
import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncSession

from core.db import SessionLocal
from repositories.user import UserRepository
from services.auth import AuthService


async def _get_user_impersonation_cookie(user_id: int):
    session: AsyncSession
    async with SessionLocal() as session:
        try:
            user_repo = UserRepository(session)
            user = await user_repo.get_by_id(user_id)
            if user is None:
                print(f"User with ID {user_id} not found.")
                sys.exit(1)

            auth_service = AuthService(session)
            session_token = auth_service.create_user_session_token(user)
            print("Successfully generated impersonation cookie! 🎉")
            print(session_token)

        except Exception as e:
            print(f"An error occurred: {e}")
            await session.rollback()
            sys.exit(1)

        finally:
            await session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get user impersonation cookie.")
    parser.add_argument("user_id", type=int, help="The user ID to impersonate.")
    args = parser.parse_args()

    asyncio.run(_get_user_impersonation_cookie(args.user_id))
