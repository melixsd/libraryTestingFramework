from sqlalchemy.orm import Session
from app.models import Book, BookCopy, CopyStatus, Author, Category
from app.repositories.base import BaseRepository


class BookRepository(BaseRepository[Book]):
    def __init__(self, db: Session):
        super().__init__(db, Book)

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self.db.query(Book).filter(Book.isbn == isbn).first()

    def search_by_title(self, keyword: str) -> list[Book]:
        return self.db.query(Book).filter(Book.title.ilike(f"%{keyword}%")).all()

    def search(self, keyword: str) -> list[Book]:
        search_term = f"%{keyword}%"
        return (
            self.db.query(Book)
            .outerjoin(Book.authors)
            .outerjoin(Book.category)
            .filter(
                (Book.title.ilike(search_term))
                | (Author.name.ilike(search_term))
                | (Category.name.ilike(search_term))
            )
            .distinct()
            .all()
        )

    def add_copies(self, book: Book, count: int) -> None:
        for i in range(1, count + 1):
            self.db.add(BookCopy(book_id=book.id, copy_number=i))
        self.db.commit()

    def get_available_copy(self, book: Book) -> BookCopy | None:
        return next((c for c in book.copies if c.status == CopyStatus.AVAILABLE), None)

    def get_copy(self, copy_id: int) -> BookCopy | None:
        return self.db.query(BookCopy).filter(BookCopy.id == copy_id).first()
