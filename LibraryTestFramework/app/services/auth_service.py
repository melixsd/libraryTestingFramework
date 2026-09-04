"""
Authentication logic: registration, login, token creation, membership approval.
No reference to FastAPI -> can be tested with plain pytest, without a server.
"""
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import (
    DuplicateError, AuthenticationError, NotFoundError, BusinessRuleError,
)
from app.models import User, UserRole, Member
from app.repositories.user_repository import UserRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.catalog_repository import MembershipTypeRepository
from app.schemas.auth import UserRegister


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        member_repo: MemberRepository,
        membership_repo: MembershipTypeRepository,
    ):
        self.user_repo = user_repo
        self.member_repo = member_repo
        self.membership_repo = membership_repo

    def register(self, data: UserRegister) -> User:
        if self.user_repo.get_by_username(data.username):
            raise DuplicateError("This username is already registered")
        if self.user_repo.get_by_email(data.email):
            raise DuplicateError("This email is already registered")

        member_id = None
        pending = False
        # If membership info is provided, also create a Member record. The
        # registration starts as PENDING: the member and user stay inactive
        # until an administrator approves the signup (see approve_member).
        if data.full_name and data.membership_type_id:
            if not self.membership_repo.get(data.membership_type_id):
                raise NotFoundError("Membership type not found")
            member = Member(
                full_name=data.full_name,
                email=data.email,
                membership_type_id=data.membership_type_id,
                is_active=False,
            )
            member = self.member_repo.add(member)
            member_id = member.id
            pending = True

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=UserRole.MEMBER,
            member_id=member_id,
            is_active=not pending,
        )
        return self.user_repo.add(user)

    def approve_member(self, member_id: int) -> Member:
        """Approve a pending self-registered member, activating their login."""
        member = self.member_repo.get(member_id)
        if not member:
            raise NotFoundError("Member not found")
        if member.is_active:
            raise BusinessRuleError("Member is already approved")

        member.is_active = True
        user = self.user_repo.get_by_member_id(member_id)
        if user:
            user.is_active = True
        self.member_repo.db.commit()
        self.member_repo.db.refresh(member)
        return member

    def reject_member(self, member_id: int) -> None:
        """Reject a pending self-registered signup, removing member and login."""
        member = self.member_repo.get(member_id)
        if not member:
            raise NotFoundError("Member not found")
        if member.is_active:
            raise BusinessRuleError("Only pending registrations can be rejected")
        if (
            self.member_repo.active_borrow_count(member_id) > 0
            or self.member_repo.get_reservations_by_member(member_id)
        ):
            raise BusinessRuleError(
                "Cannot reject a member with borrow records or reservations"
            )

        user = self.user_repo.get_by_member_id(member_id)
        if user:
            self.user_repo.delete(user)
        self.member_repo.delete(member)

    def authenticate(self, username: str, password: str) -> User:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect username or password")
        if not user.is_active:
            # An inactive member-linked account is an unapproved signup; an
            # inactive account without a member record is simply disabled.
            if user.member_id is not None:
                raise AuthenticationError(
                    "Your account is pending administrator approval"
                )
            raise AuthenticationError("User account is inactive")
        return user

    def login(self, username: str, password: str) -> str:
        user = self.authenticate(username, password)
        return create_access_token({"sub": str(user.id), "role": user.role.value})
