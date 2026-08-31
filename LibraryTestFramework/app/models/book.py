"""
Book and BookCopy models.
book_authors is defined here because Book owns the many-to-many relationship with Author.
"""
import enum
from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, Table, Text, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base


class CopyStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BORROWED = "BORROWED"
    RESERVED = "RESERVED"
    LOST = "LOST"
    DAMAGED = "DAMAGED"
    IN_REPAIR = "IN_REPAIR"


book_authors = Table(
    "book_authors",
    Base.metadata,
    Column("book_id", ForeignKey("books.id"), primary_key=True),
    Column("author_id", ForeignKey("authors.id"), primary_key=True),
)


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    isbn = Column(String(20), unique=True, index=True, nullable=False)
    price = Column(Float, nullable=False)
    publication_year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)

    publisher_id = Column(Integer, ForeignKey("publishers.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    publisher = relationship("Publisher", back_populates="books")
    category = relationship("Category", back_populates="books")
    authors = relationship("Author", secondary=book_authors, back_populates="books")
    copies = relationship("BookCopy", back_populates="book", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="book")

    @property
    def total_copies(self) -> int:
        return len(self.copies)

    @property
    def available_copies(self) -> int:
        return sum(1 for c in self.copies if c.status == CopyStatus.AVAILABLE)


class BookCopy(Base):
    __tablename__ = "book_copies"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    copy_number = Column(Integer, nullable=False)
    status = Column(Enum(CopyStatus), default=CopyStatus.AVAILABLE, nullable=False)
    shelf_location = Column(String(50), nullable=True)

    book = relationship("Book", back_populates="copies")
    borrow_records = relationship("BorrowRecord", back_populates="copy")
