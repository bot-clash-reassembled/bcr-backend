import datetime
from pydantic import BaseModel, ConfigDict


class NotificationCreate(BaseModel):
    receiver_id: int
    message: str


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receiver_id: int
    date: datetime.datetime
    message: str
