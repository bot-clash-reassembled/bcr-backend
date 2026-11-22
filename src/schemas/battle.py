import datetime

from pydantic import BaseModel, ConfigDict


class BattleCreate(BaseModel):
    user_design_id: int


class BattleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime.datetime
    designs: list
    winner_design_id: int | None
