class ApiError(Exception):
    """An expected failure that maps to an HTTP error response.

    Lives outside `app.api` so services can raise it without depending on the web layer.
    """

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
