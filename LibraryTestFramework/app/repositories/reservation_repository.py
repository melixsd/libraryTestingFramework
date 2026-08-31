from sqlalchemy.orm import Session
from app.models import Reservation, ReservationStatus
from app.repositories.base import BaseRepository


class ReservationRepository(BaseRepository[Reservation]):
    def __init__(self, db: Session):
        super().__init__(db, Reservation)

    def get_next_waiting(self, book_id: int) -> Reservation | None:
        return (
            self.db.query(Reservation)
            .filter(Reservation.book_id == book_id, Reservation.status == ReservationStatus.WAITING)
            .order_by(Reservation.reservation_date.asc())
            .first()
        )

    def get_existing_waiting(self, book_id: int, member_id: int) -> Reservation | None:
        return (
            self.db.query(Reservation)
            .filter(
                Reservation.book_id == book_id,
                Reservation.member_id == member_id,
                Reservation.status == ReservationStatus.WAITING,
            )
            .first()
        )
