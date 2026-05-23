from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    def __init__(self, status_code: int, message: str):
        self.error = self.__class__.__name__
        self.message = message

        super().__init__(
            status_code=status_code,
            detail=message,
        )


class UserNotFoundException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Usuário não encontrado.",
        )


class InvalidCredentialsException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="E-mail ou senha inválidos.",
        )


class DuplicateEntryException(BaseAPIException):
    def __init__(self, field: str = "registro"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=f"Já existe um {field} cadastrado.",
        )


class AccessDeniedException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Acesso negado.",
        )


class QuotaNotEnoughException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Cota insuficiente.",
        )
