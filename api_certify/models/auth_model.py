from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional
from enum import Enum


FULLNAME_MAX = 100
FULLNAME_MIN = 6
PASSWORD_MAX = 100
PASSWORD_MIN = 8

DESC_FULLNAME = 'Nome completo do usuário para identificação. Deve conter nome e sobrenome'
DESC_EMAIL = 'Endereço de email válido utilizado para login e comunicação'
DESC_PASSWORD = 'Senha de acesso segura. Deve conter letras, números e caracteres especiais'
DESC_ROLE = 'Nível de acesso do usuário no sistema. Define permissões e funcionalidades disponíveis'
DESC_STATUS = 'Status do usuário no sistema. Indica se possui certificado disponível ou outros estados'
DESC_CREATED_AT = 'Data e hora de criação do registro no sistema. Preenchido automaticamente'
DESC_UPDATED_AT = 'Data e hora da última atualização do registro. Atualizado automaticamente'
DESC_USER_ID = 'Identificador único do usuário no banco de dados (MongoDB ObjectId)'

EXAMPLE_FULLNAME = 'João Silva Santos'
EXAMPLE_EMAIL = 'usuario@empresa.com'
EXAMPLE_PASSWORD = 'SenhaSegura123!'
EXAMPLE_USER_ID = '507f1f77bcf86cd799439011'
EXAMPLE_DATETIME = '2024-01-15T10:30:00.000Z'
EXAMPLE_STATUS = 'available'


class Role(str, Enum):
    ADMIN = 'admin'
    USER = 'user'


class AuthUser(BaseModel):
    fullname: str = Field(
        ...,
        max_length=FULLNAME_MAX,
        min_length=FULLNAME_MIN,
        description=DESC_FULLNAME,
        example=EXAMPLE_FULLNAME
    )
    email: EmailStr = Field(
        ..., 
        description=DESC_EMAIL,
        example=EXAMPLE_EMAIL
    )
    password: str = Field(
        ...,
        max_length=PASSWORD_MAX,
        min_length=PASSWORD_MIN,
        description=DESC_PASSWORD,
        example=EXAMPLE_PASSWORD
    )
    role: Role = Field(
        ..., 
        description=DESC_ROLE,
        example=Role.USER
    )
    status: Optional[str] = Field(
        None,
        description=DESC_STATUS,
        example=EXAMPLE_STATUS
    )
    created_at: Optional[datetime] = Field(
        None,
        description=DESC_CREATED_AT
    )
    updated_at: Optional[datetime] = Field(
        None,
        description=DESC_UPDATED_AT
    )


class AuthUserLogin(BaseModel):
    email: EmailStr = Field(
        ..., 
        description=DESC_EMAIL,
        example=EXAMPLE_EMAIL
    )
    password: str = Field(
        ...,
        max_length=PASSWORD_MAX,
        min_length=PASSWORD_MIN,
        description=DESC_PASSWORD,
        example=EXAMPLE_PASSWORD
    )


class AuthUserInDb(AuthUser):
    id: str = Field(
        ..., 
        alias='_id',
        description=DESC_USER_ID,
        example=EXAMPLE_USER_ID
    )
    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)


class AuthUserReponse(BaseModel):
    id: str = Field(
        ..., 
        alias='_id',
        description=DESC_USER_ID,
        example=EXAMPLE_USER_ID
    )
    fullname: str = Field(
        ...,
        max_length=FULLNAME_MAX,
        min_length=FULLNAME_MIN,
        description=DESC_FULLNAME,
        example=EXAMPLE_FULLNAME
    )
    email: EmailStr = Field(
        ..., 
        description=DESC_EMAIL,
        example=EXAMPLE_EMAIL
    )
    role: Role = Field(
        ..., 
        description=DESC_ROLE,
        example=Role.USER
    )
    status: Optional[str] = Field(
        None,
        description=DESC_STATUS,
        example=EXAMPLE_STATUS
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