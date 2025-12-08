from pydantic import BaseModel


# Resposta de token
class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Validação de dados
class LoginSchema(BaseModel):
    email: str
    senha: str
