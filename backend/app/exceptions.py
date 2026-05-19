"""Domain exceptions for the application.

Services raise these exceptions to signal business-rule violations.
The API layer (or a global exception handler) translates them to HTTP responses.
"""


class AppException(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail or message
        super().__init__(self.message)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist (maps to 404)."""

    def __init__(self, resource: str, identifier: int | str | None = None) -> None:
        msg = f"{resource} not found" if identifier is None else f"{resource} {identifier} not found"
        super().__init__(msg)


class AlreadyExistsException(AppException):
    """Raised when creating a resource that already exists (maps to 409)."""

    def __init__(self, resource: str, field: str, value: str) -> None:
        super().__init__(f"{resource} with {field} '{value}' already exists")


class InvalidCredentialsException(AppException):
    """Raised when login credentials are invalid (maps to 401)."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class UnauthorizedException(AppException):
    """Raised when authentication is required but missing/invalid (maps to 401)."""

    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message)


class ForbiddenException(AppException):
    """Raised when the user lacks permission for an action (maps to 403)."""

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message)


class BadRequestException(AppException):
    """Raised for invalid input that does not fit other categories (maps to 400)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
