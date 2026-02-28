"""
Webhook para receber eventos da Evolution API (WhatsApp)
Processa confirmações de entrega e respostas de validação
"""
import json
from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.validation import ContactValidation

router = APIRouter(prefix="/webhooks/evolution", tags=["Webhooks"])


@router.post("")
async def evolution_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recebe webhooks da Evolution API
    
    Eventos processados:
    -messages.upsert: Nova mensagem recebida (pode ser resposta de validação)
    -messages.update: Atualização de status (entregue, lida, etc)
    """
    try:
        data = await request.json()
        event_type = data.get("event", "")
        
        print(f"[EVOLUTION WEBHOOK] Evento: {event_type}")
        print(f"[EVOLUTION WEBHOOK] Dados: {json.dumps(data, indent=2)}")
        
        # Processa mensagem recebida
        if event_type == "messages.upsert":
            await process_incoming_message(data, db)
        
        # Processa atualização de status
        elif event_type == "messages.update":
            await process_status_update(data, db)
        
        return {"success": True, "message": "Webhook processado"}
        
    except Exception as e:
        print(f"[EVOLUTION WEBHOOK] Erro: {e}")
        return {"success": False, "error": str(e)}


async def process_incoming_message(data: dict, db: Session):
    """
    Processa mensagem recebida do WhatsApp
    Verifica se é resposta de código de validação
    """
    try:
        message_data = data.get("data", {})
        message = message_data.get("message", {})
        
        # Extrai informações da mensagem
        remote_jid = message.get("remoteJid", "")
        text = ""
        
        # Extrai texto da mensagem
        if "conversation" in message:
            text = message["conversation"]
        elif "extendedTextMessage" in message:
            text = message["extendedTextMessage"].get("text", "")
        
        # Verifica se é mensagem de grupo (ignora)
        if "@g.us" in remote_jid:
            return
        
        # Extrai número de telefone (remove @s.whatsapp.net)
        phone = remote_jid.split("@")[0]
        
        print(f"[EVOLUTION] Mensagem de {phone}: {text}")
        
        # Procura validação pendente para este número
        validation = db.query(ContactValidation).filter(
            ContactValidation.phone == phone,
            ContactValidation.status == "pending"
        ).order_by(ContactValidation.created_at.desc()).first()
        
        if not validation:
            print(f"[EVOLUTION] Nenhuma validação pendente para {phone}")
            return
        
        # Verifica se a mensagem contém o código de validação
        code_received = ''.join(filter(str.isdigit, text))
        
        if code_received == validation.code:
            # Código confere! Atualiza status
            from datetime import datetime
            validation.status = "validated"
            validation.validated_at = datetime.utcnow()
            validation.webhook_received = True
            validation.webhook_data = json.dumps({
                "confirmed_via": "webhook",
                "message_text": text,
                "received_at": datetime.utcnow().isoformat()
            })
            db.commit()
            
            print(f"[EVOLUTION] Código confirmado via webhook para {validation.validation_id}")
            
            # Envia mensagem de confirmação
            # TODO: Implementar envio de "Código confirmado com sucesso!"
            
        else:
            print(f"[EVOLUTION] Código recebido ({code_received}) não confere com esperado ({validation.code})")
            
    except Exception as e:
        print(f"[EVOLUTION] Erro ao processar mensagem: {e}")


async def process_status_update(data: dict, db: Session):
    """
    Processa atualização de status de mensagem (entregue, lida, etc)
    """
    try:
        status_data = data.get("data", {})
        message_id = status_data.get("key", {}).get("id", "")
        status = status_data.get("status", "")
        
        print(f"[EVOLUTION] Status update: {message_id} -> {status}")
        
        # Aqui pode-se implementar lógica para rastrear entrega de mensagens
        
    except Exception as e:
        print(f"[EVOLUTION] Erro ao processar status: {e}")
