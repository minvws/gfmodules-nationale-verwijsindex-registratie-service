from fastapi import HTTPException
from pydantic import BaseModel


class OperationOutcomeDetail(BaseModel):
    text: str


class OperationOutcomeIssue(BaseModel):
    severity: str
    code: str
    details: OperationOutcomeDetail


class OperationOutcome(BaseModel):
    resourceType: str = "OperationOutcome"
    issue: list[OperationOutcomeIssue]


class FHIRException(HTTPException):
    def __init__(self, status_code: int, severity: str, code: str, msg: str):
        outcome = OperationOutcome(
            issue=[
                OperationOutcomeIssue(
                    severity=severity,
                    code=code,
                    details=OperationOutcomeDetail(text=msg),
                )
            ]
        )
        super().__init__(status_code=status_code, detail=outcome.model_dump())
