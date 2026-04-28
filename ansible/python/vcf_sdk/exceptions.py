"""Custom exceptions for VCF SDK."""


class VCFException(Exception):
    """Base exception for all VCF SDK errors."""

    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)

    def __str__(self):
        parts = [self.message]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        if self.response_body:
            parts.append(f"\nResponse: {self.response_body}")
        return " ".join(parts)


class AuthenticationError(VCFException):
    """Raised when authentication to SDDC Manager fails."""

    pass


class ValidationError(VCFException):
    """Raised when API request validation fails."""

    pass


class TaskFailedError(VCFException):
    """Raised when a task reaches FAILED or CANCELLED state."""

    def __init__(
        self,
        task_id: str,
        status: str,
        message: str = None,
        errors: list = None,
    ):
        self.task_id = task_id
        self.status = status
        self.errors = errors or []
        msg = f"Task {task_id} {status}"
        if message:
            msg += f": {message}"
        super().__init__(msg)


class TimeoutError(VCFException):
    """Raised when operation exceeds timeout."""

    pass


class NotFoundError(VCFException):
    """Raised when a resource is not found."""

    pass
