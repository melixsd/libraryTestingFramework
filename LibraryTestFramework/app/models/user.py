"""User model - for authentication and access control (RBAC)"""
import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"        # Full access: catalog management, members, reports
    LIBRARIAN = "librarian"  # Manage borrowing/returns/reservations
    MEMBER = "member"      # Only operations related to themselves (borrowing, viewing books)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    is_active = Column(Boolean, default=True)

    # If the user's role is MEMBER, linked to a Member record
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    member = relationship("Member")
