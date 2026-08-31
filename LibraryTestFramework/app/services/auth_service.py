"""
Authentication logic: registration, login, token creation.
No reference to FastAPI -> can be tested with plain pytest, without a server.
"""
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import DuplicateError, AuthenticationError, NotFoundError
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
        # If membership info is provided, also create a Member record
        if data.full_name and data.membership_type_id:
            if not self.membership_repo.get(data.membership_type_id):
                raise NotFoundError("Membership type not found")
            member = Member(
                full_name=data.full_name,
                email=data.email,
                membership_type_id=data.membership_type_id,
            )
            member = self.member_repo.add(member)
            member_id = member.id

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=UserRole.MEMBER,
            member_id=member_id,
        )
        return self.user_repo.add(user)

    def authenticate(self, username: str, password: str) -> User:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect username or password")
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        return user

    def login(self, username: str, password: str) -> str:
        user = self.authenticate(username, password)
        return create_access_token({"sub": str(user.id), "role": user.role.value})
