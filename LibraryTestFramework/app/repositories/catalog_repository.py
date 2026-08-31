from sqlalchemy.orm import Session
from app.models import Author, Publisher, Category, MembershipType
from app.repositories.base import BaseRepository


class AuthorRepository(BaseRepository[Author]):
    def __init__(self, db: Session):
        super().__init__(db, Author)

    def get_by_ids(self, ids: list[int]) -> list[Author]:
        return self.db.query(Author).filter(Author.id.in_(ids)).all()


class PublisherRepository(BaseRepository[Publisher]):
    def __init__(self, db: Session):
        super().__init__(db, Publisher)


class CategoryRepository(BaseRepository[Category]):
    def __init__(self, db: Session):
        super().__init__(db, Category)


class MembershipTypeRepository(BaseRepository[MembershipType]):
    def __init__(self, db: Session):
        super().__init__(db, MembershipType)
