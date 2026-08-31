"""
This file imports all models so that:
1) Base.metadata recognizes all tables (for create_all)
2) Relationship strings like relationship("Book") can be resolved at runtime
Import order matters: book before author (since author imports book_authors from book)
"""
from app.models.book import Book, BookCopy, CopyStatus, book_authors
from app.models.author import Author
from app.models.catalog import Publisher, Category
from app.models.membership import MembershipType
from app.models.member import Member
from app.models.borrow import BorrowRecord
from app.models.reservation import Reservation, ReservationStatus
from app.models.user import User, UserRole

__all__ = [
    "Book", "BookCopy", "CopyStatus", "book_authors",
    "Author", "Publisher", "Category", "MembershipType",
    "Member", "BorrowRecord", "Reservation", "ReservationStatus",
    "User", "UserRole",
]
