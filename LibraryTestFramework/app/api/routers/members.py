from fastapi import APIRouter, Depends, HTTPException
from app.schemas.member import MemberCreate, MemberOut, MemberSummaryOut, MembershipChange
from app.services.member_service import MemberService
from app.services.auth_service import AuthService
from app.api.deps import (
    get_member_service, get_auth_service, require_roles, get_current_user,
)
from app.core.exceptions import NotFoundError
from app.models import UserRole, User

router = APIRouter(prefix="/members", tags=["Members"])
staff_only = require_roles(UserRole.ADMIN, UserRole.LIBRARIAN)


@router.post("", response_model=MemberOut, status_code=201, dependencies=[Depends(staff_only)])
def create_member(data: MemberCreate, service: MemberService = Depends(get_member_service)):
    return service.create_member(data)


@router.post("/{member_id}/approve", response_model=MemberOut, dependencies=[Depends(staff_only)])
def approve_member(member_id: int, service: AuthService = Depends(get_auth_service)):
    """Approve a pending self-registered member so they can sign in and borrow."""
    return service.approve_member(member_id)


@router.post("/{member_id}/reject", status_code=204, dependencies=[Depends(staff_only)])
def reject_member(member_id: int, service: AuthService = Depends(get_auth_service)):
    """Reject a pending self-registered signup, removing the member and login."""
    service.reject_member(member_id)


@router.get("", response_model=list[MemberOut], dependencies=[Depends(staff_only)])
def list_members(service: MemberService = Depends(get_member_service)):
    return service.list_members()


@router.get("/{member_id}", response_model=MemberOut)
def get_member(member_id: int, service: MemberService = Depends(get_member_service)):
    return service.get_member(member_id)


@router.get("/me/summary", response_model=MemberSummaryOut)
def get_my_summary(
    current_user: User = Depends(get_current_user),
    service: MemberService = Depends(get_member_service),
):
    if not current_user.member_id:
        raise NotFoundError("User is not a library member")
    return service.get_member_summary(current_user.member_id)


@router.post("/{member_id}/pay-fine", response_model=MemberOut, dependencies=[Depends(staff_only)])
def pay_fine(member_id: int, amount: float, service: MemberService = Depends(get_member_service)):
    return service.pay_fine(member_id, amount)


@router.patch("/{member_id}/membership", response_model=MemberOut)
def change_membership(
    member_id: int,
    data: MembershipChange,
    service: MemberService = Depends(get_member_service),
    current_user: User = Depends(get_current_user),
):
    # Staff may change any member's plan; members may change only their own.
    if current_user.role not in (UserRole.ADMIN, UserRole.LIBRARIAN):
        if current_user.member_id is None or current_user.member_id != member_id:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this operation",
            )
    return service.change_membership(member_id, data.membership_type_id)
