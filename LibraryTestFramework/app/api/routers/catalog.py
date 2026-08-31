from fastapi import APIRouter, Depends
from app.schemas.author import AuthorCreate, AuthorOut
from app.schemas.catalog import (
    PublisherCreate, PublisherOut, CategoryCreate, CategoryOut,
    MembershipTypeCreate, MembershipTypeOut,
)
from app.services.catalog_service import CatalogService
from app.api.deps import get_catalog_service, require_roles
from app.models import UserRole

router = APIRouter(tags=["Catalog"])
staff_only = require_roles(UserRole.ADMIN, UserRole.LIBRARIAN)


@router.post("/authors", response_model=AuthorOut, status_code=201, dependencies=[Depends(staff_only)])
def create_author(data: AuthorCreate, service: CatalogService = Depends(get_catalog_service)):
    return service.create_author(data)


@router.get("/authors", response_model=list[AuthorOut])
def list_authors(service: CatalogService = Depends(get_catalog_service)):
    return service.list_authors()


@router.delete("/authors/{author_id}", status_code=204, dependencies=[Depends(staff_only)])
def delete_author(author_id: int, service: CatalogService = Depends(get_catalog_service)):
    service.delete_author(author_id)


@router.post("/publishers", response_model=PublisherOut, status_code=201, dependencies=[Depends(staff_only)])
def create_publisher(data: PublisherCreate, service: CatalogService = Depends(get_catalog_service)):
    return service.create_publisher(data)


@router.post("/categories", response_model=CategoryOut, status_code=201, dependencies=[Depends(staff_only)])
def create_category(data: CategoryCreate, service: CatalogService = Depends(get_catalog_service)):
    return service.create_category(data)


@router.post("/membership-types", response_model=MembershipTypeOut, status_code=201, dependencies=[Depends(staff_only)])
def create_membership_type(data: MembershipTypeCreate, service: CatalogService = Depends(get_catalog_service)):
    return service.create_membership_type(data)
