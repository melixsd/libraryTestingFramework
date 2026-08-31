"""Tests for the reusable test-data factories."""

from app.schemas.book import BookCreate
from app.schemas.member import MemberCreate
from tests.factories import BookFactory, BorrowRecordFactory, MemberFactory


def test_book_factory_generates_valid_book_payload():
    payload = BookFactory.build(author_ids=[1])
    book = BookCreate(**payload)

    assert book.title
    assert book.isbn.replace("-", "").isdigit()
    assert len(book.isbn.replace("-", "")) in (10, 13)
    assert book.price > 0
    assert book.number_of_copies >= 1
    assert book.author_ids == [1]


def test_member_factory_generates_valid_member_payload():
    payload = MemberFactory.build(membership_type_id=1)
    member = MemberCreate(**payload)

    assert member.full_name
    assert "@" in member.email
    assert member.membership_type_id == 1


def test_borrow_record_factory_generates_distinct_ids():
    first = BorrowRecordFactory.build()
    second = BorrowRecordFactory.build()

    assert first["copy_id"] != second["copy_id"]
    assert first["member_id"] != second["member_id"]
    assert first["book_id"] != second["book_id"]
