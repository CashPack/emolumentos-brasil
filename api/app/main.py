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
from app.services.seed import ensure_admin

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


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(emoluments.router)
app.include_router(emoluments_calc.router)
app.include_router(emoluments_crud.router)
app.include_router(public_leads.router)
app.include_router(webhooks_asaas.router)
app.include_router(webhooks_rmchat.router)
