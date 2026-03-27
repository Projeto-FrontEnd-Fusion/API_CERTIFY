from pydantic import BaseModel

from api_certify.models.auth_model import Role, AuthUserReponse


# Model para o token de acesso retornando ao usuário
class Token(BaseModel):
    access_token: str
    expires_in: int


# Dados dentro do JWT (payload)
class TokenData(BaseModel):
    sub: str  # ID  do usuário
    role: Role  # Permissão
    iss: str = 'api_certify'  # Quem emitiu
    aud: str = 'api_certify'  # Para quem o token se destina
    iat: int | None = None  # Timestamp indicando quando o token foi gerado
    exp: int | None = None  # Timestamp indicando até quando o token é válido


# Resposta para o cliente/frontend ao logar
class TokenResponse(BaseModel):
    user: AuthUserReponse
    access_token: str


# TODO: Alterar e retirar user e deixar token_type e access_token para enviar no oauth scheme
