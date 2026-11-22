from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    telegram_id: str | None
    telegram_username: str | None
    default_league_id: int | None
