import re

from pydantic import BaseModel, EmailStr, Field, field_validator

PASSWORD_MIN = 8


def validar_cnpj(cnpj: str) -> str:
    cnpj = re.sub(r"\D", "", cnpj)

    if len(cnpj) != 14:
        raise ValueError("CNPJ deve conter 14 dígitos")

    if cnpj == cnpj[0] * 14:
        raise ValueError("CNPJ inválido")

    if not _validar_digitos_verificadores(cnpj):
        raise ValueError("CNPJ inválido")

    return cnpj


def _validar_digitos_verificadores(cnpj: str) -> bool:
    def calcular_digito(base, pesos):
        soma = sum(int(d) * p for d, p in zip(base, pesos))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    base = cnpj[:12]

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    dig1 = calcular_digito(base, pesos1)

    pesos2 = [6] + pesos1
    dig2 = calcular_digito(base + dig1, pesos2)

    return cnpj.endswith(dig1 + dig2)


class CreateCompany(BaseModel):
    razao_social: str = Field(..., min_length=3, max_length=200)
    cnpj: str
    email: EmailStr
    password: str = Field(..., min_length=PASSWORD_MIN)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        return validar_cnpj(v)


class CompanyResponse(BaseModel):
    id: str
    razao_social: str
    cnpj: str
    email: EmailStr
    phone: str | None = None
    role: str = "empresa"
