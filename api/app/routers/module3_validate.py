"""
Módulo 3 - Validação de Contatos
Endpoint para validar número de WhatsApp de comprador/vendedor
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["Module 3 - Validate Contact"])


class ValidateContactRequest(BaseModel):
    phone: str
    order_id: Optional[str] = None


class ValidateContactResponse(BaseModel):
    status: str
    message: str
    validation_id: Optional[str] = None


@router.post("/validate-contact", status_code=200, response_model=ValidateContactResponse)
async def validate_contact(request: Request):
    """
    Endpoint para validar número de WhatsApp de comprador/vendedor.
    
    Recebe:
    {
        "phone": "5511999999999",
        "order_id": "123"
    }
    
    Retorna:
    {
        "status": "pending",
        "message": "Código enviado"
    }
    
    Integração futura: Evolution API para enviar código de validação
    """
    try:
        body = await request.json()
        phone = body.get("phone", "")
        order_id = body.get("order_id", "")
        
        print(f"[VALIDATE] Recebido: phone={phone}, order_id={order_id}")
        
        # TODO: Implementar integração com Evolution API
        # Por enquanto, apenas log e retorno placeholder
        
        return ValidateContactResponse(
            status="pending",
            message="Validação em breve - Evolution API não integrada",
            validation_id=f"val_{order_id}_{phone[-4:]}" if phone else None
        )
    except Exception as e:
        print(f"[VALIDATE] Erro: {e}")
        return ValidateContactResponse(
            status="error",
            message=f"Erro no processamento: {str(e)}"
        )


@router.get("/validate-contact/status/{validation_id}", status_code=200)
async def validation_status(validation_id: str):
    """
    Verifica status da validação
    """
    return {
        "validation_id": validation_id,
        "status": "pending",
        "message": "Aguardando confirmação do usuário",
        "verified": False
    }
