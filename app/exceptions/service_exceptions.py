from app.exceptions.fhir_exception import FHIRException


class InvalidResourceException(FHIRException):
    def __init__(self, detail: str = "Invalid resource") -> None:
        super().__init__(status_code=422, severity="error", code="bad-request", msg=detail)
