from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import getenv
from app.crud.webhook_events import record_event
from app.db.session import get_db

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _validate_rmchat(request: Request):
    # RMChat: token fixo via header. Preferir Authorization: Bearer <token>.
    expected = getenv("RMCHAT_WEBHOOK_SECRET", "")
    if not expected:
        raise HTTPException(status_code=500, detail="missing_RMCHAT_WEBHOOK_SECRET")

    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        if token == expected:
            return

    # fallback (se RMChat usar header alternativo)
    token2 = request.headers.get("X-RMChat-Token")
    if token2 and token2 == expected:
        return

    raise HTTPException(status_code=401, detail="invalid_rmchat_webhook_token")


@router.post("/rmchat")
async def rmchat_webhook(request: Request, db: Session = Depends(get_db)):
    _validate_rmchat(request)

    payload = await request.json()
    event_type = payload.get("event") or payload.get("type")
    external_event_id = payload.get("id") or payload.get("event_id")

    if not event_type or not external_event_id:
        raise HTTPException(400, "missing_event_fields")

    raw = json.dumps(payload, ensure_ascii=False)

    is_new = record_event(db, provider="rmchat", external_id=str(external_event_id), raw=raw)
    if not is_new:
        return {"ok": True, "duplicate": True}

    # MVP: por enquanto só registra o evento.
    # Próximo passo: mapear message.received -> atualizar lead/order e (se preciso) abrir tarefa para humano.

    return {"ok": True}
