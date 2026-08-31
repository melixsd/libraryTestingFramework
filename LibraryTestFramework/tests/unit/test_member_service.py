"""
Unit tests for MemberService.

These tests mock all repository dependencies so no real database is needed.
We test the pure business logic: member creation rules, fine payment,
and membership plan changes (including the downgrade rule).
"""
import pytest
from unittest.mock import MagicMock

from app.services.member_service import MemberService
from app.core.exceptions import NotFoundError, BusinessRuleError, DuplicateError
from app.schemas.member import MemberCreate


# ---------------------------------------------------------------------------
# Helper factory functions
# ---------------------------------------------------------------------------

def make_mock_membership_type(**overrides):
    """Build a mock MembershipType with sensible defaults."""
    defaults = dict(
        id=1,
        name="Regular",
        max_books=5,
        loan_period_days=21,
        max_renewals=2,
        can_reserve=True,
        daily_fine_rate=1.0,
    )
    defaults.update(overrides)
    mt = MagicMock(**defaults)
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
        membership_type_id=1,
    )
    defaults.update(overrides)
    member = MagicMock(**defaults)
    for k, v in defaults.items():
        setattr(member, k, v)
    if not overrides.get("membership_type"):
        member.membership_type = make_mock_membership_type()
    return member


def make_service(member, membership_types=None, active_borrows=0):
    """Build a MemberService wired to in-memory fake repositories."""
    member_repo = MagicMock()
    member_repo.get.return_value = member
    member_repo.active_borrow_count.return_value = active_borrows

    membership_repo = MagicMock()
    types_by_id = {t.id: t for t in (membership_types or [member.membership_type])}
    membership_repo.get.side_effect = lambda tid: types_by_id.get(tid)

    return MemberService(member_repo, membership_repo), member_repo


# ---------------------------------------------------------------------------
# change_membership tests
# ---------------------------------------------------------------------------

class TestChangeMembership:
    """Tests for MemberService.change_membership()."""

    def test_change_to_different_plan_updates_member(self):
        member = make_mock_member(membership_type_id=1)
        premium = make_mock_membership_type(id=2, name="Premium", max_books=10)
        svc, member_repo = make_service(member, membership_types=[premium])

        result = svc.change_membership(member_id=1, new_type_id=2)

        assert result.membership_type_id == 2
        member_repo.db.commit.assert_called_once()

    def test_change_to_same_plan_is_rejected(self):
        member = make_mock_member(membership_type_id=1)
        same_type = member.membership_type
        svc, _ = make_service(member, membership_types=[same_type])

        with pytest.raises(BusinessRuleError, match="already on the Regular plan"):
            svc.change_membership(member_id=1, new_type_id=1)

    def test_unknown_member_raises_not_found(self):
        member_repo = MagicMock()
        member_repo.get.return_value = None
        svc = MemberService(member_repo, MagicMock())

        with pytest.raises(NotFoundError):
            svc.change_membership(member_id=999, new_type_id=2)

    def test_unknown_membership_type_raises_not_found(self):
        member = make_mock_member()
        svc, _ = make_service(member, membership_types=[])

        with pytest.raises(NotFoundError, match="Membership type not found"):
            svc.change_membership(member_id=1, new_type_id=999)

    def test_downgrade_blocked_when_active_borrows_exceed_new_limit(self):
        # Member on Premium (10 books) with 4 active borrows
        # cannot downgrade to Regular (5 -> 3 books).
        member = make_mock_member(membership_type_id=2)
        member.membership_type = make_mock_membership_type(id=2, name="Premium", max_books=10)
        regular = make_mock_membership_type(id=1, name="Regular", max_books=3)
        svc, member_repo = make_service(
            member, membership_types=[regular], active_borrows=4
        )

        with pytest.raises(BusinessRuleError, match="exceeding its limit of 3 books"):
            svc.change_membership(member_id=1, new_type_id=1)
        member_repo.db.commit.assert_not_called()

    def test_downgrade_allowed_within_new_limit(self):
        member = make_mock_member(membership_type_id=2)
        member.membership_type = make_mock_membership_type(id=2, name="Premium", max_books=10)
        regular = make_mock_membership_type(id=1, name="Regular", max_books=3)
        svc, _ = make_service(member, membership_types=[regular], active_borrows=3)

        result = svc.change_membership(member_id=1, new_type_id=1)

        assert result.membership_type_id == 1

    def test_upgrade_allowed_even_with_full_shelf(self):
        # Member on Regular with 5 active borrows (at their current limit)
        # can always upgrade to Premium (10 books).
        member = make_mock_member(membership_type_id=1)
        member.membership_type = make_mock_membership_type(id=1, name="Regular", max_books=5)
        premium = make_mock_membership_type(id=2, name="Premium", max_books=10)
        svc, _ = make_service(member, membership_types=[premium], active_borrows=5)

        result = svc.change_membership(member_id=1, new_type_id=2)

        assert result.membership_type_id == 2


# ---------------------------------------------------------------------------
# pay_fine / create_member regression tests
# ---------------------------------------------------------------------------

class TestPayFine:
    """Tests for MemberService.pay_fine()."""

    def test_pay_fine_reduces_outstanding_fine(self):
        member = make_mock_member(outstanding_fine=8.0)
        svc, _ = make_service(member)

        result = svc.pay_fine(member_id=1, amount=5.0)

        assert result.outstanding_fine == 3.0

    def test_pay_fine_never_goes_negative(self):
        member = make_mock_member(outstanding_fine=2.0)
        svc, _ = make_service(member)

        result = svc.pay_fine(member_id=1, amount=10.0)

        assert result.outstanding_fine == 0.0

    def test_pay_fine_rejects_non_positive_amount(self):
        member = make_mock_member()
        svc, _ = make_service(member)

        with pytest.raises(BusinessRuleError, match="must be positive"):
            svc.pay_fine(member_id=1, amount=0)


class TestCreateMember:
    """Tests for MemberService.create_member()."""

    def test_create_member_with_unknown_membership_type(self):
        member_repo = MagicMock()
        membership_repo = MagicMock()
        membership_repo.get.return_value = None
        svc = MemberService(member_repo, membership_repo)

        with pytest.raises(NotFoundError):
            svc.create_member(MemberCreate(
                full_name="Jane Doe", email="jane@example.com", membership_type_id=99,
            ))

    def test_create_member_with_duplicate_email(self):
        member_repo = MagicMock()
        member_repo.get_by_email.return_value = make_mock_member()
        membership_repo = MagicMock()
        membership_repo.get.return_value = make_mock_membership_type()
        svc = MemberService(member_repo, membership_repo)

        with pytest.raises(DuplicateError):
            svc.create_member(MemberCreate(
                full_name="Jane Doe", email="john@example.com", membership_type_id=1,
            ))
