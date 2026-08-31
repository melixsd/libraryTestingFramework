"""
Unit tests for BorrowingService.

These tests mock all repository dependencies so no real database is needed.
We test the pure business logic: borrowing rules, return fine calculation,
renewal limits, reservation handoff, and lost copy handling.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.borrowing_service import BorrowingService, FINE_BLOCK_THRESHOLD, LOST_BOOK_REPLACEMENT_MULTIPLIER
from app.core.exceptions import NotFoundError, BusinessRuleError
from app.models import BorrowRecord, CopyStatus, ReservationStatus
from app.schemas.borrow import BorrowCreate


# ---------------------------------------------------------------------------
# Helper factory functions
# ---------------------------------------------------------------------------

def make_mock_membership_type(**overrides):
    """Build a mock MembershipType with sensible defaults."""
    defaults = dict(
        id=1,
        name="Regular",
        max_books=3,
        loan_period_days=14,
        max_renewals=1,
        can_reserve=True,
        daily_fine_rate=0.5,
    )
    defaults.update(overrides)
    mt = MagicMock(**defaults)
    # Ensure attribute-style access works for all keys
    for k, v in defaults.items():
        setattr(mt, k, v)
    return mt


def make_mock_member(**overrides):
    """Build a mock Member with sensible defaults."""
    defaults = dict(
        id=1,
        full_name="John Doe",
        email="john@example.com",
        is_active=True,
        outstanding_fine=0.0,
    )
    defaults.update(overrides)
    member = MagicMock(**defaults)
    for k, v in defaults.items():
        setattr(member, k, v)
    if not overrides.get("membership_type"):
        member.membership_type = make_mock_membership_type()
    return member


def make_mock_copy(**overrides):
    """Build a mock BookCopy with sensible defaults."""
    defaults = dict(
        id=1,
        book_id=1,
        copy_number=1,
        status=CopyStatus.AVAILABLE,
    )
    defaults.update(overrides)
    copy = MagicMock(**defaults)
    for k, v in defaults.items():
        setattr(copy, k, v)
    if not overrides.get("book"):
        copy.book = make_mock_book()
    return copy


def make_mock_book(**overrides):
    """Build a mock Book with sensible defaults."""
    defaults = dict(
        id=1,
        title="Test Book",
        isbn="1234567890",
        price=20.0,
        copies=[],
        category=None,
    )
    defaults.update(overrides)
    book = MagicMock(**defaults)
    for k, v in defaults.items():
        setattr(book, k, v)
    return book


def make_mock_borrow_record(**overrides):
    """Build a mock BorrowRecord with sensible defaults."""
    defaults = dict(
        id=1,
        copy_id=1,
        member_id=1,
        borrow_date=datetime.utcnow() - timedelta(days=10),
        due_date=datetime.utcnow() + timedelta(days=4),
        return_date=None,
        returned=False,
        renewed_count=0,
        fine_amount=0.0,
    )
    defaults.update(overrides)
    record = MagicMock(**defaults)
    for k, v in defaults.items():
        setattr(record, k, v)
    if not overrides.get("member"):
        record.member = make_mock_member()
    if not overrides.get("copy"):
        record.copy = make_mock_copy()
    return record


def make_service(**repo_overrides):
    """Create a BorrowingService with mock repositories."""
    defaults = dict(
        book_repo=MagicMock(),
        member_repo=MagicMock(),
        borrow_repo=MagicMock(),
        reservation_repo=MagicMock(),
    )
    defaults.update(repo_overrides)
    svc = BorrowingService(**defaults)
    return svc


# ---------------------------------------------------------------------------
# borrow_book tests
# ---------------------------------------------------------------------------

class TestBorrowBook:
    """Tests for BorrowingService.borrow_book()."""

    def test_successful_borrow(self):
        """A valid borrow request succeeds: copy status changes, record is created."""
        member = make_mock_member()
        book = make_mock_book()
        copy = make_mock_copy(book=book)
        book.copies = [copy]

        svc = make_service()
        svc.member_repo.get.return_value = member
        svc.book_repo.get.return_value = book
        svc.book_repo.get_available_copy.return_value = copy
        svc.member_repo.active_borrow_count.return_value = 0
        svc.borrow_repo.add.return_value = make_mock_borrow_record()

        data = BorrowCreate(book_id=1, member_id=1)
        result = svc.borrow_book(data)

        assert copy.status == CopyStatus.BORROWED
        svc.borrow_repo.add.assert_called_once()
        call_arg = svc.borrow_repo.add.call_args[0][0]
        assert call_arg.member_id == 1
        assert call_arg.copy_id == 1

    def test_borrow_member_not_found(self):
        """Borrowing with a non-existent member raises NotFoundError."""
        svc = make_service()
        svc.member_repo.get.return_value = None

        data = BorrowCreate(book_id=1, member_id=999)
        with pytest.raises(NotFoundError, match="Member not found"):
            svc.borrow_book(data)

    def test_borrow_book_not_found(self):
        """Borrowing a non-existent book raises NotFoundError."""
        member = make_mock_member()
        svc = make_service()
        svc.member_repo.get.return_value = member
        svc.book_repo.get.return_value = None

        data = BorrowCreate(book_id=999, member_id=1)
        with pytest.raises(NotFoundError, match="Book not found"):
            svc.borrow_book(data)

    def test_borrow_inactive_member(self):
        """An inactive member cannot borrow books."""
        member = make_mock_member(is_active=False)
        svc = make_service()
        svc.member_repo.get.return_value = member
        svc.book_repo.get.return_value = make_mock_book()

        data = BorrowCreate(book_id=1, member_id=1)
        with pytest.raises(BusinessRuleError, match="inactive"):
            svc.borrow_book(data)

    def test_borrow_fine_threshold_exceeded(self):
        """A member with outstanding fines above the threshold cannot borrow."""
        member = make_mock_member(outstanding_fine=15.0)
        svc = make_service()
        svc.member_repo.get.return_value = member
        svc.book_repo.get.return_value = make_mock_book()

        data = BorrowCreate(book_id=1, member_id=1)
        with pytest.raises(BusinessRuleError, match="unpaid fines"):
            svc.borrow_book(data)

    def test_borrow_fine_exactly_at_threshold_allowed(self):
        """A member with fines exactly at the threshold CAN still borrow (must be >, not >=)."""
        member = make_mock_member(outstanding_fine=FINE_BLOCK_THRESHOLD)
        book = make_mock_book()
        copy = make_mock_copy(book=book)
        book.copies = [copy]

        svc = make_service()
        svc.member_repo.get.return_value = member
        svc.book_repo.get.return_value = book
        svc.book_repo.get_available_copy.return_value = copy
        svc.member_repo.active_borrow_count.return_value = 0
        svc.borrow_repo.add.return_value = make_mock_borrow_record()

        data = BorrowCreate(book_id=1, member_id=1)
        # Should NOT raise
        result = svc.borrow_book(data)
        assert result is not None

    def test_borrow_reference_only_book(self):
        """A reference-only book cannot be borrowed."""
        member = make_mock_member()
        category = MagicMock()
        category.is_reference_only = True
        book = make_mock_book(category=category)

        svc = make_service()
        svc.member_repo.get.return_value = member
        svc.book_repo.get.return_value = book

        data = BorrowCreate(book_id=1, member_id=1)
        with pytest.raises(BusinessRuleError, match="reference only"):
            svc.borrow_book(data)

    def test_borrow_limit_reached(self):
        """A member who has reached their max books cannot borrow more."""
        member = make_mock_member()
        member.membership_type.max_books = 3
        svc = make_service()
        svc.member_repo.get.return_value = member
        svc.book_repo.get.return_value = make_mock_book()
        svc.member_repo.active_borrow_count.return_value = 3

        data = BorrowCreate(book_id=1, member_id=1)
        with pytest.raises(BusinessRuleError, match="borrowing limit"):
            svc.borrow_book(data)

    def test_borrow_no_available_copies(self):
        """Borrowing fails when the book has no available copies."""
        member = make_mock_member()
        svc = make_service()
        svc.member_repo.get.return_value = member
        svc.book_repo.get.return_value = make_mock_book()
        svc.book_repo.get_available_copy.return_value = None
        svc.member_repo.active_borrow_count.return_value = 0

        data = BorrowCreate(book_id=1, member_id=1)
        with pytest.raises(BusinessRuleError, match="No copies available"):
            svc.borrow_book(data)

    def test_borrow_sets_correct_due_date(self):
        """The due date is calculated as today + loan_period_days."""
        member = make_mock_member()
        member.membership_type.loan_period_days = 21
        book = make_mock_book()
        copy = make_mock_copy(book=book)
        book.copies = [copy]

        svc = make_service()
        svc.member_repo.get.return_value = member
        svc.book_repo.get.return_value = book
        svc.book_repo.get_available_copy.return_value = copy
        svc.member_repo.active_borrow_count.return_value = 0
        svc.borrow_repo.add.return_value = make_mock_borrow_record()

        data = BorrowCreate(book_id=1, member_id=1)
        svc.borrow_book(data)

        call_arg = svc.borrow_repo.add.call_args[0][0]
        expected_due = datetime.utcnow() + timedelta(days=21)
        # Allow 1-second tolerance for the comparison
        assert abs((call_arg.due_date - expected_due).total_seconds()) < 2


# ---------------------------------------------------------------------------
# return_book tests
# ---------------------------------------------------------------------------

class TestReturnBook:
    """Tests for BorrowingService.return_book()."""

    def test_on_time_return_no_fine(self):
        """Returning a book on time produces no fine."""
        record = make_mock_borrow_record()
        record.due_date = datetime.utcnow() + timedelta(days=5)

        svc = make_service()
        svc.borrow_repo.get.return_value = record
        svc.reservation_repo.get_next_waiting.return_value = None

        result = svc.return_book(1)

        assert result.returned is True
        assert record.fine_amount == 0.0
        assert record.copy.status == CopyStatus.AVAILABLE
        svc.borrow_repo.db.commit.assert_called_once()

    def test_late_return_calculates_fine(self):
        """Returning a book late calculates fine = days_late * daily_fine_rate."""
        member = make_mock_member()
        member.membership_type.daily_fine_rate = 0.5
        record = make_mock_borrow_record(member=member)
        # Due 5 days ago, borrowed 15 days ago
        record.due_date = datetime.utcnow() - timedelta(days=5)
        record.borrow_date = datetime.utcnow() - timedelta(days=15)

        svc = make_service()
        svc.borrow_repo.get.return_value = record
        svc.reservation_repo.get_next_waiting.return_value = None

        result = svc.return_book(1)

        assert result.returned is True
        assert record.fine_amount == 5 * 0.5  # 5 days * $0.50
        assert member.outstanding_fine == 5 * 0.5

    def test_late_return_zero_fine_rate(self):
        """A late return with a zero daily fine rate adds no fine."""
        member = make_mock_member()
        member.membership_type.daily_fine_rate = 0.0
        record = make_mock_borrow_record(member=member)
        record.due_date = datetime.utcnow() - timedelta(days=10)

        svc = make_service()
        svc.borrow_repo.get.return_value = record
        svc.reservation_repo.get_next_waiting.return_value = None

        svc.return_book(1)
        assert record.fine_amount == 0.0

    def test_return_already_returned(self):
        """Attempting to return an already returned book raises an error."""
        record = make_mock_borrow_record(returned=True)

        svc = make_service()
        svc.borrow_repo.get.return_value = record

        with pytest.raises(BusinessRuleError, match="already been returned"):
            svc.return_book(1)

    def test_return_borrow_not_found(self):
        """Returning a non-existent borrow record raises NotFoundError."""
        svc = make_service()
        svc.borrow_repo.get.return_value = None

        with pytest.raises(NotFoundError, match="Borrow record not found"):
            svc.return_book(999)

    def test_return_with_reservation_handoff(self):
        """When a book is returned and a reservation exists, the copy status becomes RESERVED."""
        record = make_mock_borrow_record()
        reservation = MagicMock()
        reservation.status = ReservationStatus.WAITING

        svc = make_service()
        svc.borrow_repo.get.return_value = record
        svc.reservation_repo.get_next_waiting.return_value = reservation

        result = svc.return_book(1)

        assert record.copy.status == CopyStatus.RESERVED
        assert reservation.status == ReservationStatus.READY
        assert reservation.expiry_date is not None

    def test_return_without_reservation_sets_available(self):
        """When no reservation exists, returned copy becomes AVAILABLE."""
        record = make_mock_borrow_record()

        svc = make_service()
        svc.borrow_repo.get.return_value = record
        svc.reservation_repo.get_next_waiting.return_value = None

        svc.return_book(1)
        assert record.copy.status == CopyStatus.AVAILABLE


# ---------------------------------------------------------------------------
# renew_book tests
# ---------------------------------------------------------------------------

class TestRenewBook:
    """Tests for BorrowingService.renew_book()."""

    def test_successful_renewal(self):
        """A valid renewal extends the due date and increments renewed_count."""
        member = make_mock_member()
        member.membership_type.loan_period_days = 14
        member.membership_type.max_renewals = 2
        record = make_mock_borrow_record(member=member, renewed_count=0)
        original_due = record.due_date

        svc = make_service()
        svc.borrow_repo.get.return_value = record
        svc.reservation_repo.get_next_waiting.return_value = None

        result = svc.renew_book(1)

        assert result.renewed_count == 1
        assert result.due_date == original_due + timedelta(days=14)
        svc.borrow_repo.db.commit.assert_called_once()

    def test_renewal_limit_reached(self):
        """Renewal fails when the max renewal count has been reached."""
        member = make_mock_member()
        member.membership_type.max_renewals = 1
        record = make_mock_borrow_record(member=member, renewed_count=1)

        svc = make_service()
        svc.borrow_repo.get.return_value = record

        with pytest.raises(BusinessRuleError, match="Renewal limit"):
            svc.renew_book(1)

    def test_renewal_blocked_by_reservation(self):
        """Renewal is blocked when another member has a waiting reservation."""
        record = make_mock_borrow_record()
        reservation = MagicMock()

        svc = make_service()
        svc.borrow_repo.get.return_value = record
        svc.reservation_repo.get_next_waiting.return_value = reservation

        with pytest.raises(BusinessRuleError, match="Another member is waiting"):
            svc.renew_book(1)

    def test_renewal_already_returned(self):
        """Cannot renew a book that has been returned."""
        record = make_mock_borrow_record(returned=True)

        svc = make_service()
        svc.borrow_repo.get.return_value = record

        with pytest.raises(BusinessRuleError, match="returned"):
            svc.renew_book(1)

    def test_renewal_borrow_not_found(self):
        """Renewing a non-existent borrow record raises NotFoundError."""
        svc = make_service()
        svc.borrow_repo.get.return_value = None

        with pytest.raises(NotFoundError, match="Borrow record not found"):
            svc.renew_book(999)

    def test_renewal_multiple_times_up_to_limit(self):
        """Can renew multiple times as long as limit is not reached."""
        member = make_mock_member()
        member.membership_type.max_renewals = 3
        record = make_mock_borrow_record(member=member, renewed_count=2)

        svc = make_service()
        svc.borrow_repo.get.return_value = record
        svc.reservation_repo.get_next_waiting.return_value = None

        result = svc.renew_book(1)
        assert result.renewed_count == 3


# ---------------------------------------------------------------------------
# mark_copy_lost tests
# ---------------------------------------------------------------------------

class TestMarkCopyLost:
    """Tests for BorrowingService.mark_copy_lost()."""

    def test_lost_copy_with_active_borrow(self):
        """Marking a lost copy with an active borrow charges a fine of price * 1.5."""
        book = make_mock_book(price=30.0)
        copy = make_mock_copy(book=book)
        member = make_mock_member(outstanding_fine=0.0)
        record = make_mock_borrow_record(copy=copy, member=member)

        svc = make_service()
        svc.book_repo.get_copy.return_value = copy
        svc.borrow_repo.get_active_for_copy.return_value = record

        result = svc.mark_copy_lost(1)

        assert result.status == CopyStatus.LOST
        expected_fine = 30.0 * LOST_BOOK_REPLACEMENT_MULTIPLIER  # 45.0
        assert member.outstanding_fine == expected_fine
        assert record.returned is True

    def test_lost_copy_without_active_borrow(self):
        """Marking a lost copy with no active borrow just changes status, no fine."""
        copy = make_mock_copy()
        member = make_mock_member(outstanding_fine=0.0)

        svc = make_service()
        svc.book_repo.get_copy.return_value = copy
        svc.borrow_repo.get_active_for_copy.return_value = None

        result = svc.mark_copy_lost(1)

        assert result.status == CopyStatus.LOST
        assert member.outstanding_fine == 0.0

    def test_lost_copy_not_found(self):
        """Marking a non-existent copy as lost raises NotFoundError."""
        svc = make_service()
        svc.book_repo.get_copy.return_value = None

        with pytest.raises(NotFoundError, match="Copy not found"):
            svc.mark_copy_lost(999)

    def test_lost_copy_fine_adds_to_existing(self):
        """The lost copy fine is added to the member's existing outstanding fine."""
        book = make_mock_book(price=20.0)
        copy = make_mock_copy(book=book)
        member = make_mock_member(outstanding_fine=5.0)
        record = make_mock_borrow_record(copy=copy, member=member)

        svc = make_service()
        svc.book_repo.get_copy.return_value = copy
        svc.borrow_repo.get_active_for_copy.return_value = record

        svc.mark_copy_lost(1)

        expected_fine = 5.0 + (20.0 * LOST_BOOK_REPLACEMENT_MULTIPLIER)  # 5 + 30 = 35
        assert member.outstanding_fine == expected_fine

    def test_lost_copy_marks_borrow_as_returned(self):
        """When a copy is lost, the active borrow record is marked as returned."""
        copy = make_mock_copy()
        record = make_mock_borrow_record(copy=copy, returned=False)

        svc = make_service()
        svc.book_repo.get_copy.return_value = copy
        svc.borrow_repo.get_active_for_copy.return_value = record

        svc.mark_copy_lost(1)

        assert record.returned is True
        assert record.return_date is not None
