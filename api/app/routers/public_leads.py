from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.leads import Lead
from app.schemas.leads import LeadCreate

router = APIRouter(prefix="/public", tags=["public"])

# naive in-memory rate limit (MVP). For multi-instance, move to Redis.
_LAST_BY_IP: dict[str, float] = {}


@router.post("/leads")
def create_lead(payload: LeadCreate, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    last = _LAST_BY_IP.get(ip, 0)
    if now - last < 2.0:
        raise HTTPException(429, "too_many_requests")
    _LAST_BY_IP[ip] = now

    lead = Lead(
        name=payload.name.strip(),
        email=(payload.email or "").strip() or None,
        phone=(payload.phone or "").strip() or None,
        profile=(payload.profile or "").strip() or None,
        uf=(payload.uf or "").strip().upper() or None,
        property_value=payload.property_value,
        message=(payload.message or "").strip() or None,
        consent=bool(payload.consent),
    )
    db.add(lead)
    db.commit()
    return {"ok": True, "id": lead.id}
