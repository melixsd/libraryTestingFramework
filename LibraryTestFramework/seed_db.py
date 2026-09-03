"""Seed a realistic development database with repeatable mock data.

Run from the project root:
    python seed_db.py

The script is idempotent: existing records are reused by username/email/ISBN/name.
All seeded member accounts use password: Member123!
"""
from datetime import datetime, timedelta

from app.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models import (
    User, UserRole, Member, MembershipType, Book, BookCopy, CopyStatus,
    Author, Publisher, Category, BorrowRecord, Reservation,
)

Base.metadata.create_all(bind=engine)


def get_or_create(db, model, defaults=None, **filters):
    instance = db.query(model).filter_by(**filters).first()
    if instance:
        return instance, False
    instance = model(**{**filters, **(defaults or {})})
    db.add(instance)
    db.flush()
    return instance, True


def seed():
    db = SessionLocal()
    try:
        # ---------- Purge leftovers from previous e2e runs ----------
        # The e2e suite creates throwaway "E2E ..." books through the admin UI
        # and there is no book-delete endpoint, so they accumulate in a
        # long-lived local database. Remove them (with their copies, loans,
        # reservations and author links) so the catalogue stays real books.
        e2e_books = db.query(Book).filter(Book.title.like("E2E %")).all()
        for book in e2e_books:
            copy_ids = [
                copy_id for (copy_id,) in db.query(BookCopy.id).filter(
                    BookCopy.book_id == book.id
                ).all()
            ]
            if copy_ids:
                db.query(BorrowRecord).filter(
                    BorrowRecord.copy_id.in_(copy_ids)
                ).delete(synchronize_session=False)
            db.query(Reservation).filter(
                Reservation.book_id == book.id
            ).delete(synchronize_session=False)
            db.query(BookCopy).filter(
                BookCopy.book_id == book.id
            ).delete(synchronize_session=False)
            db.delete(book)
        if e2e_books:
            db.commit()
            print(f"[OK] Purged {len(e2e_books)} leftover e2e book(s).")

        # ---------- Membership types ----------
        student, _ = get_or_create(
            db, MembershipType, name="Student",
            defaults=dict(max_books=3, loan_period_days=14, max_renewals=1,
                          can_reserve=True, daily_fine_rate=0.5),
        )
        regular, _ = get_or_create(
            db, MembershipType, name="Regular",
            defaults=dict(max_books=5, loan_period_days=21, max_renewals=2,
                          can_reserve=True, daily_fine_rate=1.0),
        )
        premium, _ = get_or_create(
            db, MembershipType, name="Premium",
            defaults=dict(max_books=10, loan_period_days=30, max_renewals=3,
                          can_reserve=True, daily_fine_rate=1.5),
        )

        # ---------- Publishers / categories ----------
        oreilly, _ = get_or_create(
            db, Publisher, name="O'Reilly Media",
            defaults=dict(address="Sebastopol, CA"),
        )
        penguin, _ = get_or_create(
            db, Publisher, name="Penguin Books",
            defaults=dict(address="London, UK"),
        )

        fiction, _ = get_or_create(
            db, Category, name="Fiction",
            defaults=dict(is_reference_only=False),
        )
        tech, _ = get_or_create(
            db, Category, name="Technology",
            defaults=dict(is_reference_only=False),
        )
        reference, _ = get_or_create(
            db, Category, name="Reference",
            defaults=dict(is_reference_only=True),
        )

        # ---------- Authors ----------
        author_specs = [
            ("Robert C. Martin", "American"),
            ("George Orwell", "British"),
            ("Donald Knuth", "American"),
            ("J. K. Rowling", "British"),
            ("Jane Austen", "British"),
            ("Agatha Christie", "British"),
            ("Haruki Murakami", "Japanese"),
            ("Gabriel García Márquez", "Colombian"),
            ("Leo Tolstoy", "Russian"),
            ("Fyodor Dostoevsky", "Russian"),
            ("Yuval Noah Harari", "Israeli"),
            ("Mary Shelley", "British"),
            ("F. Scott Fitzgerald", "American"),
            ("Ray Bradbury", "American"),
            ("Isaac Asimov", "American"),
            ("Stephen King", "American"),
            ("Toni Morrison", "American"),
            ("Virginia Woolf", "British"),
            ("Khaled Hosseini", "Afghan-American"),
            ("Paulo Coelho", "Brazilian"),
            ("Simon Singh", "British"),
            ("Andy Weir", "American"),
            ("Frank Herbert", "American"),
            ("J. R. R. Tolkien", "British"),
            ("Aldous Huxley", "British"),
            ("Antoine de Saint-Exupéry", "French"),
        ]
        authors = {}
        for name, nationality in author_specs:
            authors[name], _ = get_or_create(
                db, Author, name=name,
                defaults=dict(nationality=nationality),
            )

        # ---------- Books + copies ----------
        # (title, ISBN, price, year, publisher, category, author names, copies)
        # Copy counts mirror realistic demand: rare/reference titles have a
        # single copy, popular fiction goes up to 10 and 15.
        book_specs = [
            ("Clean Code", "9780132350884", 42.99, 2008, oreilly, tech, ["Robert C. Martin"], 4),
            ("1984", "9780451524935", 15.50, 1949, penguin, fiction, ["George Orwell"], 3),
            ("The Art of Computer Programming, Vol. 1", "9780201896831", 89.99, 1968, oreilly, reference, ["Donald Knuth"], 1),
            ("Harry Potter and the Philosopher's Stone", "9780747532743", 19.99, 1997, penguin, fiction, ["J. K. Rowling"], 10),
            ("Pride and Prejudice", "9780141439518", 12.99, 1813, penguin, fiction, ["Jane Austen"], 4),
            ("Murder on the Orient Express", "9780062693662", 14.99, 1934, penguin, fiction, ["Agatha Christie"], 5),
            ("Norwegian Wood", "9780375704024", 17.99, 1987, penguin, fiction, ["Haruki Murakami"], 2),
            ("One Hundred Years of Solitude", "9780060883287", 18.99, 1967, penguin, fiction, ["Gabriel García Márquez"], 3),
            ("War and Peace", "9780199232765", 24.99, 1869, penguin, fiction, ["Leo Tolstoy"], 2),
            ("Crime and Punishment", "9780486415871", 13.99, 1866, penguin, fiction, ["Fyodor Dostoevsky"], 3),
            ("Sapiens", "9780062316097", 21.99, 2011, penguin, reference, ["Yuval Noah Harari"], 5),
            ("Frankenstein", "9780486282114", 10.99, 1818, penguin, fiction, ["Mary Shelley"], 4),
            ("The Great Gatsby", "9780743273565", 11.99, 1925, penguin, fiction, ["F. Scott Fitzgerald"], 6),
            ("Fahrenheit 451", "9781451678182", 14.99, 1953, penguin, fiction, ["Ray Bradbury"], 4),
            ("Foundation", "9780553293357", 16.99, 1951, penguin, fiction, ["Isaac Asimov"], 3),
            ("The Shining", "9780307743657", 18.99, 1977, penguin, fiction, ["Stephen King"], 3),
            ("Beloved", "9781400033416", 16.99, 1987, penguin, fiction, ["Toni Morrison"], 2),
            ("Mrs Dalloway", "9780156628709", 12.99, 1925, penguin, fiction, ["Virginia Woolf"], 2),
            ("The Kite Runner", "9781594631931", 16.99, 2003, penguin, fiction, ["Khaled Hosseini"], 4),
            ("The Alchemist", "9780062315007", 14.99, 1988, penguin, fiction, ["Paulo Coelho"], 8),
            ("Clean Architecture", "9780134494166", 44.99, 2017, oreilly, tech, ["Robert C. Martin"], 3),
            ("The Pragmatic Programmer", "9780135957059", 49.99, 2019, oreilly, tech, ["Robert C. Martin"], 3),
            ("Introduction to Algorithms", "9780262046305", 79.99, 2022, oreilly, reference, ["Donald Knuth"], 1),
            ("The Code Book", "9780385495325", 22.99, 1999, penguin, tech, ["Simon Singh"], 2),
            ("Design Patterns", "9780201633610", 54.99, 1994, oreilly, tech, ["Robert C. Martin"], 2),
            ("The Martian", "9780804139021", 17.99, 2014, penguin, fiction, ["Andy Weir"], 6),
            ("Dune", "9780441172719", 18.99, 1965, penguin, fiction, ["Frank Herbert"], 7),
            ("The Hobbit", "9780547928227", 15.99, 1937, penguin, fiction, ["J. R. R. Tolkien"], 15),
            ("Brave New World", "9780060850524", 13.99, 1932, penguin, fiction, ["Aldous Huxley"], 3),
            ("The Little Prince", "9780156012195", 10.99, 1943, penguin, fiction, ["Antoine de Saint-Exupéry"], 4),
        ]

        books = {}
        for title, isbn, price, year, publisher, category, author_names, n_copies in book_specs:
            book = db.query(Book).filter(Book.isbn == isbn).first()
            is_new = book is None
            if is_new:
                book = Book(
                    title=title,
                    isbn=isbn,
                    price=price,
                    publication_year=year,
                    publisher_id=publisher.id,
                    category_id=category.id,
                )
                book.authors = [authors[name] for name in author_names]
                db.add(book)
                db.flush()
            elif not book.authors:
                book.authors = [authors[name] for name in author_names]

            # Keep the copy count in line with the spec: create the initial
            # copies for new books and top up when a book was seeded before
            # the spec grew (existing copies and their loan state untouched).
            existing_copies = len(book.copies)
            if existing_copies < n_copies:
                for i in range(existing_copies + 1, n_copies + 1):
                    db.add(BookCopy(book_id=book.id, copy_number=i))
                db.flush()
            books[isbn] = book

        # Keep Clean Code partially checked out for manual reservation/return testing.
        clean_code = books["9780132350884"]
        already_has_active_borrow = (
            db.query(BorrowRecord)
            .join(BookCopy, BorrowRecord.copy_id == BookCopy.id)
            .filter(BookCopy.book_id == clean_code.id, BorrowRecord.returned.is_(False))
            .first()
        )
        borrowed_copy = None
        if not already_has_active_borrow:
            borrowed_copy = next(
                (copy for copy in clean_code.copies if copy.status == CopyStatus.AVAILABLE),
                None,
            )

        # ---------- Members + linked User accounts ----------
        def ensure_member_user(username, email, full_name, membership_type, password):
            member, _ = get_or_create(
                db, Member, email=email,
                defaults=dict(
                    full_name=full_name,
                    is_active=True,
                    membership_type_id=membership_type.id,
                    outstanding_fine=0.0,
                ),
            )
            user, created = get_or_create(
                db, User, username=username,
                defaults=dict(
                    email=email,
                    hashed_password=hash_password(password),
                    role=UserRole.MEMBER,
                    is_active=True,
                    member_id=member.id,
                ),
            )
            if not created and user.member_id is None:
                user.member_id = member.id
            return member, user

        member1, _ = ensure_member_user(
            "member1", "member1@aldenwood.com", "Ali Rezaei", regular, "Member123!"
        )
        member2, _ = ensure_member_user(
            "member2", "member2@aldenwood.com", "Sara Ahmadi", student, "Member123!"
        )

        if member2.outstanding_fine == 0.0:
            member2.outstanding_fine = 3.0

        # 16 additional members = 18 members total.
        additional_members = [
            ("member3", "member3@aldenwood.com", "Nima Karimi", regular),
            ("member4", "member4@aldenwood.com", "Mina Hosseini", student),
            ("member5", "member5@aldenwood.com", "Arman Rahimi", premium),
            ("member6", "member6@aldenwood.com", "Sara Mohammadi", regular),
            ("member7", "member7@aldenwood.com", "Reza Ahmadi", student),
            ("member8", "member8@aldenwood.com", "Yasmin Farhadi", premium),
            ("member9", "member9@aldenwood.com", "Kian Moradi", regular),
            ("member10", "member10@aldenwood.com", "Parisa Ebrahimi", student),
            ("member11", "member11@aldenwood.com", "Amir Hosseini", regular),
            ("member12", "member12@aldenwood.com", "Negin Rahimi", premium),
            ("member13", "member13@aldenwood.com", "Sina Karimi", student),
            ("member14", "member14@aldenwood.com", "Elina Ahmadi", regular),
            ("member15", "member15@aldenwood.com", "Omid Moradi", premium),
            ("member16", "member16@aldenwood.com", "Roya Mohammadi", student),
            ("member17", "member17@aldenwood.com", "Pouya Farhadi", regular),
            ("member18", "member18@aldenwood.com", "Hana Ebrahimi", premium),
        ]
        for username, email, full_name, membership in additional_members:
            ensure_member_user(username, email, full_name, membership, "Member123!")

        if borrowed_copy:
            borrowed_copy.status = CopyStatus.BORROWED
            db.add(BorrowRecord(
                copy_id=borrowed_copy.id,
                member_id=member1.id,
                borrow_date=datetime.utcnow() - timedelta(days=5),
                due_date=datetime.utcnow() + timedelta(days=16),
            ))

        # ---------- Staff users ----------
        get_or_create(
            db, User, username="admin",
            defaults=dict(email="admin@aldenwood.com",
                          hashed_password=hash_password("Admin123!"),
                          role=UserRole.ADMIN, is_active=True, member_id=None),
        )
        get_or_create(
            db, User, username="libr1",
            defaults=dict(email="librarian1@aldenwood.com",
                          hashed_password=hash_password("Librarian123!"),
                          role=UserRole.LIBRARIAN, is_active=True, member_id=None),
        )

        db.commit()
        print("[OK] Seed completed.")
        print(f"   catalog: {db.query(Author).count()} authors, {db.query(Book).count()} books, {db.query(BookCopy).count()} copies")
        print(f"   members: {db.query(Member).count()} members")
        print("   admin   / Admin123!      (ADMIN)")
        print("   libr1   / Librarian123!  (LIBRARIAN)")
        print("   member1 / Member123!     (MEMBER — Regular, one book currently borrowed)")
        print("   member2 / Member123!     (MEMBER — Student, 3.0 outstanding fine)")
        print("   member3-member18 / Member123! (additional mock members)")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
