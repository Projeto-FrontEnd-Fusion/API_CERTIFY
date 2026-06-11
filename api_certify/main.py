from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    AutoReconnect,
    NetworkTimeout,
)

from api_certify.core.database.mongodb import mongodb_connect, mongodb_disconnect
from api_certify.exceptions.handlers import (
    generic_exception_handler,
    http_exception_handler,
)
from api_certify.routes.v1.auth_routes import auth_routes
from api_certify.routes.v1.certificate_routes import certificate_routes
from api_certify.routes.v1.event_routes import event_routes


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
    print("Conexão com MongoDB encerrada.")


app = FastAPI(
    title="Certify API",
    description=(
        "API desenvolvida para gerenciar a "
        "plataforma Certify da comunidade Frontend Fusion."
    ),
    version="1.0.1",
    lifespan=lifespan,
)


# Exception Handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# ---------- MIDDLEWARE: Erro de conexão ----------


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
                "message": "Serviço temporariamente indisponível.",
                "error_code": "SERVICE_UNAVAILABLE",
            },
        )
    except RuntimeError as e:
        if "conecta" in str(e).lower():
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "message": "Serviço temporariamente indisponível.",
                    "error_code": "SERVICE_UNAVAILABLE",
                },
            )
        raise


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.certifyfusion.com.br",
        "https://certifyfusion.com.br",
        "http://localhost:5173",
        "https://certify-platform-iota.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Length", "X-Total-Count"],
    max_age=600,
)


# Routes
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API Certify está rodando!"}


API_PREFIX = "/api/v1"

app.include_router(auth_routes, prefix=API_PREFIX)
app.include_router(certificate_routes, prefix=API_PREFIX)
app.include_router(event_routes, prefix=API_PREFIX)
