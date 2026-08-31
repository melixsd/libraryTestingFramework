"""
This is where all layers connect together.
Each route gets an instance of its required service via Depends(get_xxx_service),
without knowing how that service is constructed (Dependency Injection).

Connection chain:
  Router  --Depends-->  Service  --uses-->  Repository  --uses-->  DB Session
"""
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.core.security import decode_access_token
from app.models import User, UserRole
from app.repositories.user_repository import UserRepository
from app.repositories.member_repository import MemberRepository
from app.repositories.book_repository import BookRepository
from app.repositories.borrow_repository import BorrowRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.catalog_repository import (
    AuthorRepository, PublisherRepository, CategoryRepository, MembershipTypeRepository
)
from app.services.auth_service import AuthService
from app.services.catalog_service import CatalogService
from app.services.book_service import BookService
from app.services.member_service import MemberService
from app.services.borrowing_service import BorrowingService
from app.services.reservation_service import ReservationService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------- Service Providers ----------
def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db), MemberRepository(db), MembershipTypeRepository(db))


def get_catalog_service(db: Session = Depends(get_db)) -> CatalogService:
    return CatalogService(
        AuthorRepository(db), PublisherRepository(db),
        CategoryRepository(db), MembershipTypeRepository(db),
    )


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    return BookService(BookRepository(db), AuthorRepository(db))


def get_member_service(db: Session = Depends(get_db)) -> MemberService:
    return MemberService(MemberRepository(db), MembershipTypeRepository(db))


def get_borrowing_service(db: Session = Depends(get_db)) -> BorrowingService:
    return BorrowingService(
        BookRepository(db), MemberRepository(db),
        BorrowRepository(db), ReservationRepository(db),
    )


def get_reservation_service(db: Session = Depends(get_db)) -> ReservationService:
    return ReservationService(BookRepository(db), MemberRepository(db), ReservationRepository(db))


# ---------- Authentication / RBAC ----------
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token is invalid")

    user = UserRepository(db).get(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_roles(*roles: UserRole):
    """
    Dependency factory for role-based access control.
    Usage example: Depends(require_roles(UserRole.ADMIN, UserRole.LIBRARIAN))
    """
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have permission to perform this operation")
        return current_user
    return checker
