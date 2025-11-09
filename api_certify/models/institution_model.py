from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class InstitutionStatus(str, Enum):
    pending = 'pending'  
    available = 'available'  
    deactivated = 'deactivated'  
    activated = 'activated'  


DESC_INSTITUTION_NAME = 'Nome da instituição'
DESC_INSTITUTION_DESCRIPTION = 'Descrição geral da instituição'
DESC_INSTITUTION_RESPONSIBLE_NAME = 'Nome do responsável pela instituição'
DESC_INSTITUTION_RESPONSIBLE_POSITION = 'Cargo do responsável pela instituição'
DESC_INSTITUTION_CNPJ = 'CNPJ da instituição'
DESC_INSTITUTION_RESPONSIBLE_CPF = 'CPF do responsável'
DESC_INSTITUTION_CONTACT_EMAIL = 'E-mail de contato da instituição'
DESC_INSTITUTION_CONTACT_PHONE = 'Telefone de contato da instituição'
DESC_INSTITUTION_CREATED_AT = (
    'Data e hora em que a instituição foi cadastrada no sistema'
)
DESC_INSTITUTION_UPDATED_AT = (
    'Data e hora da última atualização do cadastro da instituição'
)
DESC_INSTITUTION_STATUS = 'Status atual da instituição (pendente, disponível, desativada ou reativada)'

EXAMPLE_DATETIME = '2025-11-09T15:30:00Z'

MAX_INSTITUTION_NAME = 50
MAX_INSTITUTION_DESCRIPTION = 255
MAX_INSTITUTION_RESPONSIBLE_POSITION = 50
MAX_INSTITUTION_CNPJ = 14
MAX_INSTITUTION_CPF = 14
MAX_INSTITUTION_PHONE = 14


class InstitutionBase(BaseModel):
    name: str = Field(
        ...,
        alias='institution_name',
        max_length=MAX_INSTITUTION_NAME,
        min_length=4,
        description=DESC_INSTITUTION_NAME,
    )
    institution_description: str = Field(
        ...,
        alias='description',
        max_length=MAX_INSTITUTION_DESCRIPTION,
        description=DESC_INSTITUTION_DESCRIPTION,
    )
    cnpj: Optional[str] = Field(
        None,
        alias='institution_cnpj',
        max_length=MAX_INSTITUTION_CNPJ,
        description=DESC_INSTITUTION_CNPJ,
    )
    contact_email: EmailStr = Field(
        ...,
        alias='institution_email',
        description=DESC_INSTITUTION_CONTACT_EMAIL,
    )
    contact_phone: str = Field(
        ...,
        alias='institution_phone',
        max_length=MAX_INSTITUTION_PHONE,
        description=DESC_INSTITUTION_CONTACT_PHONE,
    )
    responsible_name: str = Field(
        ...,
        alias='responsible_name',
        max_length=MAX_INSTITUTION_NAME,
        min_length=4,
        description=DESC_INSTITUTION_RESPONSIBLE_NAME,
    )
    responsible_position: str = Field(
        ...,
        alias='responsible_position',
        max_length=MAX_INSTITUTION_RESPONSIBLE_POSITION,
        min_length=4,
        description=DESC_INSTITUTION_RESPONSIBLE_POSITION,
    )
    responsible_cpf: Optional[str] = Field(
        None,
        alias='responsible_cpf',
        max_length=MAX_INSTITUTION_CPF,
        description=DESC_INSTITUTION_RESPONSIBLE_CPF,
    )
    status: InstitutionStatus = Field(
        default=InstitutionStatus.pending,
        description=DESC_INSTITUTION_STATUS,
        example=InstitutionStatus.pending,
    )

    class Config:
        populate_by_name = True


class CreateInstitution(InstitutionBase):
    pass


class InstitutionUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        alias='institution_name',
        max_length=MAX_INSTITUTION_NAME,
        min_length=4,
        description=DESC_INSTITUTION_NAME,
    )
    institution_description: Optional[str] = Field(
        None,
        alias='description',
        max_length=MAX_INSTITUTION_DESCRIPTION,
        description=DESC_INSTITUTION_DESCRIPTION,
    )
    cnpj: Optional[str] = Field(
        None,
        alias='institution_cnpj',
        max_length=MAX_INSTITUTION_CNPJ,
        description=DESC_INSTITUTION_CNPJ,
    )
    contact_email: Optional[EmailStr] = Field(
        None,
        alias='institution_email',
        description=DESC_INSTITUTION_CONTACT_EMAIL,
    )
    contact_phone: Optional[str] = Field(
        None,
        alias='institution_phone',
        max_length=MAX_INSTITUTION_PHONE,
        description=DESC_INSTITUTION_CONTACT_PHONE,
    )
    responsible_name: Optional[str] = Field(
        None,
        alias='responsible_name',
        max_length=MAX_INSTITUTION_NAME,
        min_length=4,
        description=DESC_INSTITUTION_RESPONSIBLE_NAME,
    )
    responsible_position: Optional[str] = Field(
        None,
        alias='responsible_position',
        max_length=MAX_INSTITUTION_RESPONSIBLE_POSITION,
        min_length=4,
        description=DESC_INSTITUTION_RESPONSIBLE_POSITION,
    )
    responsible_cpf: Optional[str] = Field(
        None,
        alias='responsible_cpf',
        max_length=MAX_INSTITUTION_CPF,
        description=DESC_INSTITUTION_RESPONSIBLE_CPF,
    )
    status: Optional[InstitutionStatus] = Field(
        None,
        description=DESC_INSTITUTION_STATUS,
        example=InstitutionStatus.available,
    )
    created_at: Optional[datetime] = Field(
        None,
        alias='created_at',
        description=DESC_INSTITUTION_CREATED_AT,
        example=EXAMPLE_DATETIME,
    )
    updated_at: Optional[datetime] = Field(
        None,
        alias='updated_at',
        description=DESC_INSTITUTION_UPDATED_AT,
        example=EXAMPLE_DATETIME,
    )

    class Config:
        populate_by_name = True


class InstitutionInDb(InstitutionBase):
    id: str = Field(
        ...,
        alias='_id',
        description='Identificador único da instituição no banco de dados',
        example='6759d41f12b3a9014c8af23c',
    )
    created_at: Optional[datetime] = Field(
        None,
        alias='created_at',
        description=DESC_INSTITUTION_CREATED_AT,
        example=EXAMPLE_DATETIME,
    )
    updated_at: Optional[datetime] = Field(
        None,
        alias='updated_at',
        description=DESC_INSTITUTION_UPDATED_AT,
        example=EXAMPLE_DATETIME,
    )

    class Config:
        populate_by_name = True
