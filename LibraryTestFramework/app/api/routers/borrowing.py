from fastapi import APIRouter, Depends, HTTPException
from app.schemas.borrow import BorrowCreate, BorrowOut
from app.services.borrowing_service import BorrowingService
from app.api.deps import get_borrowing_service, require_roles, get_current_user
from app.models import UserRole, User

router = APIRouter(tags=["Borrowing"])
staff_only = require_roles(UserRole.ADMIN, UserRole.LIBRARIAN)


def _can_return(current_user: User, record) -> bool:
    if current_user.role in (UserRole.ADMIN, UserRole.LIBRARIAN):
        return True
    return current_user.member_id is not None and record.member_id == current_user.member_id


@router.post("/borrow", response_model=BorrowOut, status_code=201)
def borrow_book(
    data: BorrowCreate,
    service: BorrowingService = Depends(get_borrowing_service),
    current_user: User = Depends(get_current_user),
):
    return service.borrow_book(data)


@router.post("/return/{borrow_id}", response_model=BorrowOut)
def return_book(
    borrow_id: int,
    service: BorrowingService = Depends(get_borrowing_service),
    current_user: User = Depends(get_current_user),
):
    # Staff may process any return; members may return only their own loans.
    record = service.get_borrow(borrow_id)
    if not _can_return(current_user, record):
        raise HTTPException(status_code=403, detail="You do not have permission to perform this operation")
    return service.return_book(borrow_id)


@router.post("/renew/{borrow_id}", response_model=BorrowOut)
def renew_book(
    borrow_id: int,
    service: BorrowingService = Depends(get_borrowing_service),
    current_user: User = Depends(get_current_user),
):
    return service.renew_book(borrow_id)


@router.post("/copies/{copy_id}/lost", dependencies=[Depends(staff_only)])
def mark_copy_lost(copy_id: int, service: BorrowingService = Depends(get_borrowing_service)):
    copy = service.mark_copy_lost(copy_id)
    return {"id": copy.id, "status": copy.status}
