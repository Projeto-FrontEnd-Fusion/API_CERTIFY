# 4. Entidade: Certificado (Certificate)
# Descrição: Registro individual de um certificado emitido para um participante em um evento.
# Propriedade | Tipo | Chave/Observação
# id | string (UUID) /OBJECTID | PK (Chave Primária).
# eventId | string | FK para Event.
# participantId | string | FK para User (role: participant).
# participantName | string | Nome do participante (para rastreabilidade/relatórios).
# workload | string | Carga horária
# eventName | string | Nome do evento.
# description | string | Observações adicionais.
# issuedAt | Date | Opcional. Data de emissão.
# availableAt | Date | Data de disponibilidade.
# validUntil | Date | Data limite de validade.
# acesskey | string | Token de altenticação
# status | enum | Status ('pending' | 'available' | 'expired').
# startDate | Date | Data de inicio do evento
# endDate | Date | Data final do Evento

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

PARTICIPANT_MAX = 100
PARTICIPANT_MIN = 6

DESC_REQ_CERTIFICATE_FULLNAME = (
    'Nome completo do usuário para identificação. Deve conter nome e sobrenome'
)
DESC_REQ_CERTIFICATE_EMAIL = (
    'Endereço de email válido utilizado para login e comunicação'
)
DESC_REQ_CERTIFICATE_ACCESS_KEY = 'Token de autenticação do certificado'

EXAMPLE_REQ_CERTIFICATE_FULLNAME = 'João Silva Santos'
EXAMPLE_REQ_CERTIFICATE_EMAIL = 'usuario@empresa.com'
EXAMPLE_REQ_CERTIFICATE_ACCESS_KEY = 'ABC123'

DESC_CERTIFICATE_ID = (
    'Identificador único do certificado no banco de dados (MongoDB ObjectId)'
)
DESC_CERTIFICATE_USER_ID = (
    'Identificador único do usuário que está emitindo o certificado'
)
DESC_CERTIFICATE_ACCESS_KEY = 'Token de autenticação do certificado'
DESC_CERTIFICATE_STATUS = (
    'Status do certificado ("pending" | "available" | "expired")'
)
DESC_CERTIFICATE_PARTICIPANT_NAME = 'Nome completo do participante para identificação. Normalmente essas informações são herdades diretamente do nome do usuário.'
DESC_CERTIFICATE_PARTICIPANT_EMAIL = (
    'Email do participante que emitiu o certificado'
)
DESC_CERTIFICATE_INSTITUTION_NAME = 'Nome da instituição que ministrou o curso'
DESC_CERTIFICATE_EVENT_ID = (
    'Identificador único do evento no banco de dados (MongoDB ObjectId)'
)
DESC_CERTIFICATE_EVENT_NAME = 'Nome do curso, evento ou palestra'
DESC_CERTIFICATE_DESCRIPTION = 'Descrição do certificado'
DESC_CERTIFICATE_WORKLOAD = 'Carga horária do certificado'
DESC_CERTIFICATE_EVENT_START = 'Data de início do evento'
DESC_CERTIFICATE_EVENT_END = 'Data de termino do evento'
DESC_CERTIFICATE_EVENT_DATE = 'Data do evento'
DESC_CERTIFICATE_ISSUED_AT = 'Horario de emissão do certificado'
DESC_CERTIFICATE_VALID_UNTIL = 'Data de expiração do certificado'

EXAMPLE_CERTIFICATE_ID = '507f1f77bcf86cd799439011'
EXAMPLE_CERTIFICATE_USER_ID = 'usr_123456789'
EXAMPLE_CERTIFICATE_ACCESS_KEY = 'ABC123'
EXAMPLE_CERTIFICATE_STATUS = 'available'
EXAMPLE_CERTIFICATE_PARTICIPANT_NAME = 'Gustavo Guanabara Fiuza da Silva'
EXAMPLE_CERTIFICATE_PARTICIPANT_EMAIL = 'joao.silva@email.com'
EXAMPLE_CERTIFICATE_INSTITUTION_NAME = 'Comunidade Frontend Fusion'
EXAMPLE_CERTIFICATE_EVENT_ID = 'evt_987654321'
EXAMPLE_CERTIFICATE_EVENT_NAME = 'Curso Avançado de JavaScript Moderno'
EXAMPLE_CERTIFICATE_DESCRIPTION = 'Certificado emitido para participante que concluiu com êxito todas as atividades avaliativas.'
EXAMPLE_CERTIFICATE_WORKLOAD = '40 horas'
EXAMPLE_CERTIFICATE_EVENT_START = '2026-03-15T00:00:00.000Z'  # "?"
EXAMPLE_CERTIFICATE_EVENT_END = '2026-03-15T00:00:00.000Z'  # "?"
EXAMPLE_CERTIFICATE_EVENT_DATE = '2026-03-15T00:00:00.000Z'  # "?"
EXAMPLE_CERTIFICATE_ISSUED_AT = '2024-01-15T00:00:00.000Z'
EXAMPLE_CERTIFICATE_VALID_UNTIL = '2026-01-15T00:00:00.000Z'


# corriji o de nomenclatura "available"
class Status(str, Enum):
    PENDING = 'pending'
    AVALIABLE = 'available'
    EXPIRED = 'expired'


# Está incorreto porque a documentação exige validar o certificado usando fullname,
# email e accessKey, mas o schema atual só recebe event_id e opcionalmente
# access_key, sem campos para fullname e email.


class CreateCertificate(BaseModel):
    # access_key pode ser opcional — o servidor pode gerar se não enviado
    fullname: str = Field(
        ...,
        description=DESC_REQ_CERTIFICATE_FULLNAME,
        example=EXAMPLE_REQ_CERTIFICATE_FULLNAME,
    )

    access_key: str = Field(
        ...,
        description=DESC_CERTIFICATE_ACCESS_KEY,
        example=EXAMPLE_CERTIFICATE_ACCESS_KEY,
    )
    event_id: str = Field(
        ...,
        description=DESC_CERTIFICATE_EVENT_ID,
        example=EXAMPLE_CERTIFICATE_EVENT_ID,
    )
    status: Status = Field(
        ..., description=DESC_CERTIFICATE_STATUS, example=Status.PENDING
    )
    email: EmailStr = Field(
        ...,
        description=DESC_REQ_CERTIFICATE_EMAIL,
        example=EXAMPLE_REQ_CERTIFICATE_EMAIL,
    )


class RequestCertificate(BaseModel):
    user_id: str = Field(
        ...,
        description=DESC_CERTIFICATE_USER_ID,
        example=EXAMPLE_CERTIFICATE_USER_ID,
    )


class RequestCertificateById(BaseModel):
    id: str = Field(
        ..., description=DESC_CERTIFICATE_ID, example=EXAMPLE_CERTIFICATE_ID
    )


# alterado para CertificateInDb , refletindo o modelo completo no banco de dados
class CertificateInDb(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(
        ...,
        alias='_id',
        description=DESC_CERTIFICATE_ID,
        example=EXAMPLE_CERTIFICATE_ID,
    )
    user_id: str = Field(
        ...,
        description=DESC_CERTIFICATE_USER_ID,
        example=EXAMPLE_CERTIFICATE_USER_ID,
    )
    access_key: str = Field(
        ...,
        description=DESC_CERTIFICATE_ACCESS_KEY,
        example=EXAMPLE_CERTIFICATE_ACCESS_KEY,
    )
    status: Status = Field(
        ...,
        description=DESC_CERTIFICATE_STATUS,
        example=Status.PENDING,
        examples=[Status.PENDING, Status.AVALIABLE, Status.EXPIRED],
    )
    participant_name: str = Field(
        ...,
        max_length=PARTICIPANT_MAX,
        min_length=PARTICIPANT_MIN,
        description=DESC_CERTIFICATE_PARTICIPANT_NAME,
        example=EXAMPLE_CERTIFICATE_PARTICIPANT_NAME,
    )
    participant_email: EmailStr = Field(
        ...,
        description=DESC_CERTIFICATE_PARTICIPANT_EMAIL,
        example=EXAMPLE_CERTIFICATE_PARTICIPANT_EMAIL,
    )
    institution_name: str = Field(
        ...,
        description=DESC_CERTIFICATE_INSTITUTION_NAME,
        example=EXAMPLE_CERTIFICATE_INSTITUTION_NAME,
    )
    event_id: str = Field(
        ...,
        description=DESC_CERTIFICATE_EVENT_ID,
        example=EXAMPLE_CERTIFICATE_EVENT_ID,
    )
    event_name: str = Field(
        ...,
        description=DESC_CERTIFICATE_EVENT_NAME,
        example=EXAMPLE_CERTIFICATE_EVENT_NAME,
    )
    description: str = Field(
        ...,
        description=DESC_CERTIFICATE_DESCRIPTION,
        example=EXAMPLE_CERTIFICATE_DESCRIPTION,
    )
    workload: str = Field(
        ...,
        description=DESC_CERTIFICATE_WORKLOAD,
        example=EXAMPLE_CERTIFICATE_WORKLOAD,
    )
    event_start: Optional[datetime] = Field(
        None,  # Explicitamente opcional
        description=DESC_CERTIFICATE_EVENT_START,
        example=EXAMPLE_CERTIFICATE_EVENT_START,
    )
    event_end: Optional[datetime] = Field(
        None,  # Explicitamente opcional
        description=DESC_CERTIFICATE_EVENT_END,
        example=EXAMPLE_CERTIFICATE_EVENT_END,
    )
    event_date: Optional[datetime] = Field(
        None,  # Explicitamente opcional
        description=DESC_CERTIFICATE_EVENT_DATE,
        example=EXAMPLE_CERTIFICATE_EVENT_DATE,
    )
    issued_at: Optional[datetime] = Field(
        None,  # Explicitamente opcional
        description=DESC_CERTIFICATE_ISSUED_AT,
        example=EXAMPLE_CERTIFICATE_ISSUED_AT,
    )
    valid_until: datetime = Field(
        ...,
        description=DESC_CERTIFICATE_VALID_UNTIL,
        example=EXAMPLE_CERTIFICATE_VALID_UNTIL,
    )
