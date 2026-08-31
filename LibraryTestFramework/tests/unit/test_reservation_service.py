"""
Unit tests for ReservationService.

These tests mock all repository dependencies so no real database is needed.
Covers the reservation business rules: membership eligibility, availability
checks, duplicate-reservation prevention, and cancellation.
"""
import pytest
from unittest.mock import MagicMock

from app.services.reservation_service import ReservationService
from app.core.exceptions import NotFoundError, BusinessRuleError
from app.models import ReservationStatus
from app.schemas.reservation import ReservationCreate


# ---------------------------------------------------------------------------
# Helper factory functions
# ---------------------------------------------------------------------------

def make_mock_member(**overrides):
    defaults = dict(id=1, full_name="Jane Doe", is_active=True)
    defaults.update(overrides)
    member = MagicMock(**defaults)
    for k, v in defaults.items():
        setattr(member, k, v)
    if "membership_type" not in overrides:
        member.membership_type = MagicMock(can_reserve=True)
    return member


def make_mock_book(**overrides):
    defaults = dict(id=1, title="Test Book", available_copies=0)
    defaults.update(overrides)
    book = MagicMock(**defaults)
    for k, v in defaults.items():
        setattr(book, k, v)
    return book


def make_service(**repo_overrides):
    defaults = dict(
        book_repo=MagicMock(),
        member_repo=MagicMock(),
        reservation_repo=MagicMock(),
    )
    defaults.update(repo_overrides)
    return ReservationService(**defaults)


# ---------------------------------------------------------------------------
# reserve_book
# ---------------------------------------------------------------------------

class TestReserveBook:
    def test_reserve_book_success(self):
        member_repo = MagicMock()
        book_repo = MagicMock()
        reservation_repo = MagicMock()

        member_repo.get.return_value = make_mock_member()
        book_repo.get.return_value = make_mock_book(available_copies=0)
        reservation_repo.get_existing_waiting.return_value = None
        reservation_repo.add.side_effect = lambda r: r

        svc = make_service(
            member_repo=member_repo, book_repo=book_repo, reservation_repo=reservation_repo
        )
        data = ReservationCreate(book_id=1, member_id=1)

        result = svc.reserve_book(data)

        reservation_repo.add.assert_called_once()
        assert result.book_id == 1
        assert result.member_id == 1

    def test_reserve_book_member_not_found_raises(self):
        member_repo = MagicMock()
        member_repo.get.return_value = None
        svc = make_service(member_repo=member_repo)

        with pytest.raises(NotFoundError):
            svc.reserve_book(ReservationCreate(book_id=1, member_id=999))

    def test_reserve_book_book_not_found_raises(self):
        member_repo = MagicMock()
        book_repo = MagicMock()
        member_repo.get.return_value = make_mock_member()
        book_repo.get.return_value = None
        svc = make_service(member_repo=member_repo, book_repo=book_repo)

        with pytest.raises(NotFoundError):
            svc.reserve_book(ReservationCreate(book_id=999, member_id=1))

    def test_reserve_book_membership_cannot_reserve_raises(self):
        member_repo = MagicMock()
        book_repo = MagicMock()
        member = make_mock_member()
        member.membership_type = MagicMock(can_reserve=False)
        member_repo.get.return_value = member
        book_repo.get.return_value = make_mock_book(available_copies=0)
        svc = make_service(member_repo=member_repo, book_repo=book_repo)

        with pytest.raises(BusinessRuleError):
            svc.reserve_book(ReservationCreate(book_id=1, member_id=1))

    def test_reserve_book_copies_available_raises(self):
        """You shouldn't be able to reserve a book that you could just borrow."""
        member_repo = MagicMock()
        book_repo = MagicMock()
        member_repo.get.return_value = make_mock_member()
        book_repo.get.return_value = make_mock_book(available_copies=2)
        svc = make_service(member_repo=member_repo, book_repo=book_repo)

        with pytest.raises(BusinessRuleError):
            svc.reserve_book(ReservationCreate(book_id=1, member_id=1))

    def test_reserve_book_duplicate_reservation_raises(self):
        member_repo = MagicMock()
        book_repo = MagicMock()
        reservation_repo = MagicMock()
        member_repo.get.return_value = make_mock_member()
        book_repo.get.return_value = make_mock_book(available_copies=0)
        reservation_repo.get_existing_waiting.return_value = MagicMock()  # already reserved
        svc = make_service(
            member_repo=member_repo, book_repo=book_repo, reservation_repo=reservation_repo
        )

        with pytest.raises(BusinessRuleError):
            svc.reserve_book(ReservationCreate(book_id=1, member_id=1))


# ---------------------------------------------------------------------------
# cancel_reservation
# ---------------------------------------------------------------------------

class TestCancelReservation:
    def test_cancel_reservation_success(self):
        reservation_repo = MagicMock()
        res = MagicMock(status=ReservationStatus.WAITING)
        reservation_repo.get.return_value = res
        svc = make_service(reservation_repo=reservation_repo)

        result = svc.cancel_reservation(reservation_id=1)

        assert result.status == ReservationStatus.CANCELLED
        reservation_repo.db.commit.assert_called_once()

    def test_cancel_reservation_not_found_raises(self):
        reservation_repo = MagicMock()
        reservation_repo.get.return_value = None
        svc = make_service(reservation_repo=reservation_repo)

        with pytest.raises(NotFoundError):
            svc.cancel_reservation(reservation_id=999)
