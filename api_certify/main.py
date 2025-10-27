from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from api_certify.core.database.mongodb import (
    mongodb_connect,
    mongodb_disconnect,
)
from api_certify.routes.v1.auth_routes import auth_routes
from api_certify.exceptions.exeptions import http_exception_handler, validation_exception_handler
from fastapi.exceptions import RequestValidationError


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongodb_connect()
    print('Conectado com Sucesso')
    yield
    await mongodb_disconnect()
    print('Conexão encerrada')


app = FastAPI(
    title='Certify Api',
    description=(
        'Api desenvolvida para gerenciar a'
        'plataforma Certify da comunidade frontend Fusion'
    ),
    version='1.0.1',
    lifespan=lifespan,
)


@app.get('/health')
def me():
    return {'message': 'API Certify está rodando!'}

api_prefix = "/api/v1"
app.include_router(auth_routes, prefix=api_prefix )
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
