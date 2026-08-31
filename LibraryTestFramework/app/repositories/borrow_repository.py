from sqlalchemy.orm import Session
from app.models import BorrowRecord
from app.repositories.base import BaseRepository


class BorrowRepository(BaseRepository[BorrowRecord]):
    def __init__(self, db: Session):
        super().__init__(db, BorrowRecord)

    def get_active_for_copy(self, copy_id: int) -> BorrowRecord | None:
        return (
            self.db.query(BorrowRecord)
            .filter(BorrowRecord.copy_id == copy_id, BorrowRecord.returned.is_(False))
            .first()
        )
