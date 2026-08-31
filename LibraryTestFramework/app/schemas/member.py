from pydantic import BaseModel, EmailStr, field_validator
from app.schemas.catalog import MembershipTypeOut
from app.schemas.borrow import BorrowOut
from app.schemas.reservation import ReservationOut


class MemberCreate(BaseModel):
    full_name: str
    email: EmailStr
    membership_type_id: int

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Member name cannot be empty")
        return v.strip()


class MembershipChange(BaseModel):
    """Request body for switching a member to a different membership plan."""
    membership_type_id: int


class MemberOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    outstanding_fine: float
    membership_type: MembershipTypeOut

    class Config:
        from_attributes = True


class MemberSummaryOut(BaseModel):
    member: MemberOut
    active_borrows: list[BorrowOut]
    reservations: list[ReservationOut]
    total_fines: float
