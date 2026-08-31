"""
Property-based tests for BorrowingService time and fine arithmetic.

Instead of single hand-picked examples, Hypothesis generates hundreds of
arbitrary clocks, due dates, loan periods, and fine rates, and asserts the
*invariants* that must hold for every combination:

  1. A late return is fined exactly days_late x daily_fine_rate — never more,
     never less — and the member's outstanding fine grows by that amount.
  2. An on-time return is never fined, whatever the clock says.
  3. Fines are never negative.
  4. Returning one day later never yields a smaller fine (monotonicity).
  5. The due date of a new loan is exactly borrow_date + loan_period_days.
  6. Each renewal adds exactly loan_period_days and increments the counter.

freezegun pins the service clock to each generated instant, so these are
deterministic and immune to midnight rollovers.
"""
from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time
from hypothesis import given, settings, strategies as st

from app.schemas.borrow import BorrowCreate
from app.services.borrowing_service import BorrowingService
from tests.test_borrowing_service import (
    make_mock_membership_type,
    make_mock_member,
    make_mock_copy,
    make_mock_borrow_record,
    make_service,
)

# Freezegun + heavy example counts can brush against Hypothesis's per-example
# deadline on slow CI machines; the invariants are about arithmetic, not speed.
COMMON_SETTINGS = dict(max_examples=50, deadline=None)

instants = st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2039, 12, 31))
rates = st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False)


def _late_return_service(due_date, rate):
    """Wire a service whose borrow #1 is unreturned and due on `due_date`."""
    record = make_mock_borrow_record(due_date=due_date, returned=False)
    record.member.membership_type.daily_fine_rate = rate
    svc = make_service()
    svc.borrow_repo.get.return_value = record
    svc.reservation_repo.get_next_waiting.return_value = None
    return svc, record


# ---------------------------------------------------------------------------
# Fine calculation properties
# ---------------------------------------------------------------------------

class TestFineProperties:
    @settings(**COMMON_SETTINGS)
    @given(
        due=instants,
        days_late=st.integers(min_value=0, max_value=365),
        rate=rates,
    )
    def test_fine_is_exactly_days_late_times_rate(self, due, days_late, rate):
        # Land 6 hours into the late day so whole-day truncation is unambiguous.
        return_time = due + timedelta(days=days_late, hours=6)
        svc, record = _late_return_service(due, rate)

        with freeze_time(return_time):
            result = svc.return_book(1)

        assert result.fine_amount == pytest.approx(days_late * rate)
        assert record.member.outstanding_fine == pytest.approx(days_late * rate)

    @settings(**COMMON_SETTINGS)
    @given(
        due=instants,
        early_by=st.integers(min_value=0, max_value=365),
        rate=rates,
    )
    def test_on_time_return_is_never_fined(self, due, early_by, rate):
        return_time = due - timedelta(days=early_by, hours=6)
        svc, record = _late_return_service(due, rate)

        with freeze_time(return_time):
            result = svc.return_book(1)

        assert result.fine_amount == 0.0
        assert record.member.outstanding_fine == 0.0

    @settings(**COMMON_SETTINGS)
    @given(due=instants, days_late=st.integers(min_value=0, max_value=365), rate=rates)
    def test_fine_is_never_negative(self, due, days_late, rate):
        return_time = due + timedelta(days=days_late, hours=6)
        svc, _ = _late_return_service(due, rate)

        with freeze_time(return_time):
            result = svc.return_book(1)

        assert result.fine_amount >= 0

    @settings(**COMMON_SETTINGS)
    @given(due=instants, days_late=st.integers(min_value=0, max_value=364), rate=rates)
    def test_returning_one_day_later_never_reduces_the_fine(self, due, days_late, rate):
        svc_early, _ = _late_return_service(due, rate)
        svc_late, _ = _late_return_service(due, rate)

        with freeze_time(due + timedelta(days=days_late, hours=6)):
            earlier = svc_early.return_book(1)
        with freeze_time(due + timedelta(days=days_late + 1, hours=6)):
            later = svc_late.return_book(1)

        assert later.fine_amount >= earlier.fine_amount
        assert later.fine_amount - earlier.fine_amount == pytest.approx(rate)


# ---------------------------------------------------------------------------
# Due-date arithmetic properties
# ---------------------------------------------------------------------------

class TestDueDateProperties:
    @settings(**COMMON_SETTINGS)
    @given(
        now=instants,
        loan_days=st.integers(min_value=1, max_value=90),
    )
    def test_new_loan_due_date_is_exactly_loan_period(self, now, loan_days):
        mt = make_mock_membership_type(loan_period_days=loan_days)
        svc = make_service()
        svc.member_repo.get.return_value = make_mock_member(membership_type=mt)
        svc.member_repo.active_borrow_count.return_value = 0
        svc.book_repo.get.return_value = make_mock_copy().book
        svc.book_repo.get_available_copy.return_value = make_mock_copy()
        svc.borrow_repo.add.side_effect = lambda record: record

        with freeze_time(now):
            record = svc.borrow_book(BorrowCreate(book_id=1, member_id=1))

        assert record.due_date == now + timedelta(days=loan_days)

    @settings(**COMMON_SETTINGS)
    @given(
        due=instants,
        loan_days=st.integers(min_value=1, max_value=90),
        renewed=st.integers(min_value=0, max_value=2),
    )
    def test_renewal_extends_due_date_by_exactly_one_period(self, due, loan_days, renewed):
        mt = make_mock_membership_type(loan_period_days=loan_days, max_renewals=5)
        record = make_mock_borrow_record(
            due_date=due, returned=False, renewed_count=renewed
        )
        record.member.membership_type = mt
        svc = make_service()
        svc.borrow_repo.get.return_value = record
        svc.reservation_repo.get_next_waiting.return_value = None

        with freeze_time(due - timedelta(days=1)):
            result = svc.renew_book(1)

        assert result.due_date == due + timedelta(days=loan_days)
        assert result.renewed_count == renewed + 1


# ---------------------------------------------------------------------------
# Frozen-clock boundary examples
# ---------------------------------------------------------------------------

class TestFrozenClockBoundaries:
    """Deterministic edge examples that hand-written clocks often miss."""

    def test_returned_exactly_on_due_date_is_not_fined(self):
        due = datetime(2026, 3, 15, 12, 0, 0)
        svc, record = _late_return_service(due, rate=2.0)

        with freeze_time(due):
            result = svc.return_book(1)

        assert result.fine_amount == 0.0
        assert record.member.outstanding_fine == 0.0

    def test_first_day_past_due_costs_exactly_one_day(self):
        due = datetime(2026, 3, 15, 12, 0, 0)
        svc, _ = _late_return_service(due, rate=2.0)

        with freeze_time(due + timedelta(days=1, minutes=1)):
            result = svc.return_book(1)

        assert result.fine_amount == pytest.approx(2.0)

    def test_fine_counts_full_24h_periods_not_calendar_days(self):
        # 23h59m past due is still within the first day (no fine); 24h01m
        # past due has completed one full day and is fined for it.
        due = datetime(2026, 3, 15, 12, 0, 0)

        svc_a, _ = _late_return_service(due, rate=1.5)
        with freeze_time(due + timedelta(hours=23, minutes=59)):
            almost = svc_a.return_book(1)

        svc_b, _ = _late_return_service(due, rate=1.5)
        with freeze_time(due + timedelta(hours=24, minutes=1)):
            just_past = svc_b.return_book(1)

        assert almost.fine_amount == 0.0
        assert just_past.fine_amount == pytest.approx(1.5)
