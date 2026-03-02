from datetime import date
from pydantic import BaseModel, field_validator


class SpaceCreate(BaseModel):
    name: str
    description: str | None = None


class SpaceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class SpaceOut(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class ReservationCreate(BaseModel):
    space_id: int
    reserver_name: str
    date: date
    note: str | None = None

    @field_validator("reserver_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        return v


class ReservationOut(BaseModel):
    id: int
    space_id: int
    reserver_name: str
    date: date
    note: str | None

    model_config = {"from_attributes": True}
