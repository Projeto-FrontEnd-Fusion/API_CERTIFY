from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from api_certify.core.database.mongodb import (
    mongodb_connect,
    mongodb_disconnect,
)
from api_certify.exceptions.exeptions import (
    http_exception_handler,
    validation_exception_handler,
)
from api_certify.routes.v1.auth_routes import auth_routes
from api_certify.routes.v1.certificate_routes import certificate_routes
from api_certify.routes.v1.institution_auth_routes import (
    institution_auth_routes,
)


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'https://www.certifyfusion.com.br',
        'https://certifyfusion.com.br',
        'http://localhost:5173',
        'https://certify-platform-iota.vercel.app',
    ],
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization', 'Accept'],
    expose_headers=['Content-Length', 'X-Total-Count'],
    max_age=600,
)
print('CORS Middleware carregado com sucesso!')


@app.get('/')
def me():
    return {'Fala meu Frontend Sênior, Primeiramente': 'Hello World'}


@app.get('/health')
def me():
    return {'message': 'API Certify está rodando!'}


api_prefix = '/api/v1'
app.include_router(auth_routes, prefix=api_prefix)
app.include_router(certificate_routes, prefix=api_prefix)
app.include_router(institution_auth_routes, prefix=api_prefix)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
