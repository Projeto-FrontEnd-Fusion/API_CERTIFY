from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from typing import Optional
from datetime import datetime


DESC_EVENT_NAME = 'Nome do evento, curso ou palestra'
DESC_INSTITUTION = 'Nome da instituição organizadora'
DESC_WORKLOAD = 'Carga horária do evento em horas'
DESC_DESCRIPTION = 'Descrição do evento'
DESC_START_DATE = 'Data de início do evento'
DESC_END_DATE = 'Data de término do evento'
DESC_EVENT_ID = 'Identificador único do evento no banco de dados (MongoDB ObjectId)'

EXAMPLE_EVENT_NAME = 'Imersão Dev Insights'
EXAMPLE_INSTITUTION = 'Comunidade Frontend Fusion'
EXAMPLE_WORKLOAD = 9
EXAMPLE_DESCRIPTION = 'Evento voltado ao aprendizado e desenvolvimento em tecnologia.'
EXAMPLE_START_DATE = '2025-11-05T00:00:00.000Z'
EXAMPLE_END_DATE = '2025-11-07T00:00:00.000Z'
EXAMPLE_EVENT_ID = '507f1f77bcf86cd799439011'

EVENT_NAME_MIN = 5
EVENT_NAME_MAX = 200


class CreateEvent(BaseModel):
    name: str = Field(
        ...,
        min_length=EVENT_NAME_MIN,
        max_length=EVENT_NAME_MAX,
        description=DESC_EVENT_NAME,
        example=EXAMPLE_EVENT_NAME,
    )
    institution: str = Field(
        ...,
        description=DESC_INSTITUTION,
        example=EXAMPLE_INSTITUTION,
    )
    workload: int = Field(
        ...,
        description=DESC_WORKLOAD,
        example=EXAMPLE_WORKLOAD,
    )
    description: str = Field(
        ...,
        description=DESC_DESCRIPTION,
        example=EXAMPLE_DESCRIPTION,
    )
    start_date: datetime = Field(
        ...,
        description=DESC_START_DATE,
        example=EXAMPLE_START_DATE,
    )
    end_date: datetime = Field(
        ...,
        description=DESC_END_DATE,
        example=EXAMPLE_END_DATE,
    )

    @field_validator('workload')
    @classmethod
    def workload_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Carga horária deve ser maior que zero')
        return v

    @field_validator('end_date')
    @classmethod
    def end_date_after_start(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('Data de término não pode ser anterior à data de início')
        return v


class EventInDb(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str = Field(
        ...,
        alias='_id',
        description=DESC_EVENT_ID,
        example=EXAMPLE_EVENT_ID,
    )
    name: str = Field(..., description=DESC_EVENT_NAME)
    institution: str = Field(..., description=DESC_INSTITUTION)
    workload: int = Field(..., description=DESC_WORKLOAD)
    description: str = Field(..., description=DESC_DESCRIPTION)
    start_date: datetime = Field(..., description=DESC_START_DATE)
    end_date: datetime = Field(..., description=DESC_END_DATE)
    created_at: Optional[datetime] = None


class UpdateEventSchema(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=EVENT_NAME_MIN,
        max_length=EVENT_NAME_MAX,
        description=DESC_EVENT_NAME,
        example=EXAMPLE_EVENT_NAME,
    )
    workload: Optional[int] = Field(
        None,
        description=DESC_WORKLOAD,
        example=EXAMPLE_WORKLOAD,
    )
    description: Optional[str] = Field(
        None,
        description=DESC_DESCRIPTION,
        example=EXAMPLE_DESCRIPTION,
    )
    start_date: Optional[datetime] = Field(
        None,
        description=DESC_START_DATE,
        example=EXAMPLE_START_DATE,
    )
    end_date: Optional[datetime] = Field(
        None,
        description=DESC_END_DATE,
        example=EXAMPLE_END_DATE,
    )
    @field_validator('workload')
    @classmethod
    def workload_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Carga horária deve ser maior que zero')
        return v

    @model_validator(mode='after')
    def validate_dates_together(self) -> 'UpdateEventSchema':
        start = self.start_date
        end = self.end_date

        if (start is not None and end is None) or (start is None and end is not None):
            raise ValueError('Ambas as datas (início e término) devem ser fornecidas juntas.')

        if (start is not None) and (end is not None):
            if end < start:
                raise ValueError('Data de término não pode ser anterior à data de início')

        return self