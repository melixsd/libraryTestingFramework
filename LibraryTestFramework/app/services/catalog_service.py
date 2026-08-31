"""Simple CRUD logic for Author, Publisher, Category, MembershipType."""
from app.core.exceptions import NotFoundError, BusinessRuleError
from app.models import Author, Publisher, Category, MembershipType
from app.repositories.catalog_repository import (
    AuthorRepository, PublisherRepository, CategoryRepository, MembershipTypeRepository
)
from app.schemas.author import AuthorCreate
from app.schemas.catalog import PublisherCreate, CategoryCreate, MembershipTypeCreate


class CatalogService:
    def __init__(
        self,
        author_repo: AuthorRepository,
        publisher_repo: PublisherRepository,
        category_repo: CategoryRepository,
        membership_repo: MembershipTypeRepository,
    ):
        self.author_repo = author_repo
        self.publisher_repo = publisher_repo
        self.category_repo = category_repo
        self.membership_repo = membership_repo

    def create_author(self, data: AuthorCreate) -> Author:
        return self.author_repo.add(Author(**data.model_dump()))

    def list_authors(self) -> list[Author]:
        return self.author_repo.get_all()

    def delete_author(self, author_id: int) -> None:
        author = self.author_repo.get(author_id)
        if not author:
            raise NotFoundError("Author not found")
        if author.books:
            raise BusinessRuleError("Cannot delete an author that has books in the catalogue. Remove their books first.")
        self.author_repo.delete(author)

    def create_publisher(self, data: PublisherCreate) -> Publisher:
        return self.publisher_repo.add(Publisher(**data.model_dump()))

    def create_category(self, data: CategoryCreate) -> Category:
        return self.category_repo.add(Category(**data.model_dump()))

    def create_membership_type(self, data: MembershipTypeCreate) -> MembershipType:
        return self.membership_repo.add(MembershipType(**data.model_dump()))

    def list_membership_types(self) -> list[MembershipType]:
        return self.membership_repo.get_all()

    def get_membership_type(self, id: int) -> MembershipType:
        mt = self.membership_repo.get(id)
        if not mt:
            raise NotFoundError("Membership type not found")
        return mt
