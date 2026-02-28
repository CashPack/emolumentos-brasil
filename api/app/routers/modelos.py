"""
Endpoints para gestão de modelos de documentos
Upload, download, versionamento e gerenciamento de modelos
"""
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File, 
    Form, Query, status
)
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.modelos_documentos import ModeloDocumento, VersaoModelo, TipoModelo, Cartorio
from app.services.modelo_processor import processar_modelo

router = APIRouter(prefix="/api/modelos", tags=["Gestão de Modelos"])

# Configuração de storage
UPLOAD_DIR = os.getenv("MODELS_UPLOAD_DIR", "/data/modelos")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==================== MODELOS Pydantic ====================

class ModeloCreate(BaseModel):
    nome: str
    tipo: TipoModelo
    descricao: Optional[str] = None
    cartorio_id: Optional[str] = None


class ModeloResponse(BaseModel):
    id: str
    nome: str
    tipo: str
    descricao: Optional[str]
    cartorio_id: Optional[str]
    versao_atual: int
    ativo: bool
    metadados: dict
    criado_em: datetime
    
    class Config:
        from_attributes = True


class VersaoResponse(BaseModel):
    id: str
    versao: int
    motivo_alteracao: Optional[str]
    criado_em: datetime
    criado_por: Optional[str]


# ==================== ENDPOINTS ====================

@router.get("", response_model=List[ModeloResponse])
async def listar_modelos(
    tipo: Optional[TipoModelo] = Query(None, description="Filtrar por tipo"),
    cartorio_id: Optional[str] = Query(None, description="Filtrar por cartório (null = globais)"),
    ativos_only: bool = Query(True, description="Apenas modelos ativos"),
    db: Session = Depends(get_db)
):
    """
    Lista modelos de documentos com filtros
    """
    query = db.query(ModeloDocumento)
    
    if tipo:
        query = query.filter(ModeloDocumento.tipo == tipo)
    
    if cartorio_id:
        query = query.filter(ModeloDocumento.cartorio_id == cartorio_id)
    elif cartorio_id is not None:  # Se explicitamente null, busca globais
        query = query.filter(ModeloDocumento.cartorio_id.is_(None))
    
    if ativos_only:
        query = query.filter(ModeloDocumento.ativo == True)
    
    modelos = query.order_by(ModeloDocumento.criado_em.desc()).all()
    
    return [
        {
            "id": str(m.id),
            "nome": m.nome,
            "tipo": m.tipo.value,
            "descricao": m.descricao,
            "cartorio_id": str(m.cartorio_id) if m.cartorio_id else None,
            "versao_atual": m.versao_atual,
            "ativo": m.ativo,
            "metadados": m.metadados or {},
            "criado_em": m.criado_em
        }
        for m in modelos
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_modelo(
    nome: str = Form(..., description="Nome do modelo"),
    tipo: TipoModelo = Form(..., description="Tipo do documento"),
    arquivo: UploadFile = File(..., description="Arquivo DOCX ou PDF"),
    descricao: Optional[str] = Form(None, description="Descrição opcional"),
    cartorio_id: Optional[str] = Form(None, description="ID do cartório (se modelo específico)"),
    criado_por: Optional[str] = Form(None, description="ID do usuário"),
    db: Session = Depends(get_db)
):
    """
    Faz upload de novo modelo de documento
    Processa o arquivo e extrai metadados (placeholders, campos)
    """
    # Valida extensão
    extensao = os.path.splitext(arquivo.filename)[1].lower()
    if extensao not in ['.docx', '.pdf']:
        raise HTTPException(
            status_code=400, 
            detail="Tipo de arquivo não suportado. Envie DOCX ou PDF."
        )
    
    # Cria ID único para o modelo
    modelo_id = uuid.uuid4()
    
    # Define caminho de storage
    storage_path = os.path.join(UPLOAD_DIR, str(modelo_id))
    os.makedirs(storage_path, exist_ok=True)
    
    arquivo_path = os.path.join(storage_path, f"v1{extensao}")
    
    # Salva arquivo
    try:
        with open(arquivo_path, "wb") as f:
            shutil.copyfileobj(arquivo.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")
    
    # Processa arquivo para extrair metadados
    resultado = processar_modelo(arquivo_path)
    
    # Cria registro no banco
    modelo = ModeloDocumento(
        id=modelo_id,
        nome=nome,
        tipo=tipo,
        descricao=descricao,
        cartorio_id=uuid.UUID(cartorio_id) if cartorio_id else None,
        arquivo_path=arquivo_path,
        versao_atual=1,
        ativo=True,
        metadados={
            "campos_extraidos": resultado.get("campos", []),
            "placeholders": resultado.get("placeholders", []),
            "tipo_arquivo": resultado.get("tipo_arquivo"),
            "total_campos": resultado.get("total_campos", 0),
            "erro_processamento": resultado.get("erro")
        },
        criado_por=criado_por
    )
    
    db.add(modelo)
    db.flush()
    
    # Cria versão inicial
    versao = VersaoModelo(
        id=uuid.uuid4(),
        modelo_id=modelo_id,
        arquivo_path=arquivo_path,
        versao=1,
        motivo_alteracao="Upload inicial",
        criado_por=criado_por
    )
    db.add(versao)
    db.commit()
    
    return {
        "success": True,
        "id": str(modelo_id),
        "nome": nome,
        "tipo": tipo.value,
        "versao": 1,
        "metadados": modelo.metadados,
        "message": "Modelo criado com sucesso"
    }


@router.get("/{modelo_id}")
async def download_modelo(
    modelo_id: str,
    versao: Optional[int] = Query(None, description="Versão específica (se não informado, baixa a atual)"),
    db: Session = Depends(get_db)
):
    """
    Download do arquivo do modelo
    """
    modelo = db.query(ModeloDocumento).filter(ModeloDocumento.id == modelo_id).first()
    
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    
    # Se versão específica foi solicitada
    if versao:
        versao_obj = db.query(VersaoModelo).filter(
            VersaoModelo.modelo_id == modelo_id,
            VersaoModelo.versao == versao
        ).first()
        
        if not versao_obj:
            raise HTTPException(status_code=404, detail=f"Versão {versao} não encontrada")
        
        arquivo_path = versao_obj.arquivo_path
    else:
        arquivo_path = modelo.arquivo_path
    
    if not os.path.exists(arquivo_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no storage")
    
    # Determina media type
    extensao = os.path.splitext(arquivo_path)[1]
    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if extensao == '.docx' else "application/pdf"
    
    return FileResponse(
        arquivo_path,
        media_type=media_type,
        filename=f"{modelo.nome}_v{versao or modelo.versao_atual}{extensao}"
    )


@router.put("/{modelo_id}")
async def atualizar_modelo(
    modelo_id: str,
    arquivo: UploadFile = File(..., description="Novo arquivo (DOCX ou PDF)"),
    motivo: str = Form(..., description="Motivo da alteração"),
    criado_por: Optional[str] = Form(None, description="ID do usuário"),
    db: Session = Depends(get_db)
):
    """
    Atualiza modelo para nova versão
    Mantém histórico de versões anteriores
    """
    modelo = db.query(ModeloDocumento).filter(ModeloDocumento.id == modelo_id).first()
    
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    
    # Valida extensão
    extensao = os.path.splitext(arquivo.filename)[1].lower()
    if extensao not in ['.docx', '.pdf']:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não suportado")
    
    # Incrementa versão
    nova_versao = modelo.versao_atual + 1
    
    # Define novo caminho
    storage_path = os.path.dirname(modelo.arquivo_path)
    novo_arquivo_path = os.path.join(storage_path, f"v{nova_versao}{extensao}")
    
    # Salva nova versão
    try:
        with open(novo_arquivo_path, "wb") as f:
            shutil.copyfileobj(arquivo.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")
    
    # Processa nova versão
    resultado = processar_modelo(novo_arquivo_path)
    
    # Atualiza modelo
    modelo.arquivo_path = novo_arquivo_path
    modelo.versao_atual = nova_versao
    modelo.metadados = {
        "campos_extraidos": resultado.get("campos", []),
        "placeholders": resultado.get("placeholders", []),
        "tipo_arquivo": resultado.get("tipo_arquivo"),
        "total_campos": resultado.get("total_campos", 0)
    }
    modelo.atualizado_em = datetime.utcnow()
    
    # Cria registro de versão
    versao_obj = VersaoModelo(
        id=uuid.uuid4(),
        modelo_id=modelo.id,
        arquivo_path=novo_arquivo_path,
        versao=nova_versao,
        motivo_alteracao=motivo,
        criado_por=criado_por
    )
    db.add(versao_obj)
    db.commit()
    
    return {
        "success": True,
        "id": str(modelo_id),
        "nome": modelo.nome,
        "versao_anterior": nova_versao - 1,
        "versao_atual": nova_versao,
        "metadados": modelo.metadados,
        "message": f"Modelo atualizado para versão {nova_versao}"
    }


@router.post("/{modelo_id}/ativar")
async def ativar_versao_modelo(
    modelo_id: str,
    versao: int,
    db: Session = Depends(get_db)
):
    """
    Ativa uma versão específica do modelo (rollback)
    """
    modelo = db.query(ModeloDocumento).filter(ModeloDocumento.id == modelo_id).first()
    
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    
    versao_obj = db.query(VersaoModelo).filter(
        VersaoModelo.modelo_id == modelo_id,
        VersaoModelo.versao == versao
    ).first()
    
    if not versao_obj:
        raise HTTPException(status_code=404, detail=f"Versão {versao} não encontrada")
    
    if not os.path.exists(versao_obj.arquivo_path):
        raise HTTPException(status_code=404, detail="Arquivo da versão não encontrado")
    
    # Atualiza modelo para apontar para versão antiga
    modelo.arquivo_path = versao_obj.arquivo_path
    modelo.versao_atual = versao
    modelo.atualizado_em = datetime.utcnow()
    
    # Reprocessa metadados
    resultado = processar_modelo(versao_obj.arquivo_path)
    modelo.metadados = {
        "campos_extraidos": resultado.get("campos", []),
        "placeholders": resultado.get("placeholders", []),
        "tipo_arquivo": resultado.get("tipo_arquivo"),
        "total_campos": resultado.get("total_campos", 0),
        "observacao": f"Rollback para versão {versao}"
    }
    
    db.commit()
    
    return {
        "success": True,
        "id": str(modelo_id),
        "versao_ativada": versao,
        "message": f"Modelo revertido para versão {versao}"
    }


@router.get("/{modelo_id}/versoes", response_model=List[VersaoResponse])
async def listar_versoes(
    modelo_id: str,
    db: Session = Depends(get_db)
):
    """
    Lista histórico de versões do modelo
    """
    modelo = db.query(ModeloDocumento).filter(ModeloDocumento.id == modelo_id).first()
    
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    
    versoes = db.query(VersaoModelo).filter(
        VersaoModelo.modelo_id == modelo_id
    ).order_by(VersaoModelo.versao.desc()).all()
    
    return [
        {
            "id": str(v.id),
            "versao": v.versao,
            "motivo_alteracao": v.motivo_alteracao,
            "criado_em": v.criado_em,
            "criado_por": v.criado_por
        }
        for v in versoes
    ]


@router.delete("/{modelo_id}")
async def desativar_modelo(
    modelo_id: str,
    db: Session = Depends(get_db)
):
    """
    Desativa um modelo (soft delete)
    """
    modelo = db.query(ModeloDocumento).filter(ModeloDocumento.id == modelo_id).first()
    
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    
    modelo.ativo = False
    modelo.atualizado_em = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": "Modelo desativado com sucesso"
    }


@router.get("/{modelo_id}/metadados")
async def obter_metadados(
    modelo_id: str,
    db: Session = Depends(get_db)
):
    """
    Retorna metadados extraídos do modelo (campos, placeholders)
    """
    modelo = db.query(ModeloDocumento).filter(ModeloDocumento.id == modelo_id).first()
    
    if not modelo:
        raise HTTPException(status_code=404, detail="Modelo não encontrado")
    
    return {
        "id": str(modelo_id),
        "nome": modelo.nome,
        "tipo": modelo.tipo.value,
        "versao_atual": modelo.versao_atual,
        "metadados": modelo.metadados or {},
        "campos_sugeridos": modelo.metadados.get("campos_extraidos", []) if modelo.metadados else []
    }
