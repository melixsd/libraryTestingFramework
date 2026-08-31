"""
Integration tests using FastAPI TestClient with in-memory SQLite.

Each test gets a fresh database so tests are isolated from each other.
These tests exercise the full HTTP stack: router -> service -> repository -> database.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Import models FIRST so Base.metadata knows all tables
import app.models  # noqa: F401
from app.database import get_db, Base
from app.core.security import hash_password


# --------------- In-memory SQLite engine ---------------

SQLALCHEMY_TEST_URL = "sqlite:///"
test_engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=None,
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Enable foreign keys for SQLite (needed for cascade deletes)
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# --------------- Session-scoped app + DB setup ---------------

@pytest.fixture(scope="session")
def db_tables():
    """Create all tables once for the session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def db_session(db_tables):
    """Provide a fresh session per test and override get_db dependency."""
    from app.main import app

    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    app.dependency_overrides[get_db] = lambda: session
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()


def _seed_membership_type(db):
    """Create a standard membership type and return it."""
    from app.models.membership import MembershipType
    mt = MembershipType(
        name="Regular",
        max_books=3,
        loan_period_days=14,
        max_renewals=1,
        daily_fine_rate=0.5,
    )
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
    return {"Authorization": f"Bearer {token}"}


def _client():
    from app.main import app
    return TestClient(app)


# ==================================================================
# Auth flow tests
# ==================================================================

class TestAuthFlow:
    """Full authentication flow: register -> login -> /me."""

    def test_register_and_login(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)

        c = _client()
        # Register
        resp = c.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "password123",
            "full_name": "New User",
            "membership_type_id": mt.id,
        })
        assert resp.status_code == 201
        user_data = resp.json()
        assert user_data["username"] == "newuser"
        assert user_data["role"] == "member"

        # Login
        token = _login(c, "newuser", "password123")
        assert token is not None

        # Get /me
        resp = c.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["username"] == "newuser"

    def test_login_wrong_password(self, db_session):
        _seed_admin_user(db_session)
        c = _client()
        resp = c.post(
            "/auth/login",
            data={"username": "admin", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_unauthenticated_access_returns_401(self):
        c = _client()
        resp = c.get("/auth/me")
        assert resp.status_code == 401

    def test_duplicate_registration_returns_400(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)

        c = _client()
        payload = {
            "username": "dupuser",
            "email": "dup@test.com",
            "password": "password123",
            "full_name": "Dup User",
            "membership_type_id": mt.id,
        }
        resp1 = c.post("/auth/register", json=payload)
        assert resp1.status_code == 201

        resp2 = c.post("/auth/register", json=payload)
        assert resp2.status_code == 400


# ==================================================================
# Book CRUD tests
# ==================================================================

class TestBookCRUD:
    """Creating books, adding copies, listing."""

    def test_create_book_as_admin(self, db_session):
        db = db_session
        admin = _seed_admin_user(db)
        author = _seed_author(db)
        token = _login(_client(), admin.username, "Admin123!")

        c = _client()
        resp = c.post("/books", json={
            "title": "New Book",
            "isbn": "2222222222",
            "price": 15.0,
            "author_ids": [author.id],
            "number_of_copies": 2,
        }, headers=_auth_header(token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "New Book"
        assert data["total_copies"] == 2

    def test_list_books(self, db_session):
        db = db_session
        author = _seed_author(db)
        _seed_book_with_copies(db, author.id, isbn="3333333333")

        c = _client()
        resp = c.get("/books")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_member_cannot_create_book(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)
        user, member = _seed_member_user(db, "m1", mt.id)
        token = _login(_client(), "m1", "Member123!")

        c = _client()
        resp = c.post("/books", json={
            "title": "Forbidden Book",
            "isbn": "4444444444",
            "price": 10.0,
            "author_ids": [1],
        }, headers=_auth_header(token))
        assert resp.status_code == 403


# ==================================================================
# Author tests
# ==================================================================

class TestAuthorCRUD:
    """Create and delete authors."""

    def test_create_and_delete_author(self, db_session):
        db = db_session
        admin = _seed_admin_user(db)
        token = _login(_client(), admin.username, "Admin123!")

        c = _client()
        # Create
        resp = c.post("/authors", json={"name": "Author to Delete"},
                       headers=_auth_header(token))
        assert resp.status_code == 201
        author_id = resp.json()["id"]

        # List to verify
        resp = c.get("/authors")
        assert any(a["id"] == author_id for a in resp.json())

        # Delete (no books linked)
        resp = c.delete(f"/authors/{author_id}", headers=_auth_header(token))
        assert resp.status_code == 204

    def test_delete_author_with_books_returns_400(self, db_session):
        db = db_session
        admin = _seed_admin_user(db)
        author = _seed_author(db)
        _seed_book_with_copies(db, author.id, isbn="5555555555")
        token = _login(_client(), admin.username, "Admin123!")

        c = _client()
        resp = c.delete(f"/authors/{author.id}", headers=_auth_header(token))
        assert resp.status_code == 400
        assert "books" in resp.json()["detail"].lower()


# ==================================================================
# Borrowing flow tests
# ==================================================================

class TestBorrowingFlow:
    """Borrow -> return -> verify fine."""

    def test_borrow_and_return_book(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)
        admin = _seed_admin_user(db)
        user, member = _seed_member_user(db, "borrower", mt.id)
        author = _seed_author(db)
        book = _seed_book_with_copies(db, author.id, isbn="6666666666", num_copies=1)

        admin_token = _login(_client(), admin.username, "Admin123!")
        member_token = _login(_client(), "borrower", "Member123!")

        c = _client()
        # Borrow
        resp = c.post("/borrow", json={
            "book_id": book.id,
            "member_id": member.id,
        }, headers=_auth_header(member_token))
        assert resp.status_code == 201
        borrow_data = resp.json()
        assert borrow_data["member_id"] == member.id

        # Verify book availability decreased
        resp = c.get(f"/books/{book.id}")
        assert resp.json()["available_copies"] == 0

        # Return (staff only)
        resp = c.post(f"/return/{borrow_data['id']}",
                       headers=_auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["returned"] is True

    def test_borrow_limit_enforced(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)
        mt.max_books = 1
        db.commit()

        admin = _seed_admin_user(db)
        user, member = _seed_member_user(db, "limited", mt.id)
        author = _seed_author(db)
        book1 = _seed_book_with_copies(db, author.id, isbn="7777777777", num_copies=1)
        book2 = _seed_book_with_copies(db, author.id, isbn="8888888888", num_copies=1)

        member_token = _login(_client(), "limited", "Member123!")

        c = _client()
        # First borrow should succeed
        resp = c.post("/borrow", json={
            "book_id": book1.id,
            "member_id": member.id,
        }, headers=_auth_header(member_token))
        assert resp.status_code == 201

        # Second borrow should fail (limit = 1)
        resp = c.post("/borrow", json={
            "book_id": book2.id,
            "member_id": member.id,
        }, headers=_auth_header(member_token))
        assert resp.status_code == 400


# ==================================================================
# Role-based access control tests
# ==================================================================

class TestRoleAccess:
    """Verify that role-based access control works at the API level."""

    def test_member_cannot_access_members_list(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)
        user, member = _seed_member_user(db, "rba_member", mt.id)
        token = _login(_client(), "rba_member", "Member123!")

        c = _client()
        resp = c.get("/members", headers=_auth_header(token))
        assert resp.status_code == 403

    def test_admin_can_access_members_list(self, db_session):
        db = db_session
        admin = _seed_admin_user(db)
        token = _login(_client(), admin.username, "Admin123!")

        c = _client()
        resp = c.get("/members", headers=_auth_header(token))
        assert resp.status_code == 200

    def test_member_cannot_delete_author(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)
        _seed_member_user(db, "no_delete", mt.id)
        author = _seed_author(db)
        token = _login(_client(), "no_delete", "Member123!")

        c = _client()
        resp = c.delete(f"/authors/{author.id}", headers=_auth_header(token))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_borrow(self):
        c = _client()
        resp = c.post("/borrow", json={"book_id": 1, "member_id": 1})
        assert resp.status_code == 401

    def test_admin_can_create_author(self, db_session):
        db = db_session
        admin = _seed_admin_user(db)
        token = _login(_client(), admin.username, "Admin123!")

        c = _client()
        resp = c.post("/authors", json={"name": "New Author"},
                       headers=_auth_header(token))
        assert resp.status_code == 201
        assert resp.json()["name"] == "New Author"
