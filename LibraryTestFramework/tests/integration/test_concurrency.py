"""
Concurrency tests for the borrow flow.

These use REAL threads with SEPARATE database sessions against a shared
file-backed SQLite database — unlike the other integration tests, which run
through a single session. They reproduce the race where two members borrow
the last copy of a book at the same moment:

  1. Both requests read the same copy as AVAILABLE (neither has written yet).
  2. Both create a BorrowRecord and flip the copy to BORROWED.
  3. Both commits succeed -> the physical copy is double-booked.

A partial unique index (one active borrow per copy, enforced by the database
itself) turns the losing commit into an IntegrityError, which the service
translates into the normal "no copies available" business rule.
"""
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database import Base
from app.models import BorrowRecord, CopyStatus, MembershipType, Member, User, UserRole, Book, BookCopy
from app.core.security import hash_password
from app.repositories.book_repository import BookRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.borrow_repository import BorrowRepository
from app.repositories.reservation_repository import ReservationRepository
from app.services.borrowing_service import BorrowingService
from app.core.exceptions import BusinessRuleError
from app.schemas.borrow import BorrowCreate


@pytest.fixture
def race_engine(tmp_path):
    """A file-backed SQLite engine shared by racing threads.

    In-memory SQLite gives every connection its own empty database, and the
    app's StaticPool shares one connection — neither can reproduce a race,
    so this test brings its own file-backed engine instead.
    """
    engine = create_engine(
        f"sqlite:///{tmp_path / 'race.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


def _race_sessionmaker(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


_RACE_SEQ = 0


def _seed_last_copy(engine):
    """Create two members and one book with exactly one copy; return ids."""
    global _RACE_SEQ
    _RACE_SEQ += 1
    run = _RACE_SEQ

    Session = _race_sessionmaker(engine)
    db = Session()
    try:
        mt = db.query(MembershipType).filter_by(name="Regular").first()
        if not mt:
            mt = MembershipType(name="Regular", max_books=5, loan_period_days=21,
                                max_renewals=2, can_reserve=True, daily_fine_rate=1.0)
            db.add(mt)
            db.flush()
        members = []
        for i in (1, 2):
            member = Member(full_name=f"Racer {run}-{i}", email=f"racer{run}-{i}@test.com",
                            membership_type_id=mt.id, is_active=True)
            db.add(member)
            db.flush()
            db.add(User(username=f"racer{run}-{i}", email=member.email,
                        hashed_password=hash_password("Member123!"),
                        role=UserRole.MEMBER, is_active=True, member_id=member.id))
            members.append(member)
        book = Book(title=f"Raced Book {run}", isbn=f"99999999{run:02d}", price=20.0)
        db.add(book)
        db.flush()
        db.add(BookCopy(book_id=book.id, copy_number=1, status=CopyStatus.AVAILABLE))
        db.commit()
        return book.id, [m.id for m in members]
    finally:
        db.close()


def _attempt_borrow(engine, member_id, book_id, barrier):
    """One racer: wait at the barrier, then borrow on a private session."""
    Session = _race_sessionmaker(engine)
    session = Session()
    service = BorrowingService(
        BookRepository(session), MemberRepository(session),
        BorrowRepository(session), ReservationRepository(session),
    )
    barrier.wait(timeout=10)
    try:
        service.borrow_book(BorrowCreate(book_id=book_id, member_id=member_id))
        return "ok"
    except BusinessRuleError as exc:
        return f"blocked: {exc}"
    except Exception as exc:  # noqa: BLE001 - reported verbatim in the assertion
        return f"error: {type(exc).__name__}: {exc}"
    finally:
        session.close()


class TestConcurrentBorrowOfLastCopy:
    def test_only_one_member_gets_the_last_copy(self, race_engine):
        book_id, member_ids = _seed_last_copy(race_engine)
        barrier = threading.Barrier(len(member_ids))

        with ThreadPoolExecutor(max_workers=len(member_ids)) as pool:
            futures = [
                pool.submit(_attempt_borrow, race_engine, member_id, book_id, barrier)
                for member_id in member_ids
            ]
            outcomes = [f.result(timeout=30) for f in futures]

        # Exactly one racer must win; nobody may crash with a raw DB error.
        winners = [o for o in outcomes if o == "ok"]
        assert len(winners) == 1, (
            f"Double-booking race detected: outcomes were {outcomes}. "
            "Two members borrowed the same physical copy."
        )
        for outcome in outcomes:
            if outcome != "ok":
                assert outcome.startswith("blocked"), (
                    f"The loser must fail with a business rule, not a raw error: {outcome}"
                )

        # The database must hold exactly one active borrow for the copy.
        Session = _race_sessionmaker(race_engine)
        db = Session()
        try:
            active = db.scalar(
                select(func.count(BorrowRecord.id)).where(
                    BorrowRecord.copy_id == 1, BorrowRecord.returned == False  # noqa: E712
                )
            )
            assert active == 1, f"{active} active borrow records exist for one physical copy"
            copy = db.get(BookCopy, 1)
            assert copy.status == CopyStatus.BORROWED
        finally:
            db.close()

    def test_race_is_repeatable(self, race_engine):
        """Run the race several times so a scheduler-dependent failure surfaces."""
        for _ in range(5):
            book_id, member_ids = _seed_last_copy(race_engine)
            barrier = threading.Barrier(len(member_ids))

            with ThreadPoolExecutor(max_workers=len(member_ids)) as pool:
                futures = [
                    pool.submit(_attempt_borrow, race_engine, member_id, book_id, barrier)
                    for member_id in member_ids
                ]
                outcomes = [f.result(timeout=30) for f in futures]

            assert outcomes.count("ok") == 1, f"Double-booking detected: {outcomes}"
