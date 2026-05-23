from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from api_certify.core.database.mongodb import mongodb_connect, mongodb_disconnect
from api_certify.exceptions.handlers import (
    generic_exception_handler,
    http_exception_handler,
)
from api_certify.routes.v1.auth_routes import auth_routes
from api_certify.routes.v1.certificate_routes import certificate_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongodb_connect()
    print("Conectado com sucesso ao MongoDB.")
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
    return {"message": "Fala, meu Frontend Sênior! Primeiramente, Hello World!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API Certify está rodando!"}


API_PREFIX = "/api/v1"

app.include_router(auth_routes, prefix=API_PREFIX)
app.include_router(certificate_routes, prefix=API_PREFIX)
