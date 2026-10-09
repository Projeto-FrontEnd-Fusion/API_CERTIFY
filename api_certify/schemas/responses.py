from pydantic import BaseModel, Field
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
    access_key: str = ''
    institution_name: str = ''
    description: str = ''
    valid_until: Optional[datetime] = None
    design: dict = Field(default_factory=dict)
    participant_name: str
    event_name: str
    workload: str
    issued_at: Optional[datetime] = None
    event_start: Optional[datetime] = None
    event_end: Optional[datetime] = None
