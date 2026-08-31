from fastapi import APIRouter, Depends
from app.schemas.borrow import BorrowCreate, BorrowOut
from app.services.borrowing_service import BorrowingService
from app.api.deps import get_borrowing_service, require_roles, get_current_user
from app.models import UserRole, User

router = APIRouter(tags=["Borrowing"])
staff_only = require_roles(UserRole.ADMIN, UserRole.LIBRARIAN)


@router.post("/borrow", response_model=BorrowOut, status_code=201)
def borrow_book(
    data: BorrowCreate,
    service: BorrowingService = Depends(get_borrowing_service),
    current_user: User = Depends(get_current_user),
):
    return service.borrow_book(data)


@router.post("/return/{borrow_id}", response_model=BorrowOut, dependencies=[Depends(staff_only)])
def return_book(borrow_id: int, service: BorrowingService = Depends(get_borrowing_service)):
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
