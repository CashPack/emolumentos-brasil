"""
Background workers para webhooks - processamento assíncrono
Isolamos operações lentas (banco, WhatsApp) do endpoint principal
para garantir resposta rápida ao Asaas (<1s).
"""

import asyncio
import json
import logging

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.orders import Order
from app.services.rmchat import send_template
from app.core.config import getenv

logger = logging.getLogger(__name__)


async def processar_pagamento_recebido(payload, db: Session) -> None:
    """
    Processamento pesado em background para evento PAYMENT_RECEIVED/PAYMENT_CONFIRMED.
    
    Fluxo:
    1. Buscar pedido no banco (lento)
    2. Atualizar status para PAGO (lento)
    3. Disparar WhatsApp via RMChat (lento)
    4. Log
    
    Tudo isso roda em background sem bloquear a resposta ao Asaas.
    
    NOTE: O payload pode vir como string ou dict, convertemos para dict automaticamente.
    """
    try:
        logger.info(f"[asaas-background] INICIANDO PROCESSAMENTO - Payload tipo: {type(payload)}")
        
        # Converter string para dict se necessário
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
                logger.info("[asaas-background] Payload convertido de string para dict")
            except json.JSONDecodeError as e:
                logger.error(f"[asaas-background] Erro ao converter payload: {e}")
                return
        
        logger.info(f"[asaas-background] Payload processado - Tipo: {type(payload)}")
        
        payment = payload.get("payment") or {}
        logger.info(f"[asaas-background] Payment dict extraído - Tipo: {type(payment)}")
        
        payment_id = payment.get("id") if isinstance(payment, dict) else None
        logger.info(f"[asaas-background] payment_id extraído: {payment_id}")
        
        if not payment_id:
            logger.warning("[asaas-background] payment_id não encontrado no payload")
            logger.warning(f"[asaas-background] Payload completo: {payload}")
            return

        customer = payment.get("customer") or payload.get("customer") or {}
        logger.info(f"[asaas-background] Customer dict extraído - Tipo: {type(customer)}")
        
        customer_phone = (
            customer.get("phone")
            or customer.get("mobilePhone")
            or payment.get("phone")
            or payment.get("mobilePhone")
            or None
        )
        logger.info(f"[asaas-background] customer_phone extraído: {customer_phone}")

        if not payment_id:
            logger.warning("[asaas-background] payment_id não encontrado no payload")
            return

        # Buscar pedido (lento)
        order = db.query(Order).filter(Order.asaas_charge_id == str(payment_id)).one_or_none()
        logger.info(f"[asaas-background] Pedido encontrado: {order is not None}")

        # MVP: cria o pedido se ainda não existir e tiver payment_id
        if order is None:
            logger.info(f"[asaas-background] Criando novo pedido com payment_id: {payment_id}")
            order = Order(
                asaas_charge_id=str(payment_id),
                customer_whatsapp=(str(customer_phone).strip() if customer_phone else None),
                status="COBRANCA_CRIADA",
            )
            db.add(order)
            db.commit()
            db.refresh(order)
            logger.info(f"[asaas-background] ✅ Pedido criado: {order.id} com WhatsApp: {order.customer_whatsapp}")
        else:
            logger.info(f"[asaas-background] ✅ Pedido já existente: {order.id}")

        if order:
            logger.info(f"[asaas-background] Atualizando status para PAGO - Pedido ID: {order.id}")
            # Atualizar status (lento)
            order.status = "PAGO"
            db.add(order)
            db.commit()
            logger.info(f"[asaas-background] ✅ Status atualizado para PAGO")

            # Disparar WhatsApp (lento - RMChat)
            template = getenv("RMCHAT_PAYMENT_CONFIRMED_TEMPLATE", "")
            logger.info(f"[asaas-background] Verificando template de WhatsApp: template='{template}', phone='{order.customer_whatsapp}'")
            
            if template and order.customer_whatsapp:
                logger.info(f"[asaas-background] 🚀 TENTANDO ENVIAR WHATSAPP para {order.customer_whatsapp}")
                try:
                    await send_template(
                        to=order.customer_whatsapp,
                        template=template,
                        variables={
                            "order_id": order.id,
                            "charge_id": order.asaas_charge_id,
                        },
                    )
                    logger.info(f"[asaas-background] ✅ WhatsApp enviado com sucesso para {order.customer_whatsapp}")
                except Exception as e:
                    logger.error(f"[asaas-background] ❌ Erro ao enviar WhatsApp: {e}", exc_info=True)
                    logger.error(f"[asaas-background] ❌ Template: {template}")
                    logger.error(f"[asaas-background] ❌ Phone: {order.customer_whatsapp}")
            else:
                logger.warning(f"[asaas-background] ❌ NÃO ENVIANDO WHATSAPP - Template: {bool(template)}, Phone: {bool(order.customer_whatsapp)}")
                if not template:
                    logger.error(f"[asaas-background] ❌ Template RMCHAT_PAYMENT_CONFIRMED_TEMPLATE não configurado no ambiente!")
                if not order.customer_whatsapp:
                    logger.error(f"[asaas-background] ❌ customer_whatsapp está vazio no pedido {order.id}!")

        logger.info(f"[asaas-background] ✅ PROCESSAMENTO CONCLUÍDO com sucesso para pagamento {payment_id}")

    except Exception as e:
        logger.error(f"[asaas-background] ❌ ERRO FATAL NO PROCESSAMENTO: {e}", exc_info=True)
        # Importante: não re-raise para não causar retry no Asaas
        # O importante é que o endpoint já respondeu 200 OK
