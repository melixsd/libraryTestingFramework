"""
Authentication security tests.

These verify that malformed, expired, tampered, or incorrectly signed JWTs
are rejected at the API boundary, and that valid tokens stop working the
moment their user is deactivated. They complement the RBAC tests: those
prove "who may do what", these prove "the credential itself is sound".
"""
import base64
import json

import jwt as pyjwt

from app.core.config import settings
from app.core.security import create_access_token
from tests.helpers import (
    _seed_membership_type, _seed_member_user, _login, _auth_header, _client,
)


def _b64url(data: bytes) -> str:
    """JWT base64url encoding without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


class TestTokenSecurity:
    """Attack-style checks against the JWT authentication layer."""

    def _me(self, token: str):
        return _client().get("/auth/me", headers=_auth_header(token))

    def test_expired_token_is_rejected(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)
        user, _ = _seed_member_user(db, "sec_expired", mt.id)

        token = create_access_token({"sub": str(user.id)}, expires_minutes=-5)
        assert self._me(token).status_code == 401

    def test_tampered_signature_is_rejected(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)
        _seed_member_user(db, "sec_tamper", mt.id)

        valid = _login(_client(), "sec_tamper", "Member123!")
        header, payload, signature = valid.split(".")
        # Flip the last signature character to a guaranteed-different one.
        forged_sig = signature[:-1] + ("A" if signature[-1] != "A" else "B")
        assert self._me(f"{header}.{payload}.{forged_sig}").status_code == 401

    def test_escalated_payload_without_resigning_is_rejected(self, db_session):
        """Editing the payload (e.g. swapping the user id) must invalidate the token."""
        db = db_session
        mt = _seed_membership_type(db)
        _seed_member_user(db, "sec_escalate", mt.id)

        valid = _login(_client(), "sec_escalate", "Member123!")
        header, payload, signature = valid.split(".")

        raw = json.loads(base64.urlsafe_b64decode(payload + "==" * (-len(payload) % 4)))
        raw["sub"] = "1"  # try to become someone else
        forged_payload = _b64url(json.dumps(raw).encode())
        assert self._me(f"{header}.{forged_payload}.{signature}").status_code == 401

    def test_wrong_secret_token_is_rejected(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)
        user, _ = _seed_member_user(db, "sec_wrongkey", mt.id)

        token = pyjwt.encode({"sub": str(user.id)}, "not-the-real-secret", algorithm="HS256")
        assert self._me(token).status_code == 401

    def test_alg_none_token_is_rejected(self, db_session):
        """The classic 'alg=none' JWT bypass must not authenticate."""
        db = db_session
        mt = _seed_membership_type(db)
        user, _ = _seed_member_user(db, "sec_algnone", mt.id)

        header = _b64url(json.dumps({"alg": "none", "typ": "JWT"}).encode())
        payload = _b64url(json.dumps({"sub": str(user.id)}).encode())
        assert self._me(f"{header}.{payload}.").status_code == 401

    def test_token_without_subject_is_rejected(self, db_session):
        token = pyjwt.encode({"nonsense": True}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        assert self._me(token).status_code == 401

    def test_token_for_unknown_user_is_rejected(self, db_session):
        token = create_access_token({"sub": "999999"})
        assert self._me(token).status_code == 401

    def test_valid_token_for_inactive_user_is_rejected(self, db_session):
        db = db_session
        mt = _seed_membership_type(db)
        user, _ = _seed_member_user(db, "sec_inactive", mt.id)
        token = _login(_client(), "sec_inactive", "Member123!")

        # Deactivate the account; the still-valid JWT must stop working.
        user.is_active = False
        db.commit()

        assert self._me(token).status_code == 401

    def test_expired_token_cannot_reach_protected_routes(self, db_session):
        """The 401 must fire for business endpoints too, not just /auth/me."""
        db = db_session
        mt = _seed_membership_type(db)
        user, _ = _seed_member_user(db, "sec_probe", mt.id)

        token = create_access_token({"sub": str(user.id)}, expires_minutes=-5)
        resp = _client().get("/members/me/summary", headers=_auth_header(token))
        assert resp.status_code == 401
