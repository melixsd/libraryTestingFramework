from pydantic import BaseModel, field_validator
from app.schemas.author import AuthorOut


class BookCreate(BaseModel):
    title: str
    isbn: str
    price: float
    publication_year: int | None = None
    description: str | None = None
    author_ids: list[int]
    publisher_id: int | None = None
    category_id: int | None = None
    number_of_copies: int = 1

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Book title cannot be empty")
        return v.strip()

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return v

    @field_validator("isbn")
    @classmethod
    def isbn_format(cls, v: str) -> str:
        cleaned = v.replace("-", "")
        if not cleaned.isdigit() or len(cleaned) not in (10, 13):
            raise ValueError("Invalid ISBN format")
        return v

    @field_validator("number_of_copies")
    @classmethod
    def copies_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Number of copies must be at least 1")
        return v

    @field_validator("author_ids")
    @classmethod
    def at_least_one_author(cls, v: list) -> list:
        if not v:
            raise ValueError("Book must have at least one author")
        return v


class BookOut(BaseModel):
    id: int
    title: str
    isbn: str
    price: float
    publication_year: int | None = None
    authors: list[AuthorOut] = []
    available_copies: int = 0
    total_copies: int = 0

    class Config:
        from_attributes = True
