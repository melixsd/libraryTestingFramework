"""
Integration tests using FastAPI TestClient with in-memory SQLite.

Each test gets a fresh database so tests are isolated from each other.
These tests exercise the full HTTP stack: router -> service -> repository -> database.

All DB fixtures and seed helpers live in tests/conftest.py.
"""
import pytest

from tests.factories import BookFactory, MemberFactory


# ==================================================================
# Auth flow tests
# ==================================================================

class TestAuthFlow:
    """Full authentication flow: register -> admin approval -> login -> /me."""

    def test_register_and_login(self, db_session):
        from tests.helpers import (
            _seed_membership_type, _seed_admin_user, _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db)
        _seed_admin_user(db)

        c = _client()
        # Register
        member_data = MemberFactory.build(membership_type_id=mt.id)
        resp = c.post("/auth/register", json={
            "username": "newuser",
            "email": member_data["email"],
            "password": "password123",
            "full_name": member_data["full_name"],
            "membership_type_id": member_data["membership_type_id"],
        })
        assert resp.status_code == 201
        user_data = resp.json()
        assert user_data["username"] == "newuser"
        assert user_data["role"] == "member"

        # A fresh signup is pending: login is refused until an admin approves it
        resp = c.post(
            "/auth/login",
            data={"username": "newuser", "password": "password123"},
        )
        assert resp.status_code == 401
        assert "pending" in resp.json()["detail"].lower()

        # Admin sees the pending signup in the member list and approves it
        admin_token = _login(c, "admin", "Admin123!")
        members = c.get("/members", headers=_auth_header(admin_token)).json()
        target = next(m for m in members if m["email"] == member_data["email"])
        assert target["is_active"] is False

        resp = c.post(
            f"/members/{target['id']}/approve", headers=_auth_header(admin_token)
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

        # Login now succeeds
        token = _login(c, "newuser", "password123")
        resp = c.get("/auth/me", headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["username"] == "newuser"

    def test_reject_pending_signup_removes_member_and_login(self, db_session):
        from tests.helpers import (
            _seed_membership_type, _seed_admin_user, _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db)
        _seed_admin_user(db)

        c = _client()
        resp = c.post("/auth/register", json={
            "username": "rejectme",
            "email": "rejectme@test.com",
            "password": "password123",
            "full_name": "Rejected User",
            "membership_type_id": mt.id,
        })
        assert resp.status_code == 201

        admin_token = _login(c, "admin", "Admin123!")
        members = c.get("/members", headers=_auth_header(admin_token)).json()
        target = next(m for m in members if m["email"] == "rejectme@test.com")

        resp = c.post(
            f"/members/{target['id']}/reject", headers=_auth_header(admin_token)
        )
        assert resp.status_code == 204

        # The signup is fully removed: no member record and no working login
        members = c.get("/members", headers=_auth_header(admin_token)).json()
        assert all(m["email"] != "rejectme@test.com" for m in members)
        resp = c.post(
            "/auth/login", data={"username": "rejectme", "password": "password123"}
        )
        assert resp.status_code == 401

    def test_approve_member_without_linked_user_succeeds(self, db_session):
        """A pending member record with no login yet can still be approved."""
        from tests.helpers import _seed_membership_type, _seed_admin_user, _login, _auth_header, _client
        from app.models import Member
        db = db_session
        mt = _seed_membership_type(db)
        _seed_admin_user(db)

        pending = Member(
            full_name="No Login Yet",
            email="nologin@test.com",
            membership_type_id=mt.id,
            is_active=False,
        )
        db.add(pending)
        db.commit()
        db.refresh(pending)

        c = _client()
        admin_token = _login(c, "admin", "Admin123!")
        resp = c.post(
            f"/members/{pending.id}/approve", headers=_auth_header(admin_token)
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    def test_approve_active_member_returns_400(self, db_session):
        """Approving an already-active member violates the approval rule."""
        from tests.helpers import (
            _seed_membership_type, _seed_admin_user, _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db)
        _seed_admin_user(db)

        c = _client()
        admin_token = _login(c, "admin", "Admin123!")
        resp = c.post("/members", json={
            "full_name": "Direct Member",
            "email": "direct@test.com",
            "membership_type_id": mt.id,
        }, headers=_auth_header(admin_token))
        assert resp.status_code == 201
        member_id = resp.json()["id"]

        resp = c.post(
            f"/members/{member_id}/approve", headers=_auth_header(admin_token)
        )
        assert resp.status_code == 400
        assert "already approved" in resp.json()["detail"].lower()

    def test_reject_active_member_returns_400(self, db_session):
        """Only pending registrations may be rejected, never active members."""
        from tests.helpers import (
            _seed_membership_type, _seed_admin_user, _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db)
        _seed_admin_user(db)

        c = _client()
        admin_token = _login(c, "admin", "Admin123!")
        resp = c.post("/members", json={
            "full_name": "Active Member",
            "email": "active@test.com",
            "membership_type_id": mt.id,
        }, headers=_auth_header(admin_token))
        assert resp.status_code == 201
        member_id = resp.json()["id"]

        resp = c.post(
            f"/members/{member_id}/reject", headers=_auth_header(admin_token)
        )
        assert resp.status_code == 400
        assert "pending" in resp.json()["detail"].lower()

    def test_login_wrong_password(self, db_session):
        from tests.helpers import _seed_admin_user, _client
        _seed_admin_user(db_session)
        c = _client()
        resp = c.post(
            "/auth/login",
            data={"username": "admin", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    def test_unauthenticated_access_returns_401(self):
        from tests.helpers import _client
        c = _client()
        resp = c.get("/auth/me")
        assert resp.status_code == 401

    def test_duplicate_registration_returns_400(self, db_session):
        from tests.helpers import _seed_membership_type, _login, _auth_header, _client
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
        from tests.helpers import _seed_admin_user, _seed_author, _login, _auth_header, _client
        db = db_session
        admin = _seed_admin_user(db)
        author = _seed_author(db)
        token = _login(_client(), admin.username, "Admin123!")

        c = _client()
        payload = BookFactory.build(
            author_ids=[author.id],
            number_of_copies=2,
        )
        resp = c.post("/books", json=payload, headers=_auth_header(token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == payload["title"]
        assert data["isbn"] == payload["isbn"]
        assert data["total_copies"] == payload["number_of_copies"]

    def test_list_books(self, db_session):
        from tests.helpers import _seed_author, _seed_book_with_copies, _client
        db = db_session
        author = _seed_author(db)
        _seed_book_with_copies(db, author.id, isbn="3333333333")

        c = _client()
        resp = c.get("/books")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_member_cannot_create_book(self, db_session):
        from tests.helpers import (
            _seed_membership_type, _seed_member_user, _login, _auth_header, _client,
        )
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
        from tests.helpers import _seed_admin_user, _seed_author, _login, _auth_header, _client
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
        from tests.helpers import _seed_admin_user, _seed_author, _seed_book_with_copies, _login, _auth_header, _client
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
        from tests.helpers import (
            _seed_membership_type, _seed_admin_user, _seed_member_user,
            _seed_author, _seed_book_with_copies, _login, _auth_header, _client,
        )
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
        from tests.helpers import (
            _seed_membership_type, _seed_admin_user, _seed_member_user,
            _seed_author, _seed_book_with_copies, _login, _auth_header, _client,
        )
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
        from tests.helpers import (
            _seed_membership_type, _seed_member_user, _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db)
        user, member = _seed_member_user(db, "rba_member", mt.id)
        token = _login(_client(), "rba_member", "Member123!")

        c = _client()
        resp = c.get("/members", headers=_auth_header(token))
        assert resp.status_code == 403

    def test_admin_can_access_members_list(self, db_session):
        from tests.helpers import _seed_admin_user, _login, _auth_header, _client
        db = db_session
        admin = _seed_admin_user(db)
        token = _login(_client(), admin.username, "Admin123!")

        c = _client()
        resp = c.get("/members", headers=_auth_header(token))
        assert resp.status_code == 200

    def test_member_cannot_delete_author(self, db_session):
        from tests.helpers import (
            _seed_membership_type, _seed_member_user, _seed_author,
            _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db)
        _seed_member_user(db, "no_delete", mt.id)
        author = _seed_author(db)
        token = _login(_client(), "no_delete", "Member123!")

        c = _client()
        resp = c.delete(f"/authors/{author.id}", headers=_auth_header(token))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_borrow(self):
        from tests.helpers import _client
        c = _client()
        resp = c.post("/borrow", json={"book_id": 1, "member_id": 1})
        assert resp.status_code == 401

    def test_admin_can_create_author(self, db_session):
        from tests.helpers import _seed_admin_user, _login, _auth_header, _client
        db = db_session
        admin = _seed_admin_user(db)
        token = _login(_client(), admin.username, "Admin123!")

        c = _client()
        resp = c.post("/authors", json={"name": "New Author"},
                       headers=_auth_header(token))
        assert resp.status_code == 201
        assert resp.json()["name"] == "New Author"


# ==================================================================
# Membership plan change
# ==================================================================
class TestMembershipPlanChange:
    """Plan listing, self-service plan changes, and the downgrade rule."""

    def test_list_membership_types_is_public(self, db_session):
        from tests.helpers import _seed_membership_type, _client
        db = db_session
        _seed_membership_type(db, name="Regular")
        _seed_membership_type(db, name="Premium", max_books=10, loan_period_days=30,
                              max_renewals=3, daily_fine_rate=1.5)

        c = _client()
        resp = c.get("/membership-types")
        assert resp.status_code == 200
        names = [t["name"] for t in resp.json()]
        assert "Regular" in names and "Premium" in names

    def test_member_can_change_own_plan(self, db_session):
        from tests.helpers import (
            _seed_membership_type, _seed_member_user, _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db, name="Regular")
        premium = _seed_membership_type(db, name="Premium", max_books=10,
                                        loan_period_days=30, max_renewals=3,
                                        daily_fine_rate=1.5)
        user, member = _seed_member_user(db, "plan_member", mt.id)
        token = _login(_client(), "plan_member", "Member123!")

        c = _client()
        resp = c.patch(f"/members/{member.id}/membership",
                       json={"membership_type_id": premium.id},
                       headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["membership_type"]["name"] == "Premium"

    def test_member_cannot_change_another_members_plan(self, db_session):
        from tests.helpers import (
            _seed_membership_type, _seed_member_user, _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db, name="Regular")
        premium = _seed_membership_type(db, name="Premium", max_books=10,
                                        loan_period_days=30, max_renewals=3,
                                        daily_fine_rate=1.5)
        other_user, other_member = _seed_member_user(db, "plan_owner", mt.id)
        _seed_member_user(db, "plan_attacker", mt.id)
        token = _login(_client(), "plan_attacker", "Member123!")

        c = _client()
        resp = c.patch(f"/members/{other_member.id}/membership",
                       json={"membership_type_id": premium.id},
                       headers=_auth_header(token))
        assert resp.status_code == 403

    def test_admin_can_change_members_plan(self, db_session):
        from tests.helpers import (
            _seed_membership_type, _seed_member_user, _seed_admin_user,
            _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db, name="Regular")
        premium = _seed_membership_type(db, name="Premium", max_books=10,
                                        loan_period_days=30, max_renewals=3,
                                        daily_fine_rate=1.5)
        user, member = _seed_member_user(db, "plan_target", mt.id)
        admin = _seed_admin_user(db)
        token = _login(_client(), admin.username, "Admin123!")

        c = _client()
        resp = c.patch(f"/members/{member.id}/membership",
                       json={"membership_type_id": premium.id},
                       headers=_auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["membership_type"]["name"] == "Premium"

    def test_downgrade_blocked_by_active_borrows(self, db_session):
        from tests.helpers import (
            _seed_membership_type, _seed_member_user, _seed_admin_user, _seed_author,
            _seed_book_with_copies, _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db, name="Regular", max_books=5)
        student = _seed_membership_type(db, name="Student", max_books=3)
        user, member = _seed_member_user(db, "downgrader", mt.id)
        admin = _seed_admin_user(db)
        author = _seed_author(db)

        # Borrow 4 books (allowed on Regular with max_books=5).
        for i in range(4):
            book = _seed_book_with_copies(db, author.id, isbn=f"90{i:09d}", num_copies=1)
            resp = _client().post("/borrow", json={
                "book_id": book.id, "member_id": member.id,
            }, headers=_auth_header(_login(_client(), "downgrader", "Member123!")))
            assert resp.status_code == 201

        # Switching to Student (max 3) must be rejected.
        c = _client()
        resp = c.patch(f"/members/{member.id}/membership",
                       json={"membership_type_id": student.id},
                       headers=_auth_header(_login(_client(), "downgrader", "Member123!")))
        assert resp.status_code == 400
        assert "active borrows" in resp.json()["detail"]

    def test_change_to_same_plan_returns_400(self, db_session):
        from tests.helpers import (
            _seed_membership_type, _seed_member_user, _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db, name="Regular")
        user, member = _seed_member_user(db, "same_plan", mt.id)
        token = _login(_client(), "same_plan", "Member123!")

        c = _client()
        resp = c.patch(f"/members/{member.id}/membership",
                       json={"membership_type_id": mt.id},
                       headers=_auth_header(token))
        assert resp.status_code == 400
        assert "already on" in resp.json()["detail"]

    def test_change_to_unknown_plan_returns_404(self, db_session):
        from tests.helpers import (
            _seed_membership_type, _seed_member_user, _login, _auth_header, _client,
        )
        db = db_session
        mt = _seed_membership_type(db, name="Regular")
        user, member = _seed_member_user(db, "unknown_plan", mt.id)
        token = _login(_client(), "unknown_plan", "Member123!")

        c = _client()
        resp = c.patch(f"/members/{member.id}/membership",
                       json={"membership_type_id": 99999},
                       headers=_auth_header(token))
        assert resp.status_code == 404

    def test_unauthenticated_plan_change_returns_401(self, db_session):
        from tests.helpers import _seed_membership_type, _seed_member_user, _client
        db = db_session
        mt = _seed_membership_type(db, name="Regular")
        user, member = _seed_member_user(db, "noauth_plan", mt.id)

        c = _client()
        resp = c.patch(f"/members/{member.id}/membership",
                       json={"membership_type_id": mt.id})
        assert resp.status_code == 401
