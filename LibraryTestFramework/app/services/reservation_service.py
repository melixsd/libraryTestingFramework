from app.core.time import utc_now
from app.core.exceptions import NotFoundError, BusinessRuleError
from app.models import Reservation
from app.repositories.book_repository import BookRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.reservation_repository import ReservationRepository
from app.schemas.reservation import ReservationCreate


class ReservationService:
    def __init__(
        self,
        book_repo: BookRepository,
        member_repo: MemberRepository,
        reservation_repo: ReservationRepository,
    ):
        self.book_repo = book_repo
        self.member_repo = member_repo
        self.reservation_repo = reservation_repo

    def reserve_book(self, data: ReservationCreate) -> Reservation:
        member = self.member_repo.get(data.member_id)
        if not member:
            raise NotFoundError("Member not found")
        book = self.book_repo.get(data.book_id)
        if not book:
            raise NotFoundError("Book not found")

        if not member.membership_type.can_reserve:
            raise BusinessRuleError("This member's membership type does not allow reservations")
        if book.available_copies > 0:
            raise BusinessRuleError("Copies are available; no need to reserve")
        if self.reservation_repo.get_existing_waiting(book.id, member.id):
            raise BusinessRuleError("This member has already reserved this book")

        res = Reservation(book_id=book.id, member_id=member.id, reservation_date=utc_now())
        return self.reservation_repo.add(res)

    def cancel_reservation(self, reservation_id: int) -> Reservation:
        from app.models import ReservationStatus
        res = self.reservation_repo.get(reservation_id)
        if not res:
            raise NotFoundError("Reservation not found")
        res.status = ReservationStatus.CANCELLED
        self.reservation_repo.db.commit()
        self.reservation_repo.db.refresh(res)
        return res
