"""
Background workers para webhooks - processamento assíncrono
Isolamos operações lentas (banco, WhatsApp) do endpoint principal
para garantir resposta rápida ao Asaas (<1s).
"""

import asyncio
import logging

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.orders import Order
from app.services.rmchat import send_template
from app.core.config import getenv

logger = logging.getLogger(__name__)


async def processar_pagamento_recebido(payload: dict, db: Session) -> None:
    """
    Processamento pesado em background para evento PAYMENT_RECEIVED/PAYMENT_CONFIRMED.
    
    Fluxo:
    1. Buscar pedido no banco (lento)
    2. Atualizar status para PAGO (lento)
    3. Disparar WhatsApp via RMChat (lento)
    4. Log
    
    Tudo isso roda em background sem bloquear a resposta ao Asaas.
    """
    try:
        payment = payload.get("payment") or {}
        payment_id = payment.get("id")
        customer = payment.get("customer") or payload.get("customer") or {}
        customer_phone = (
            customer.get("phone")
            or customer.get("mobilePhone")
            or payment.get("phone")
            or payment.get("mobilePhone")
            or None
        )

        if not payment_id:
            logger.warning("[asaas-background] payment_id não encontrado no payload")
            return

        # Buscar pedido (lento)
        order = db.query(Order).filter(Order.asaas_charge_id == str(payment_id)).one_or_none()

        # MVP: cria o pedido se ainda não existir e tiver payment_id
        if order is None:
            order = Order(
                asaas_charge_id=str(payment_id),
                customer_whatsapp=(str(customer_phone).strip() if customer_phone else None),
                status="COBRANCA_CRIADA",
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            logger.info(f"[asaas-background] Pedido criado: {order.id}")

        if order:
            # Atualizar status (lento)
            order.status = "PAGO"
            db.add(order)
            db.commit()

            # Disparar WhatsApp (lento - RMChat)
            template = getenv("RMCHAT_PAYMENT_CONFIRMED_TEMPLATE", "")
            if template and order.customer_whatsapp:
                try:
                    await send_template(
                        to=order.customer_whatsapp,
                        template=template,
                        variables={
                            "order_id": order.id,
                            "charge_id": order.asaas_charge_id,
                        },
                    )
                    logger.info(f"[asaas-background] ✅ WhatsApp enviado para {order.customer_whatsapp}")
                except Exception as e:
                    logger.error(f"[asaas-background] Erro ao enviar WhatsApp: {e}")
            else:
                logger.warning(f"[asaas-background] Template não configurado ou sem telefone")

        logger.info(f"[asaas-background] ✅ Pagamento {payment_id} processado com sucesso")

    except Exception as e:
        logger.error(f"[asaas-background] ❌ Erro no background: {e}", exc_info=True)
        # Importante: não re-raise para não causar retry no Asaas
        # O importante é que o endpoint já respondeu 200 OK
