from fastapi import APIRouter, Depends
from app.schemas.book import BookCreate, BookOut
from app.services.book_service import BookService
from app.api.deps import get_book_service, require_roles
from app.models import UserRole

router = APIRouter(prefix="/books", tags=["Books"])
staff_only = require_roles(UserRole.ADMIN, UserRole.LIBRARIAN)


@router.post("", response_model=BookOut, status_code=201, dependencies=[Depends(staff_only)])
def create_book(data: BookCreate, service: BookService = Depends(get_book_service)):
    return service.create_book(data)


@router.get("", response_model=list[BookOut])
def list_books(search: str | None = None, service: BookService = Depends(get_book_service)):
    return service.list_books(search)


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, service: BookService = Depends(get_book_service)):
    return service.get_book(book_id)


@router.post("/{book_id}/copies", response_model=BookOut, dependencies=[Depends(staff_only)])
def add_copies(book_id: int, count: int, service: BookService = Depends(get_book_service)):
    return service.add_copies(book_id, count)


@router.delete("/{book_id}/copies/{copy_id}", response_model=BookOut, dependencies=[Depends(staff_only)])
def remove_copy(book_id: int, copy_id: int, service: BookService = Depends(get_book_service)):
    return service.remove_copy(book_id, copy_id)
