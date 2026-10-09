from contextlib import asynccontextmanager
from contextlib import suppress
import asyncio
import logging
import os

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

from api_certify.core.database.mongodb import db_mongo, mongodb_connect, mongodb_disconnect
from api_certify.exceptions.handlers import (
    generic_exception_handler,
    http_exception_handler,
)
from api_certify.routes.v1.auth_routes import auth_routes
from api_certify.routes.v1.certificate_routes import certificate_routes
from api_certify.routes.v1.event_routes import event_routes
from api_certify.routes.v1.upload_routes import upload_routes
from api_certify.service.upload_service import UPLOAD_DIR
from api_certify.service.certificate_email_service import CertificateEmailService
from api_certify.repositories.auth_repository import AuthRepository


async def process_email_queue():
    database = await db_mongo.get_database()
    service = CertificateEmailService(database.get_collection('certificates'), AuthRepository(database))
    while True:
        try:
            await service.dispatch_pending()
        except Exception:
            logging.getLogger(__name__).warning('Certificate email queue unavailable; retrying later')
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await mongodb_connect()
        print('✅ Conectado ao MongoDB com sucesso')
    except RuntimeError as e:
        print(f'❌ {e}')
        raise SystemExit(1)
    worker = None
    if os.getenv('EMAIL_WORKER_ENABLED', 'false').lower() == 'true':
        worker = asyncio.create_task(process_email_queue())
    try:
        yield
    finally:
        if worker:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker
        await mongodb_disconnect()


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


# CORS: em produção, informe a origem do frontend por FRONTEND_URLS
# (lista separada por vírgulas). Mantemos os domínios conhecidos como padrão
# para não quebrar os ambientes locais já existentes.
default_frontend_urls = [
    "https://www.certifyfusion.com.br",
    "https://certifyfusion.com.br",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://certify-platform-iota.vercel.app",
]
frontend_urls = os.getenv("FRONTEND_URLS", "")
allowed_origins = [
    origin.strip()
    for origin in frontend_urls.split(",")
    if origin.strip()
] or default_frontend_urls

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
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


@app.get('/ready')
async def readiness_check():
    try:
        database = await db_mongo.get_database()
        await database.command('ping')
    except Exception:
        return JSONResponse(status_code=503, content={'status': 'not_ready'})
    return {'status': 'ready'}


API_PREFIX = "/api/v1"

app.include_router(auth_routes, prefix=API_PREFIX)
app.include_router(certificate_routes, prefix=API_PREFIX)
app.include_router(event_routes, prefix=API_PREFIX)
app.include_router(upload_routes, prefix=API_PREFIX)

# Servir arquivos estáticos (uploads)
from fastapi.staticfiles import StaticFiles
uploads_path = UPLOAD_DIR
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")
