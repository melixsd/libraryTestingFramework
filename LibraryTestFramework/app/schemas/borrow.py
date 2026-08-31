from datetime import datetime
from pydantic import BaseModel


class BorrowCreate(BaseModel):
    book_id: int
    member_id: int


class BorrowOut(BaseModel):
    id: int
    copy_id: int
    member_id: int
    borrow_date: datetime
    due_date: datetime
    return_date: datetime | None = None
    returned: bool
    renewed_count: int
    fine_amount: float

    class Config:
        from_attributes = True
