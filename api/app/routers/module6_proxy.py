"""
Módulo 6 - Recebimento de Procuração Lavrada
Endpoint para receber PDF da procuração lavrada enviada pelo comprador
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

router = APIRouter(prefix="/api", tags=["Module 6 - Proxy"])


class ProxyReceivedResponse(BaseModel):
    status: str
    proxy_id: str
    message: str
    order_id: Optional[str] = None
    received_at: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None


@router.post("/proxy-received", status_code=200, response_model=ProxyReceivedResponse)
async def proxy_received(
    file: UploadFile = File(...),
    order_id: str = Form(...),
    cartorio_id: str = Form(...),  # ID do cartório que enviou
    assinado: bool = Form(False),   # Se já foi assinado digitalmente
) -> ProxyReceivedResponse:
    """
    Recebe PDF da procuração lavrada enviada pelo comprador ou cartório.
    
    Args:
        file: PDF da procuração lavrada
        order_id: ID do pedido relacionado
        cartorio_id: ID do cartório que enviou
        assinado: Indica se o documento já tem assinatura digital
    
    Retorna:
    {
        "status": "received",
        "proxy_id": "proxy_abc123",
        "message": "Procuração recebida com sucesso"
    }
    
    TODO:
    - Validar assinatura digital (se houver)
    - Integrar com sistema de arquivamento
    - Notificar corretor e cliente
    - Mover pedido para próxima etapa (escritura)
    """
    try:
        proxy_id = f"proxy_{uuid.uuid4().hex[:8]}"
        
        # Ler conteúdo
        content = await file.read()
        file_size = len(content)
        
        print(f"[PROXY] Recebida procuração para pedido: {order_id}")
        print(f"[PROXY] Arquivo: {file.filename}")
        print(f"[PROXY] Tamanho: {file_size} bytes")
        print(f"[PROXY] Cartório: {cartorio_id}")
        print(f"[PROXY] Assinado digitalmente: {assinado}")
        print(f"[PROXY] Proxy ID: {proxy_id}")
        
        # TODO: Salvar em storage permanente
        # TODO: Validar se é PDF válido
        # TODO: Verificar assinatura digital (se assinado=True)
        
        return ProxyReceivedResponse(
            status="received",
            proxy_id=proxy_id,
            message="Procuração recebida com sucesso (placeholder)",
            order_id=order_id,
            received_at=datetime.now().isoformat(),
            filename=file.filename,
            size=file_size
        )
    except Exception as e:
        print(f"[PROXY] Erro: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no recebimento: {str(e)}")


@router.get("/proxy/{proxy_id}/status", status_code=200)
async def proxy_status(proxy_id: str):
    """
    Verifica status da procuração recebida
    """
    return {
        "proxy_id": proxy_id,
        "status": "received",
        "validated": False,
        "archived": False,
        "next_step": "aguardando_validacao",
        "message": "Procuração recebida, aguardando validação"
    }


@router.post("/proxy/{proxy_id}/validate", status_code=200)
async def validate_proxy(proxy_id: str):
    """
    Valida procuração recebida (futuro: OCR + verificação cartório)
    """
    return {
        "proxy_id": proxy_id,
        "status": "validated",
        "validated_at": datetime.now().isoformat(),
        "valid": True,
        "issues": [],
        "message": "Procuração validada com sucesso"
    }
