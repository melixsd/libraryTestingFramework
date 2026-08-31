from pydantic import BaseModel


class PublisherCreate(BaseModel):
    name: str
    address: str | None = None


class PublisherOut(PublisherCreate):
    id: int

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: str
    is_reference_only: bool = False


class CategoryOut(CategoryCreate):
    id: int

    class Config:
        from_attributes = True


class MembershipTypeCreate(BaseModel):
    name: str
    max_books: int = 3
    loan_period_days: int = 14
    max_renewals: int = 1
    can_reserve: bool = True
    daily_fine_rate: float = 0.5


class MembershipTypeOut(MembershipTypeCreate):
    id: int

    class Config:
        from_attributes = True
