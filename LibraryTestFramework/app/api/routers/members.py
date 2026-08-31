from fastapi import APIRouter, Depends
from app.schemas.member import MemberCreate, MemberOut, MemberSummaryOut
from app.services.member_service import MemberService
from app.api.deps import get_member_service, require_roles, get_current_user
from app.core.exceptions import NotFoundError
from app.models import UserRole, User

router = APIRouter(prefix="/members", tags=["Members"])
staff_only = require_roles(UserRole.ADMIN, UserRole.LIBRARIAN)


@router.post("", response_model=MemberOut, status_code=201, dependencies=[Depends(staff_only)])
def create_member(data: MemberCreate, service: MemberService = Depends(get_member_service)):
    return service.create_member(data)


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
