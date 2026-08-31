"""
Unit tests for BookService.

These tests mock all repository dependencies so no real database is needed.
Includes regression tests for a bug where invalid-count / borrowed-copy
protection incorrectly raised NotFoundError (-> 404) instead of
BusinessRuleError (-> 400): the book/copy exists, the *action* is what's
disallowed, so a 404 is misleading for API consumers.
"""
import pytest
from unittest.mock import MagicMock

from app.services.book_service import BookService
from app.core.exceptions import NotFoundError, DuplicateError, BusinessRuleError
from app.models import CopyStatus
from app.schemas.book import BookCreate


# ---------------------------------------------------------------------------
# Helper factory functions
# ---------------------------------------------------------------------------

def make_mock_copy(**overrides):
    defaults = dict(id=1, book_id=1, copy_number=1, status=CopyStatus.AVAILABLE)
    defaults.update(overrides)
    copy = MagicMock(**defaults)
    for k, v in defaults.items():
        setattr(copy, k, v)
    return copy


def make_mock_book(**overrides):
    defaults = dict(id=1, title="Test Book", isbn="1234567890", total_copies=2)
    defaults.update(overrides)
    book = MagicMock(**defaults)
    for k, v in defaults.items():
        setattr(book, k, v)
    return book


def make_book_create(**overrides):
    defaults = dict(
        title="New Book",
        isbn="9999999999",
        price=15.0,
        publication_year=2024,
        description=None,
        author_ids=[1],
        publisher_id=None,
        category_id=None,
        number_of_copies=2,
    )
    defaults.update(overrides)
    return BookCreate(**defaults)


def make_service(**repo_overrides):
    defaults = dict(book_repo=MagicMock(), author_repo=MagicMock())
    defaults.update(repo_overrides)
    return BookService(**defaults)


# ---------------------------------------------------------------------------
# create_book
# ---------------------------------------------------------------------------

class TestCreateBook:
    def test_create_book_success(self):
        book_repo = MagicMock()
        author_repo = MagicMock()
        book_repo.get_by_isbn.return_value = None
        author_repo.get_by_ids.return_value = [MagicMock(id=1)]
        book_repo.add.side_effect = lambda b: b

        svc = make_service(book_repo=book_repo, author_repo=author_repo)
        data = make_book_create(author_ids=[1])

        result = svc.create_book(data)

        book_repo.add.assert_called_once()
        book_repo.add_copies.assert_called_once()
        assert result.isbn == "9999999999"

    def test_create_book_duplicate_isbn_raises(self):
        book_repo = MagicMock()
        book_repo.get_by_isbn.return_value = make_mock_book()
        svc = make_service(book_repo=book_repo)

        with pytest.raises(DuplicateError):
            svc.create_book(make_book_create())

    def test_create_book_unknown_author_raises_not_found(self):
        book_repo = MagicMock()
        author_repo = MagicMock()
        book_repo.get_by_isbn.return_value = None
        author_repo.get_by_ids.return_value = []  # none of the given ids exist
        svc = make_service(book_repo=book_repo, author_repo=author_repo)

        with pytest.raises(NotFoundError):
            svc.create_book(make_book_create(author_ids=[999]))


# ---------------------------------------------------------------------------
# add_copies — regression test for NotFoundError -> BusinessRuleError fix
# ---------------------------------------------------------------------------

class TestAddCopies:
    def test_add_copies_success(self):
        book_repo = MagicMock()
        book = make_mock_book(total_copies=2)
        book_repo.get.return_value = book
        svc = make_service(book_repo=book_repo)

        result = svc.add_copies(book_id=1, count=3)

        assert book_repo.db.add.call_count == 3
        book_repo.db.commit.assert_called_once()
        assert result is book

    def test_add_copies_zero_raises_business_rule_error(self):
        """Regression test: count=0 previously raised NotFoundError (404)
        even though the book exists — the count itself is invalid, which
        is a business-rule violation (400), not a missing resource."""
        book_repo = MagicMock()
        book_repo.get.return_value = make_mock_book()
        svc = make_service(book_repo=book_repo)

        with pytest.raises(BusinessRuleError):
            svc.add_copies(book_id=1, count=0)

    def test_add_copies_negative_raises_business_rule_error(self):
        book_repo = MagicMock()
        book_repo.get.return_value = make_mock_book()
        svc = make_service(book_repo=book_repo)

        with pytest.raises(BusinessRuleError):
            svc.add_copies(book_id=1, count=-5)

    def test_add_copies_book_not_found_raises_not_found(self):
        book_repo = MagicMock()
        book_repo.get.return_value = None
        svc = make_service(book_repo=book_repo)

        with pytest.raises(NotFoundError):
            svc.add_copies(book_id=999, count=2)


# ---------------------------------------------------------------------------
# remove_copy — regression test for NotFoundError -> BusinessRuleError fix
# ---------------------------------------------------------------------------

class TestRemoveCopy:
    def test_remove_available_copy_success(self):
        book_repo = MagicMock()
        book = make_mock_book()
        copy = make_mock_copy(status=CopyStatus.AVAILABLE, book_id=book.id)
        book_repo.get.return_value = book
        book_repo.get_copy.return_value = copy
        svc = make_service(book_repo=book_repo)

        result = svc.remove_copy(book_id=book.id, copy_id=copy.id)

        book_repo.db.delete.assert_called_once_with(copy)
        book_repo.db.commit.assert_called_once()
        assert result is book

    def test_remove_borrowed_copy_raises_business_rule_error(self):
        """Regression test: removing a copy that's currently checked out
        previously raised NotFoundError (404) even though the copy clearly
        exists — it's just protected from removal, which is a business
        rule violation (400), not a missing resource."""
        book_repo = MagicMock()
        book = make_mock_book()
        copy = make_mock_copy(status=CopyStatus.BORROWED, book_id=book.id)
        book_repo.get.return_value = book
        book_repo.get_copy.return_value = copy
        svc = make_service(book_repo=book_repo)

        with pytest.raises(BusinessRuleError):
            svc.remove_copy(book_id=book.id, copy_id=copy.id)

        book_repo.db.delete.assert_not_called()

    def test_remove_copy_not_found_raises_not_found(self):
        book_repo = MagicMock()
        book_repo.get.return_value = make_mock_book()
        book_repo.get_copy.return_value = None
        svc = make_service(book_repo=book_repo)

        with pytest.raises(NotFoundError):
            svc.remove_copy(book_id=1, copy_id=999)

    def test_remove_copy_belonging_to_different_book_raises_not_found(self):
        book_repo = MagicMock()
        book = make_mock_book(id=1)
        copy = make_mock_copy(book_id=2)  # copy belongs to a different book
        book_repo.get.return_value = book
        book_repo.get_copy.return_value = copy
        svc = make_service(book_repo=book_repo)

        with pytest.raises(NotFoundError):
            svc.remove_copy(book_id=1, copy_id=copy.id)
