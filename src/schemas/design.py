from typing import Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class DesignBase(BaseModel):
    name: str = Field(..., max_length=30)
    color: str = Field(..., max_length=7, pattern=r"^#[0-9a-fA-F]{6}$")
    slot: int = Field(..., ge=1, le=5)
    parts: Dict[str, Any]


class DesignCreate(DesignBase):
    pass


class DesignRead(DesignBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
