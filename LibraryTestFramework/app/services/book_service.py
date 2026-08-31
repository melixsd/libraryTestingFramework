from app.core.exceptions import NotFoundError, DuplicateError, BusinessRuleError
from app.models import Book, BookCopy, CopyStatus
from app.repositories.book_repository import BookRepository
from app.repositories.catalog_repository import AuthorRepository
from app.schemas.book import BookCreate


class BookService:
    def __init__(self, book_repo: BookRepository, author_repo: AuthorRepository):
        self.book_repo = book_repo
        self.author_repo = author_repo

    def create_book(self, data: BookCreate) -> Book:
        if self.book_repo.get_by_isbn(data.isbn):
            raise DuplicateError("ISBN is duplicate")

        authors = self.author_repo.get_by_ids(data.author_ids)
        if len(authors) != len(set(data.author_ids)):
            raise NotFoundError("One or more authors not found")

        book = Book(
            title=data.title,
            isbn=data.isbn,
            price=data.price,
            publication_year=data.publication_year,
            description=data.description,
            publisher_id=data.publisher_id,
            category_id=data.category_id,
            authors=authors,
        )
        book = self.book_repo.add(book)
        self.book_repo.add_copies(book, data.number_of_copies)
        self.book_repo.db.refresh(book)
        return book

    def get_book(self, book_id: int) -> Book:
        book = self.book_repo.get(book_id)
        if not book:
            raise NotFoundError("Book not found")
        return book

    def list_books(self, search: str | None = None) -> list[Book]:
        if search:
            return self.book_repo.search(search)
        return self.book_repo.get_all()

    def add_copies(self, book_id: int, count: int) -> Book:
        book = self.get_book(book_id)
        if count < 1:
            raise BusinessRuleError("Count must be at least 1")
        start_num = book.total_copies + 1
        for i in range(count):
            self.book_repo.db.add(BookCopy(book_id=book.id, copy_number=start_num + i))
        self.book_repo.db.commit()
        self.book_repo.db.refresh(book)
        return book

    def remove_copy(self, book_id: int, copy_id: int) -> Book:
        book = self.get_book(book_id)
        copy = self.book_repo.get_copy(copy_id)
        if not copy or copy.book_id != book.id:
            raise NotFoundError("Copy not found")
        if copy.status == CopyStatus.BORROWED:
            raise BusinessRuleError("Copy is currently borrowed and cannot be removed")
        self.book_repo.db.delete(copy)
        self.book_repo.db.commit()
        self.book_repo.db.refresh(book)
        return book
