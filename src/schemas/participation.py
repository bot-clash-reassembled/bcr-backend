from pydantic import BaseModel, ConfigDict


class ParticipationCreate(BaseModel):
    design_id: int
    league_id: int | None = None


class ParticipationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    design_id: int
    league_id: int
    battles_total: int
    battles_won: int
