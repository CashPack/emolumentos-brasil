import logging
import sys

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.routers import auth, users, emoluments
from app.routers import emoluments_calc
from app.routers import emoluments_crud
from app.routers import public_leads
from app.routers import webhooks_asaas_optimized as webhooks_asaas
from app.routers import webhooks_rmchat
from app.routers import webhooks_evolution
from app.routers import module3_validate
from app.routers import corretor
from app.routers import modelos
from app.services.seed import ensure_admin
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.emoluments import EmolumentBracket, EmolumentTable, TableStatus
from app.models.validation import ContactValidation
from app.models.corretor import Corretor
from app.models.modelos_documentos import ModeloDocumento, VersaoModelo, Cartorio

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

# CORS configurado para aceitar requisições da landing page e do Bolt
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://praticodocumentos.com.br",
        "https://www.praticodocumentos.com.br",
        "https://admin.praticodocumentos.com.br",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:4321",
        "https://pr-tico-documentos-o-863e.bolt.host",
        "https://*.bolt.host",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


class CalcularResponse(BaseModel):
    uf: str
    valor: float
    custo_local: float
    custo_pratico: float
    economia: float
    economia_pct: float
    comissao_corretor: float


def get_emolumento_for_value(uf: str, property_value: float, db: Session):
    """Busca o emolumento para um valor específico em uma UF."""
    t = (
        db.query(EmolumentTable)
        .filter(EmolumentTable.uf == uf, EmolumentTable.status == TableStatus.active)
        .order_by(EmolumentTable.year.desc(), EmolumentTable.created_at.desc())
        .first()
    )
    if not t:
        return None

    bs = (
        db.query(EmolumentBracket)
        .filter(EmolumentBracket.table_id == t.id, EmolumentBracket.active == True)
        .order_by(EmolumentBracket.range_from.asc())
        .all()
    )
    for b in bs:
        if float(b.range_from) <= property_value <= float(b.range_to):
            return float(b.amount)

    # fallback: above last range
    if bs and property_value > float(bs[-1].range_to):
        return float(bs[-1].amount)

    return None


@app.post("/calcular", response_model=CalcularResponse)
def calcular_landing(request: CalcularRequest, db: Session = Depends(get_db)):
    """Endpoint simplificado para calculadora da landing page."""
    uf = request.uf.strip().upper()
    valor = request.valor

    # Obtém emolumento local
    custo_local = get_emolumento_for_value(uf, valor, db)
    if custo_local is None:
        raise HTTPException(404, "Tabela não encontrada para a UF informada")

    # Busca o menor emolumento entre todas as UFs
    tables = (
        db.query(EmolumentTable)
        .filter(EmolumentTable.status == TableStatus.active)
        .all()
    )

    menor_emolumento = custo_local
    for t in tables:
        emol = get_emolumento_for_value(t.uf, valor, db)
        if emol and emol < menor_emolumento:
            menor_emolumento = emol

    economia = round(custo_local - menor_emolumento, 2)
    economia_pct = round((economia / custo_local) * 100, 2) if custo_local else 0
    comissao_corretor = round(economia * 0.35, 2)

    return CalcularResponse(
        uf=uf,
        valor=valor,
        custo_local=custo_local,
        custo_pratico=menor_emolumento,
        economia=economia,
        economia_pct=economia_pct,
        comissao_corretor=comissao_corretor,
    )


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(emoluments.router)
app.include_router(emoluments_calc.router)
app.include_router(emoluments_crud.router)
app.include_router(public_leads.router)
app.include_router(webhooks_asaas.router)
app.include_router(webhooks_rmchat.router)
app.include_router(webhooks_evolution.router)
app.include_router(module3_validate.router)
app.include_router(corretor.router)
app.include_router(modelos.router)
