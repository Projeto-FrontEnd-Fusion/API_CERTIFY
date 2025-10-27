from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum


FULLNAME_MAX = 100
FULLNAME_MIN = 6
PASSWORD_MAX = 100
PASSWORD_MIN = 8


class Role(str, Enum):
    ADMIN = ('admin',)
    USER = 'user'


class AuthUser(BaseModel):
    fullname: str = Field(
        ...,
        max_length=FULLNAME_MAX,
        min_length=FULLNAME_MIN,
        description='Nome completo do usuário',
    )
    email: EmailStr = Field(..., description='Email do usuário')
    password: str = Field(
        ...,
        max_digits=PASSWORD_MAX,
        min_length=PASSWORD_MIN,
        description='Senha do Usuário',
    )
    role: Role = Field(..., description='')
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AuthUserInDb(AuthUser):
    _id: str = Field(..., alias='_id')
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)
