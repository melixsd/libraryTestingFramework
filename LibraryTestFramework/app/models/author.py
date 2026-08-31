"""Author model - the book_authors junction table is imported from book.py (many-to-many relationship)"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.book import book_authors


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    nationality = Column(String(80), nullable=True)

    books = relationship("Book", secondary=book_authors, back_populates="authors")
