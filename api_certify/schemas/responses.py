from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class BaseResponse(BaseModel):
    success: bool
    message: str
    details: Optional[str] = None


class SucessResponse(BaseResponse):
    data: Optional[Any] = None


class ErrorResponse(BaseResponse):
    error_code: Optional[str] = None


class CertificateValidationResponse(BaseModel):
    participant_name: str
    event_name: str
    workload: str
    issued_at: Optional[datetime] = None
    event_start: Optional[datetime] = None
    event_end: Optional[datetime] = None
