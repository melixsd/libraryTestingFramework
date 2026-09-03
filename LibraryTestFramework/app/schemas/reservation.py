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
    # Denormalised for display: the member profile shows the reserved book's
    # title instead of a bare book id. None when not explicitly resolved.
    book_title: str | None = None

    class Config:
        from_attributes = True
