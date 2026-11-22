from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", env_prefix="BCR_", env_parse_none_str=""
    )

    app_name: str = "BCR API"
    database_url: PostgresDsn
    battle_max_turns: int = 25
    debug: bool = False
    telegram_bot_id: str
    jwt_secret_key: str
    new_registrations_allowed: bool = True
    league_match_hour_utc: int = 9
    global_default_league_id: int | None = None


settings = Settings()
