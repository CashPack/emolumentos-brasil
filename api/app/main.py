import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.routers import auth, users, emoluments
from app.routers import emoluments_calc
from app.routers import emoluments_crud
from app.routers import public_leads
from app.routers import webhooks_asaas_optimized as webhooks_asaas
from app.routers import webhooks_rmchat
from app.routers import modules_3_to_6
from app.routers import module3_validate
from app.routers import module4_documents
from app.routers import module5_drafts
from app.routers import module6_proxy
from app.routers.emoluments_calc import calcular_economia
from app.services.seed import ensure_admin
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db

# Configuração de logging para aparecer nos logs do Render
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Forçar nível INFO para loggers específicos
logging.getLogger("app.workers.webhook_tasks").setLevel(logging.INFO)
logging.getLogger("asaas-background").setLevel(logging.INFO)

app = FastAPI(title="Pratico Admin API", version="0.1.0")

# MVP: libera CORS para uso do admin web (e testes via browser). Em produção,
# restringimos para o domínio do painel.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)


@app.on_event("startup")
def on_startup():
    # Simple MVP approach: create tables on startup
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = ensure_admin(db)
        # log in Render runtime logs
        print(f"[seed] {result}")
    finally:
        db.close()


@app.get("/health")
def health():
    return {"ok": True}


# Endpoint simplificado para a landing page (POST /calcular)
class CalcularRequest(BaseModel):
    uf: str
    valor: float


@app.post("/calcular")
def calcular_landing(request: CalcularRequest, db: Session = Depends(get_db)):
    """Endpoint simplificado para calculadora da landing page."""
    return calcular_economia(request, db)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(emoluments.router)
app.include_router(emoluments_calc.router)
app.include_router(emoluments_crud.router)
app.include_router(public_leads.router)
app.include_router(webhooks_asaas.router)
app.include_router(webhooks_rmchat.router)
app.include_router(modules_3_to_6.router)
app.include_router(module3_validate.router)
app.include_router(module4_documents.router)
app.include_router(module5_drafts.router)
app.include_router(module6_proxy.router)
