class NotFoundError(Exception):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(message)
