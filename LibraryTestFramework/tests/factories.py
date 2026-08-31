"""Factory Boy + Faker test-data factories.

Factories return plain dictionaries that match the payload shape used by
the application. They are intentionally independent of the database so
tests can generate realistic data without coupling unit tests to ORM state.
"""
import factory


class MemberFactory(factory.Factory):
    """Generate realistic Member-like payloads."""

    class Meta:
        model = dict

    full_name = factory.Faker("name")
    email = factory.Faker("email")
    is_active = True
    outstanding_fine = 0.0
    membership_type_id = 1


class BookFactory(factory.Factory):
    """Generate realistic BookCreate-like payloads."""

    class Meta:
        model = dict

    title = factory.Faker("sentence", nb_words=4)
    isbn = factory.Faker("isbn13", separator="")
    price = factory.Faker("pyfloat", min_value=5, max_value=100, right_digits=2)
    publication_year = factory.Faker("random_int", min=1950, max=2026)
    description = factory.Faker("paragraph", nb_sentences=2)
    author_ids = factory.LazyFunction(lambda: [1])
    number_of_copies = 2


class BorrowRecordFactory(factory.Factory):
    """Generate realistic BorrowRecord-like identifiers."""

    class Meta:
        model = dict

    copy_id = factory.Sequence(lambda n: n + 1)
    member_id = factory.Sequence(lambda n: n + 1)
    book_id = factory.Sequence(lambda n: n + 1)
