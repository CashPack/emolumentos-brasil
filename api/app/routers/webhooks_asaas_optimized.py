from __future__ import annotations

import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.config import getenv
from app.crud.webhook_events import record_event
from app.db.session import get_db
from app.models.orders import Order
from app.services.rmchat import send_template

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _validate_asaas(request: Request):
    """Valida o token do Asaas - resposta rápida"""
    token = request.headers.get("access-token") or request.headers.get("asaas-access-token")
    expected = getenv("ASAAS_WEBHOOK_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=500, detail="missing_ASAAS_WEBHOOK_TOKEN")
    if not token or token != expected:
        raise HTTPException(status_code=401, detail="invalid_asaas_webhook_token")


async def _process_payment_webhook(payload: dict, db: Session):
    """Processa o pagamento em background - não bloqueia a resposta"""
    try:
        event_type = payload.get("event") or payload.get("type")
        external_event_id = payload.get("id") or payload.get("eventId")

        if not event_type or not external_event_id:
            return

        # Idempotência
        is_new = record_event(db, provider="asaas", external_id=str(external_event_id), raw=json.dumps(payload, ensure_ascii=False))
        if not is_new:
            return

        payment = payload.get("payment") or {}
        charge_id = payment.get("id")

        customer = payment.get("customer") or payload.get("customer") or {}
        customer_phone = (
            customer.get("phone")
            or customer.get("mobilePhone")
            or payment.get("phone")
            or payment.get("mobilePhone")
            or None
        )

        order = None
        if charge_id:
            order = db.query(Order).filter(Order.asaas_charge_id == str(charge_id)).one_or_none()

        if order is None and charge_id:
            order = Order(
                asaas_charge_id=str(charge_id),
                customer_whatsapp=(str(customer_phone).strip() if customer_phone else None),
                status="COBRANCA_CRIADA",
            )
            db.add(order)
            db.commit()
            db.refresh(order)

        if order:
            if event_type in ("PAYMENT_CONFIRMED", "PAYMENT_RECEIVED"):
                order.status = "PAGO"
                db.add(order)
                db.commit()

                # Enviar WhatsApp em background
                template = getenv("RMCHAT_PAYMENT_CONFIRMED_TEMPLATE", "")
                if template and order.customer_whatsapp:
                    try:
                        await send_template(
                            to=order.customer_whatsapp,
                            template=template,
                            variables={"order_id": order.id, "charge_id": order.asaas_charge_id},
                        )
                    except Exception as e:
                        print(f"[asaas] rmchat send failed: {e}")

            elif event_type in ("PAYMENT_OVERDUE",):
                order.status = "AGUARDANDO_PAGAMENTO"
                db.add(order)
                db.commit()

            elif event_type in ("PAYMENT_REFUNDED", "PAYMENT_DELETED"):
                order.status = "CANCELADO"
                db.add(order)
                db.commit()

    except Exception as e:
        print(f"[asaas] background processing failed: {e}")


@router.post("/asaas")
async def asaas_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Endpoint otimizado - resposta rápida em 200ms"""
    _validate_asaas(request)

    try:
        payload = await request.json()
        
        # Processar em background - não bloqueia a resposta
        background_tasks.add_task(_process_payment_webhook, payload, db)
        
        # Responder imediatamente
        return {"ok": True, "processing": "background"}
        
    except Exception as e:
        # Mesmo com erro, responder com 200 para não penalizar
        print(f"[asaas] error processing webhook: {e}")
        return {"ok": True, "error": str(e), "processing": "failed"}