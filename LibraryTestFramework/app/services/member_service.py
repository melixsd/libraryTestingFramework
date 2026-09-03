from app.core.exceptions import NotFoundError, DuplicateError, BusinessRuleError
from app.models import Member, BorrowRecord, Reservation, ReservationStatus
from app.repositories.member_repository import MemberRepository
from app.repositories.catalog_repository import MembershipTypeRepository
from app.schemas.member import MemberCreate


class MemberService:
    def __init__(self, member_repo: MemberRepository, membership_repo: MembershipTypeRepository):
        self.member_repo = member_repo
        self.membership_repo = membership_repo

    def create_member(self, data: MemberCreate) -> Member:
        if not self.membership_repo.get(data.membership_type_id):
            raise NotFoundError("Membership type not found")
        if self.member_repo.get_by_email(data.email):
            raise DuplicateError("This email is already registered")
        return self.member_repo.add(Member(**data.model_dump()))

    def get_member(self, member_id: int) -> Member:
        member = self.member_repo.get(member_id)
        if not member:
            raise NotFoundError("Member not found")
        return member

    def list_members(self) -> list[Member]:
        return self.member_repo.get_all()

    def pay_fine(self, member_id: int, amount: float) -> Member:
        if amount <= 0:
            raise BusinessRuleError("Payment amount must be positive")
        member = self.get_member(member_id)
        member.outstanding_fine = max(0.0, member.outstanding_fine - amount)
        self.member_repo.db.commit()
        self.member_repo.db.refresh(member)
        return member

    def change_membership(self, member_id: int, new_type_id: int) -> Member:
        """Switch a member to a different membership plan.

        A downgrade is rejected while the member's active borrows exceed the
        target plan's borrowing limit; upgrades are always allowed.
        """
        member = self.get_member(member_id)
        new_type = self.membership_repo.get(new_type_id)
        if not new_type:
            raise NotFoundError("Membership type not found")
        if member.membership_type_id == new_type_id:
            raise BusinessRuleError(f"Member is already on the {new_type.name} plan")

        active_borrows = self.member_repo.active_borrow_count(member_id)
        if active_borrows > new_type.max_books:
            raise BusinessRuleError(
                f"Cannot switch to the {new_type.name} plan: the member has "
                f"{active_borrows} active borrows, exceeding its limit of "
                f"{new_type.max_books} books. Some books must be returned first."
            )

        member.membership_type_id = new_type_id
        self.member_repo.db.commit()
        self.member_repo.db.refresh(member)
        return member

    def get_member_summary(self, member_id: int) -> dict:
        member = self.get_member(member_id)
        active_borrows = [b for b in self.member_repo.get_borrows_by_member(member_id) if not b.returned]
        reservations = self.member_repo.get_reservations_by_member(member_id)
        return {
            "member": member,
            # The profile UI shows real book titles, so resolve them here
            # rather than leaking copy/book ids into the member-facing view.
            "active_borrows": [
                {
                    "id": b.id,
                    "copy_id": b.copy_id,
                    "member_id": b.member_id,
                    "borrow_date": b.borrow_date,
                    "due_date": b.due_date,
                    "return_date": b.return_date,
                    "returned": b.returned,
                    "renewed_count": b.renewed_count,
                    "fine_amount": b.fine_amount,
                    "book_title": b.copy.book.title if b.copy and b.copy.book else None,
                }
                for b in active_borrows
            ],
            "reservations": [
                {
                    "id": r.id,
                    "book_id": r.book_id,
                    "member_id": r.member_id,
                    "reservation_date": r.reservation_date,
                    "status": r.status.value if isinstance(r.status, ReservationStatus) else r.status,
                    "expiry_date": r.expiry_date,
                    "book_title": r.book.title if r.book else None,
                }
                for r in reservations
            ],
            "total_fines": member.outstanding_fine,
        }
