from fastapi import APIRouter, Depends
from app.schemas.reservation import ReservationCreate, ReservationOut
from app.services.reservation_service import ReservationService
from app.api.deps import get_reservation_service, get_current_user
from app.models import User

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("", response_model=ReservationOut, status_code=201)
def reserve_book(
    data: ReservationCreate,
    service: ReservationService = Depends(get_reservation_service),
    current_user: User = Depends(get_current_user),
):
    return service.reserve_book(data)


@router.post("/{reservation_id}/cancel", response_model=ReservationOut)
def cancel_reservation(
    reservation_id: int,
    service: ReservationService = Depends(get_reservation_service),
    current_user: User = Depends(get_current_user),
):
    return service.cancel_reservation(reservation_id)
