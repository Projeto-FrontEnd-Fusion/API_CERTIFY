from pydantic import BaseModel
from typing import Optional, Any


class BaseResponse(BaseModel):
    success: bool
    message: str
    details: Optional[str] = None


class SucessResponse(BaseResponse):
    data: Optional[Any] = None


class ErrorResponse(BaseResponse):
    error_code: Optional[str] = None
