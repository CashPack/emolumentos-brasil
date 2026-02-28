"""
Módulo 4 - Upload de Documentos
Endpoint para receber documentos enviados pelo corretor/cliente
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import uuid

router = APIRouter(prefix="/api", tags=["Module 4 - Documents"])


class DocumentUploadResponse(BaseModel):
    status: str
    file_id: str
    message: str
    filename: Optional[str] = None
    size: Optional[int] = None
    order_id: Optional[str] = None


@router.post("/documents/upload", status_code=200, response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    order_id: str = Form(...),
    document_type: str = Form("other")  # rg, cnh, contrato, etc.
):
    """
    Recebe documentos enviados pelo corretor/cliente.
    
    Args:
        file: Arquivo a ser enviado (PDF, JPG, PNG)
        order_id: ID do pedido relacionado
        document_type: Tipo do documento (rg, cnh, contrato, outro)
    
    Retorna:
    {
        "status": "received",
        "file_id": "temp_123",
        "message": "Documento recebido"
    }
    
    TODO: 
    - Salvar em storage permanente (S3, GCP, etc.)
    - Integrar com OCR para extração de dados
    - Validar tipos de arquivo permitidos
    """
    try:
        # Gerar ID único para o arquivo
        file_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        # Ler conteúdo (temporariamente)
        content = await file.read()
        file_size = len(content)
        
        print(f"[UPLOAD] Recebido arquivo: {file.filename}")
        print(f"[UPLOAD] Tamanho: {file_size} bytes")
        print(f"[UPLOAD] Tipo: {file.content_type}")
        print(f"[UPLOAD] Pedido: {order_id}")
        print(f"[UPLOAD] Tipo documento: {document_type}")
        print(f"[UPLOAD] File ID: {file_id}")
        
        # TODO: Salvar em storage permanente
        # Por enquanto, apenas log e retorno placeholder
        
        return DocumentUploadResponse(
            status="received",
            file_id=file_id,
            message=f"Documento '{document_type}' recebido com sucesso (placeholder)",
            filename=file.filename,
            size=file_size,
            order_id=order_id
        )
    except Exception as e:
        print(f"[UPLOAD] Erro: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")


@router.get("/documents/{file_id}/status", status_code=200)
async def document_status(file_id: str):
    """
    Verifica status do processamento do documento
    """
    return {
        "file_id": file_id,
        "status": "received",
        "processing": "pending",
        "ocr_status": "not_started",
        "message": "Documento aguardando processamento OCR"
    }


@router.get("/documents/{file_id}/download", status_code=200)
async def download_document(file_id: str):
    """
    Download do documento (futuro)
    """
    return {
        "file_id": file_id,
        "download_url": "#",
        "message": "Download disponível em breve"
    }
