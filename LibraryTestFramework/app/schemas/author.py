from pydantic import BaseModel, field_validator


class AuthorCreate(BaseModel):
    name: str
    nationality: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Author name cannot be empty")
        return v.strip()


class AuthorOut(BaseModel):
    id: int
    name: str
    nationality: str | None = None

    class Config:
        from_attributes = True
