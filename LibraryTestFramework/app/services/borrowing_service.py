"""
BorrowingService - the core business logic of the project.
All borrowing/return/renewal rules are here and operate on Repositories,
not directly on Session -> meaning this service can be unit-tested with fake/mock repositories
without a real database.
"""
from datetime import timedelta
from app.core.exceptions import NotFoundError, BusinessRuleError
from app.core.time import utc_now
from app.models import BorrowRecord, CopyStatus, ReservationStatus
from app.repositories.book_repository import BookRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.borrow_repository import BorrowRepository
from app.repositories.reservation_repository import ReservationRepository
from app.schemas.borrow import BorrowCreate

FINE_BLOCK_THRESHOLD = 10.0
LOST_BOOK_REPLACEMENT_MULTIPLIER = 1.5


class BorrowingService:
    def __init__(
        self,
        book_repo: BookRepository,
        member_repo: MemberRepository,
        borrow_repo: BorrowRepository,
        reservation_repo: ReservationRepository,
    ):
        self.book_repo = book_repo
        self.member_repo = member_repo
        self.borrow_repo = borrow_repo
        self.reservation_repo = reservation_repo

    def borrow_book(self, data: BorrowCreate) -> BorrowRecord:
        member = self.member_repo.get(data.member_id)
        if not member:
            raise NotFoundError("Member not found")
        book = self.book_repo.get(data.book_id)
        if not book:
            raise NotFoundError("Book not found")

        if not member.is_active:
            raise BusinessRuleError("Member is inactive")

        if member.outstanding_fine > FINE_BLOCK_THRESHOLD:
            raise BusinessRuleError(
                f"Member has unpaid fines exceeding {FINE_BLOCK_THRESHOLD}"
            )

        if book.category and book.category.is_reference_only:
            raise BusinessRuleError("This book is for reference only and cannot be borrowed")

        if self.member_repo.active_borrow_count(member.id) >= member.membership_type.max_books:
            raise BusinessRuleError(
                f"Member has reached the borrowing limit of {member.membership_type.max_books} books"
            )

        copy = self.book_repo.get_available_copy(book)
        if not copy:
            raise BusinessRuleError("No copies available; you can reserve the book")

        copy.status = CopyStatus.BORROWED
        due_date = utc_now() + timedelta(days=member.membership_type.loan_period_days)
        record = BorrowRecord(
            copy_id=copy.id, member_id=member.id,
            borrow_date=utc_now(), due_date=due_date,
        )
        return self.borrow_repo.add(record)

    def return_book(self, borrow_id: int) -> BorrowRecord:
        record = self.borrow_repo.get(borrow_id)
        if not record:
            raise NotFoundError("Borrow record not found")
        if record.returned:
            raise BusinessRuleError("This book has already been returned")

        now = utc_now()
        record.returned = True
        record.return_date = now

        if now > record.due_date:
            days_late = (now - record.due_date).days
            member = record.member
            fine = days_late * member.membership_type.daily_fine_rate
            record.fine_amount = fine
            member.outstanding_fine += fine

        copy = record.copy
        next_reservation = self.reservation_repo.get_next_waiting(copy.book_id)
        if next_reservation:
            copy.status = CopyStatus.RESERVED
            next_reservation.status = ReservationStatus.READY
            next_reservation.expiry_date = now + timedelta(days=2)
        else:
            copy.status = CopyStatus.AVAILABLE

        self.borrow_repo.db.commit()
        self.borrow_repo.db.refresh(record)
        return record

    def renew_book(self, borrow_id: int) -> BorrowRecord:
        record = self.borrow_repo.get(borrow_id)
        if not record:
            raise NotFoundError("Borrow record not found")
        if record.returned:
            raise BusinessRuleError("Book has been returned; cannot be renewed")

        member = record.member
        if record.renewed_count >= member.membership_type.max_renewals:
            raise BusinessRuleError("Renewal limit has been reached")

        if self.reservation_repo.get_next_waiting(record.copy.book_id):
            raise BusinessRuleError("Another member is waiting for this book")

        record.due_date += timedelta(days=member.membership_type.loan_period_days)
        record.renewed_count += 1
        self.borrow_repo.db.commit()
        self.borrow_repo.db.refresh(record)
        return record

    def mark_copy_lost(self, copy_id: int):
        copy = self.book_repo.get_copy(copy_id)
        if not copy:
            raise NotFoundError("Copy not found")

        active_record = self.borrow_repo.get_active_for_copy(copy_id)
        if active_record:
            member = active_record.member
            replacement_cost = copy.book.price * LOST_BOOK_REPLACEMENT_MULTIPLIER
            member.outstanding_fine += replacement_cost
            active_record.returned = True
            active_record.return_date = utc_now()

        copy.status = CopyStatus.LOST
        self.book_repo.db.commit()
        self.book_repo.db.refresh(copy)
        return copy
