from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    AutoReconnect,
    NetworkTimeout,
)

from api_certify.core.database.mongodb import (
    mongodb_connect,
    mongodb_disconnect,
)

from fastapi.middleware.cors import CORSMiddleware
from api_certify.routes.v1.auth_routes import auth_routes
from api_certify.routes.v1.certificate_routes import certificate_routes
from api_certify.routes.v1.event_routes import event_routes
from api_certify.exceptions.exeptions import http_exception_handler, validation_exception_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await mongodb_connect()
        print('✅ Conectado ao MongoDB com sucesso')
    except RuntimeError as e:
        print(f'❌ {e}')
        raise SystemExit(1)
    yield
    await mongodb_disconnect()
    print('Conexão encerrada')


app = FastAPI(
    title='Certify Api',
    description=(
        'Api desenvolvida para gerenciar a '
        'plataforma Certify da comunidade frontend Fusion'
    ),
    version='1.0.1',
    lifespan=lifespan,
)


# ---------- MIDDLEWARE: Erro de conexão MongoDB ----------


@app.middleware("http")
async def database_error_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except (ConnectionFailure, ServerSelectionTimeoutError, AutoReconnect, NetworkTimeout):
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "Serviço temporariamente indisponível. Não foi possível conectar ao banco de dados.",
                "error_code": "DATABASE_UNAVAILABLE",
                "details": "Tente novamente em alguns instantes.",
            },
        )
    except RuntimeError as e:
        if "MongoDB" in str(e) or "conectada" in str(e):
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": "Serviço temporariamente indisponível. Não foi possível conectar ao banco de dados.",
                    "error_code": "DATABASE_UNAVAILABLE",
                    "details": "Tente novamente em alguns instantes.",
                },
            )
        raise


# ---------- CORS ----------


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.certifyfusion.com.br",
        "https://certifyfusion.com.br",
        "http://localhost:5173",
        "https://certify-platform-iota.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Length", "X-Total-Count"],
    max_age=600
)
print("CORS Middleware carregado com sucesso!")


# ---------- ROTAS ----------


@app.get('/')
def root():
    return {'message': "Hello World"}


@app.get('/health')
def health():
    return {'message': 'API Certify está rodando!'}


api_prefix = "/api/v1"
app.include_router(auth_routes, prefix=api_prefix)
app.include_router(certificate_routes, prefix=api_prefix)
app.include_router(event_routes, prefix=api_prefix)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
