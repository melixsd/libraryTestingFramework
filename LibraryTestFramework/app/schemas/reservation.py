from datetime import datetime
from pydantic import BaseModel


class ReservationCreate(BaseModel):
    book_id: int
    member_id: int


class ReservationOut(BaseModel):
    id: int
    book_id: int
    member_id: int
    reservation_date: datetime
    status: str
    expiry_date: datetime | None = None

    class Config:
        from_attributes = True
