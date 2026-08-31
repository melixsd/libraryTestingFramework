"""
Domain Exceptions.
Important: these classes have no dependency on FastAPI.
The Service layer raises them and the API layer (main.py) translates them
to the appropriate HTTP status codes. This means Services are testable without a web server.
"""


class DomainError(Exception):
    """Base class for all business logic errors"""


class NotFoundError(DomainError):
    """Requested entity not found -> 404"""


class DuplicateError(DomainError):
    """Attempt to create a duplicate record -> 400"""


class BusinessRuleError(DomainError):
    """Violation of a business rule (e.g. borrowing limit, fine) -> 400/409"""


class AuthenticationError(DomainError):
    """Authentication failed -> 401"""


class PermissionDeniedError(DomainError):
    """User does not have permission to perform this operation -> 403"""
