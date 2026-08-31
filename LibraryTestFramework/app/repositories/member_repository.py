from sqlalchemy.orm import Session
from app.models import Member, BorrowRecord, Reservation
from app.repositories.base import BaseRepository


class MemberRepository(BaseRepository[Member]):
    def __init__(self, db: Session):
        super().__init__(db, Member)

    def get_by_email(self, email: str) -> Member | None:
        return self.db.query(Member).filter(Member.email == email).first()

    def active_borrow_count(self, member_id: int) -> int:
        return (
            self.db.query(BorrowRecord)
            .filter(BorrowRecord.member_id == member_id, BorrowRecord.returned.is_(False))
            .count()
        )

    def get_borrows_by_member(self, member_id: int) -> list[BorrowRecord]:
        return (
            self.db.query(BorrowRecord)
            .filter(BorrowRecord.member_id == member_id)
            .order_by(BorrowRecord.borrow_date.desc())
            .all()
        )

    def get_reservations_by_member(self, member_id: int) -> list[Reservation]:
        return (
            self.db.query(Reservation)
            .filter(Reservation.member_id == member_id)
            .order_by(Reservation.reservation_date.desc())
            .all()
        )
