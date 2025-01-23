from app.exceptions.fhir_exception import FHIRException


class ResourceNotFoundException(FHIRException):
    def __init__(self, detail: str = "Requested resource was not found") -> None:
        super().__init__(status_code=404, severity="error", code="resource-not-found", msg=detail)


class ResourceNotAddedException(FHIRException):
    def __init__(self, detail: str = "Creating new resource failed") -> None:
        super().__init__(status_code=409, severity="error", code="conflict-occurred", msg=detail)


class ResourceNotDeletedException(FHIRException):
    def __init__(self, detail: str = "Deleting resource failed") -> None:
        super().__init__(status_code=409, severity="error", code="conflict-occurred", msg=detail)


class InvalidResourceException(FHIRException):
    def __init__(self, detail: str = "Invalid resource") -> None:
        super().__init__(status_code=422, severity="error", code="bad-request", msg=detail)
