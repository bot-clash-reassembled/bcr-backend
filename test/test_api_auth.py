import os
import unittest
from unittest.mock import patch

import jwt
from fastapi.testclient import TestClient

os.environ["BCR_DATABASE_URL"] = "postgresql+asyncpg://foo:bar@localhost:5432/baz"
os.environ["BCR_JWT_SECRET_KEY"] = "2WWYI81XMfiUUhiDZqyfneq0jHtKwhZb"
os.environ["BCR_TELEGRAM_BOT_ID"] = "quux"

from models.user import User
from entrypoints.web_api import app


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("services.auth.BcrPyJWKClient")
    @patch("jwt.decode")
    @patch("repositories.user.UserRepository.get_by_telegram_id")
    def test_login_existing_user_success(
        self, mock_repo_get_by_telegram_id, mock_decode, mock_jwk_client
    ):
        # Arrange
        mock_jwk_client.return_value.get_signing_key_from_jwt.return_value.key = (
            "fake_key"
        )
        mock_decode.return_value = {
            "id": "123",
            "name": "Foo",
            "preferred_username": "bar",
            "iss": "https://oauth.telegram.org",
            "aud": "8829704061",
        }
        mock_repo_get_by_telegram_id.return_value = User(
            id=1, full_name="Foo", telegram_id="123", telegram_username="bar"
        )
        payload = {
            "id_token": "fake_token",
        }

        # Act
        response = self.client.post("/api/v1/auth/login_via_telegram", json=payload)

        # Assert
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.json()["id"])
        self.assertEqual("bar", response.json()["telegram_username"])

    @patch("services.auth.BcrPyJWKClient")
    @patch("jwt.decode")
    def test_login_invalid_token(self, mock_decode, mock_jwk_client):
        # Arrange
        mock_jwk_client.return_value.get_signing_key_from_jwt.return_value.key = (
            "fake_key"
        )
        mock_decode.side_effect = jwt.InvalidTokenError("Invalid signature")

        payload = {
            "id_token": "invalid_token",
        }

        # Act
        response = self.client.post("/api/v1/auth/login_via_telegram", json=payload)

        # Assert
        self.assertEqual(400, response.status_code)
        self.assertIn(
            "Telegram ID token is either expired or invalid", response.json()["detail"]
        )
