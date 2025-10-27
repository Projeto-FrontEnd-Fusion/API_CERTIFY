from fastapi import FastAPI
from contextlib import asynccontextmanager
from api_certify.core.database.mongodb import mongodb_connect, mongodb_disconnect


@asynccontextmanager
async def lifespan(app:FastAPI):
  await mongodb_connect()
  print("Conectado com Sucesso")
  yield
  await mongodb_disconnect()
  print("Conexão encerrada")

app = FastAPI(
  title="Certify Api",
  description="Api desenvolvida para gerenciar a plataforma Certify da comunidade frontend Fusion",
  version="1.0.1",
  lifespan=lifespan
)

@app.get("/health")
def me():
  return {"message":"API Certify está rodando!"}