from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum
from bson import ObjectId


DESC_INSTITUTION_NAME = (
    'Nome oficial da instituição responsável pelos eventos e certificados.'
)
DESC_EMAIL = 'Endereço de email institucional utilizado para login e comunicações oficiais.'
DESC_PASSWORD = 'Senha de acesso segura. Deve conter letras, números e caracteres especiais.'
DESC_ROLE = 'Nível de acesso no sistema: instituição ou administrador.'
DESC_STATUS = 'Status da instituição no sistema. Indica se está ativa, pendente ou inativa.'
DESC_CREATED_AT = 'Data e hora de criação do registro no sistema. Preenchido automaticamente.'
DESC_UPDATED_AT = 'Data e hora da última atualização do registro. Atualizado automaticamente.'
DESC_INSTITUTION_ID = (
    'Identificador único da instituição no banco de dados (MongoDB ObjectId).'
)

EXAMPLE_INSTITUTION_NAME = 'Instituto Tech Avançar'
EXAMPLE_EMAIL = 'contato@institutoavancar.org'
EXAMPLE_PASSWORD = 'SenhaSegura123!'
EXAMPLE_INSTITUTION_ID = '507f1f77bcf86cd799439011'
EXAMPLE_DATETIME = '2024-01-15T10:30:00.000Z'
EXAMPLE_STATUS = 'ativo'

INSTITUTION_NAME_MAX = 100
INSTITUTION_NAME_MIN = 3
PASSWORD_MAX = 100
PASSWORD_MIN = 8


class Role(str, Enum):
    ADMIN = 'admin'
    INSTITUTION = 'institution'


class Status(str, Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'


class InstitutionAuth(BaseModel):
    institution_name: str = Field(
        ...,
        max_length=INSTITUTION_NAME_MAX,
        min_length=INSTITUTION_NAME_MIN,
        description=DESC_INSTITUTION_NAME,
        example=EXAMPLE_INSTITUTION_NAME,
    )
    email: EmailStr = Field(..., description=DESC_EMAIL, example=EXAMPLE_EMAIL)
    password: str = Field(
        ...,
        max_length=PASSWORD_MAX,
        min_length=PASSWORD_MIN,
        description=DESC_PASSWORD,
        example=EXAMPLE_PASSWORD,
    )
    role: Role = Field(..., description=DESC_ROLE, example=Role.INSTITUTION)
    status: Optional[str] = Field(
        None, description=DESC_STATUS, example=EXAMPLE_STATUS
    )
    created_at: Optional[datetime] = Field(
        None,
        description=DESC_CREATED_AT,
        example=EXAMPLE_DATETIME
    )
    updated_at: Optional[datetime] = Field(
        None,
        description=DESC_UPDATED_AT,
        example=EXAMPLE_DATETIME
    )


class InstitutionAuthLogin(BaseModel):
    email: EmailStr = Field(..., description=DESC_EMAIL, example=EXAMPLE_EMAIL)
    password: str = Field(
        ...,
        max_length=PASSWORD_MAX,
        min_length=PASSWORD_MIN,
        description=DESC_PASSWORD,
        example=EXAMPLE_PASSWORD,
    )


class InstitutionAuthInDb(InstitutionAuth):
    id: str = Field(
        ...,
        alias='_id',
        description=DESC_INSTITUTION_ID,
        example=EXAMPLE_INSTITUTION_ID,
    )
    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)


class InstitutionAuthResponse(BaseModel):
    id: str = Field(
        ...,
        alias='_id',
        description=DESC_INSTITUTION_ID,
        example=EXAMPLE_INSTITUTION_ID,
    )
    institution_name: str = Field(
        ...,
        max_length=INSTITUTION_NAME_MAX,
        min_length=INSTITUTION_NAME_MIN,
        description=DESC_INSTITUTION_NAME,
        example=EXAMPLE_INSTITUTION_NAME,
    )
    email: EmailStr = Field(..., description=DESC_EMAIL, example=EXAMPLE_EMAIL)
    role: Role = Field(..., description=DESC_ROLE, example=Role.INSTITUTION)
    status: Optional[str] = Field(
        None, description=DESC_STATUS, example=EXAMPLE_STATUS
    )
    created_at: Optional[datetime] = Field(
        None, description=DESC_CREATED_AT, example=EXAMPLE_DATETIME
    )
    updated_at: Optional[datetime] = Field(
        None, description=DESC_UPDATED_AT, example=EXAMPLE_DATETIME
    )
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str} 
    )
    