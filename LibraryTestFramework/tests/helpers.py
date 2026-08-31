"""Reusable test setup helpers.

These helpers create deterministic domain objects and API clients without
being pytest fixtures themselves. Keeping them outside conftest.py makes
the test suite easier to discover and reuse explicitly.
"""
from fastapi.testclient import TestClient
from app.core.security import hash_password


def _seed_membership_type(db, **overrides):
    """Create a standard membership type and return it."""
    from app.models.membership import MembershipType
    defaults = dict(
        name="Regular",
        max_books=3,
        loan_period_days=14,
        max_renewals=1,
        daily_fine_rate=0.5,
    )
    defaults.update(overrides)
    mt = MembershipType(**defaults)
    db.add(mt)
    db.commit()
    db.refresh(mt)
    return mt


def _seed_admin_user(db):
    """Create an admin user and return it."""
    from app.models.user import User, UserRole
    user = User(
        username="admin",
        email="admin@aldenwood.com",
        hashed_password=hash_password("Admin123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _seed_member_user(db, username="member1", membership_type_id=1):
    """Create a member-linked user with a Member record."""
    from app.models.user import User, UserRole
    from app.models.member import Member
    member = Member(
        full_name="Test Member",
        email=f"{username}@test.com",
        membership_type_id=membership_type_id,
        is_active=True,
        outstanding_fine=0.0,
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    user = User(
        username=username,
        email=f"{username}@test.com",
        hashed_password=hash_password("Member123!"),
        role=UserRole.MEMBER,
        is_active=True,
        member_id=member.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, member


def _seed_author(db, name="Test Author"):
    from app.models.author import Author
    author = Author(name=name)
    db.add(author)
    db.commit()
    db.refresh(author)
    return author


def _seed_book_with_copies(db, author_id, isbn="1111111111", num_copies=2, price=20.0):
    """Create a book with copies and return it."""
    from app.models.book import Book, BookCopy, book_authors
    book = Book(
        title="Integration Test Book",
        isbn=isbn,
        price=price,
    )
    db.add(book)
    db.flush()
    db.execute(book_authors.insert().values(book_id=book.id, author_id=author_id))
    for i in range(1, num_copies + 1):
        db.add(BookCopy(book_id=book.id, copy_number=i))
    db.commit()
    db.refresh(book)
    return book


def _login(client, username, password):
    """Helper: login and return the access token."""
    resp = client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


def _auth_header(token):
    """Return an Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}


def _client():
    """Return a fresh TestClient bound to the app."""
    from app.main import app
    return TestClient(app)
