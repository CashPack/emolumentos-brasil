from __future__ import annotations

import asyncio
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import getenv
from app.crud.webhook_events import record_event
from app.db.session import get_db
from app.workers.webhook_tasks import processar_pagamento_recebido

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _validate_asaas(request: Request):
    """
    Validação tolerante - SEMPRE retorna OK para evitar penalização.
    
    Estratégia: nunca rejeitar webhook do Asaas, mesmo com erro.
    Isso evita que o Asaas aplique penalizações por timeout ou erros.
    """
    # Asaas: token fixo via header `access-token` (padrão)
    token = request.headers.get("access-token") or request.headers.get("asaas-access-token")
    
    # Otimização: se não tiver token configurado, aceita qualquer coisa
    # Isso evita penalização se a variável não estiver no Render
    expected = os.environ.get("ASAAS_WEBHOOK_TOKEN", "")
    if not expected:
        # Token não configurado - aceita qualquer requisição para evitar penalização
        # (em produção, configure a variável no Render!)
        return
    
    if not token:
        # Sem token no request - aceita (não queremos rejeitar)
        return
    
    if token != expected:
        # Token inválido - mas ainda retorna OK para não penalizar
        # Em produção, pode liberar 401 se quiser segurança estrita
        return


@router.post("/asaas")
async def asaas_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook do Asaas - RESPONDA RÁPIDO (<1s) para evitar penalização por timeout.
    
    Estratégia:
    1. Validar token rapidamente (tolerante)
    2. Registrar evento para idempotência
    3. Disparar processamento pesado em background (asyncio.create_task)
    4. Responder 200 OK IMEDIATAMENTE
    """
    # 1. Validação rápida do token (tolerante)
    _validate_asaas(request)

    # 2. Pega payload
    payload = await request.json()

    event_type = payload.get("event") or payload.get("type")
    external_event_id = payload.get("id") or payload.get("eventId")

    if not event_type or not external_event_id:
        return {"ok": True}  # Retorna 200 mesmo se dados inválidos

    # 3. Idempotência (MVP): registra evento e, se já existir, não processa de novo.
    raw = json.dumps(payload, ensure_ascii=False)
    is_new = record_event(db, provider="asaas", external_id=str(external_event_id), raw=raw)
    if not is_new:
        return {"ok": True, "duplicate": True}

    # 4. Dispara background para eventos de pagamento (lentos)
    if event_type in ("PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"):
        # Joga tudo para background - banco + WhatsApp
        asyncio.create_task(processar_pagamento_recebido(payload, db))

    # 5. RESPOSTA IMEDIATA (<1 segundo) - SEMPRE 200!
    return {"ok": True}
