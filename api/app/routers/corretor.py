"""
Módulo 0 - Cadastro de Corretores
Endpoint para onboarding de corretores parceiros via WhatsApp
"""
import os
import json
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import (
    APIRouter, Request, Depends, HTTPException, 
    BackgroundTasks, File, UploadFile, Form
)
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.corretor import Corretor, DocumentStatus
from app.services.evolution_service import send_text_message
from app.services.ocr_service import extract_document_data
from app.services.creci_validator import validate_creci
from app.services.asaas_service import create_asaas_account

router = APIRouter(prefix="/api/corretor", tags=["Module 0 - Cadastro Corretor"])


# ==================== MODELOS DE REQUISIÇÃO/RESPOSTA ====================

class StartCadastroRequest(BaseModel):
    phone: str
    name: Optional[str] = None


class StartCadastroResponse(BaseModel):
    success: bool
    cadastro_id: str
    message: str
    next_step: str


class DocumentUploadResponse(BaseModel):
    success: bool
    document_type: str
    status: str
    extracted_data: Optional[dict] = None
    message: str


class DadosPessoaisRequest(BaseModel):
    cadastro_id: str
    nome: str
    cpf: str
    data_nascimento: str
    creci_numero: str
    creci_uf: str
    email: str


class DadosPessoaisResponse(BaseModel):
    success: bool
    creci_valido: bool
    asaas_account: Optional[dict] = None
    message: str


class CadastroStatusResponse(BaseModel):
    cadastro_id: str
    status: str
    progresso: int  # 0-100%
    documentos: dict
    dados_pessoais: Optional[dict]
    contrato_gerado: bool
    contrato_url: Optional[str]


# ==================== ENDPOINTS PRINCIPAIS ====================

@router.post("/iniciar", response_model=StartCadastroResponse)
async def iniciar_cadastro(
    request: StartCadastroRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Inicia processo de cadastro de corretor.
    
    Envia mensagem de boas-vindas via WhatsApp com instruções.
    """
    try:
        # Gera ID único para o cadastro
        cadastro_id = str(uuid.uuid4())[:8]
        
        # Cria registro no banco
        corretor = Corretor(
            cadastro_id=cadastro_id,
            phone=request.phone,
            nome=request.name or "",
            status="iniciado",
            created_at=datetime.utcnow()
        )
        db.add(corretor)
        db.commit()
        
        # Envia mensagem de boas-vindas via WhatsApp
        mensagem = f"""
👋 Bem-vindo à PRÁTICO Documentos!

Sou seu assistente para o cadastro de corretor parceiro. 

Para prosseguir, vou precisar de alguns documentos:

📄 *Documentos necessários:*
1️⃣ RG ou CNH (foto frente e verso)
2️⃣ Carteira do CRECI (frente e verso) 
3️⃣ Comprovante de residência

Envie os documentos *um por vez*, enviando a foto diretamente aqui no WhatsApp.

Seu código de cadastro: *{cadastro_id}*
        """.strip()
        
        background_tasks.add_task(
            send_text_message,
            phone=request.phone,
            text=mensagem
        )
        
        return StartCadastroResponse(
            success=True,
            cadastro_id=cadastro_id,
            message="Cadastro iniciado. Verifique seu WhatsApp.",
            next_step="enviar_documentos"
        )
        
    except Exception as e:
        print(f"[CADASTRO] Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/documento")
async def receber_documento_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook para receber documentos enviados via WhatsApp (Evolution API).
    
    Processa automaticamente:
    1. Recebe imagem/documento
    2. Baixa arquivo
    3. Identifica tipo de documento (RG, CNH, CRECI, Comprovante)
    4. Extrai dados via OCR (Google Document AI)
    5. Atualiza cadastro no banco
    """
    try:
        data = await request.json()
        
        # Extrai informações do webhook da Evolution
        event = data.get("event", "")
        message_data = data.get("data", {})
        
        # Só processa mensagens com mídia (imagem/documento)
        if event not in ["messages.upsert"]:
            return {"success": True, "message": "Evento ignorado"}
        
        message = message_data.get("message", {})
        remote_jid = message.get("remoteJid", "")
        phone = remote_jid.split("@")[0]
        
        # Verifica se há mídia (imagem)
        has_image = "imageMessage" in message
        has_document = "documentMessage" in message
        
        if not has_image and not has_document:
            return {"success": True, "message": "Mensagem sem mídia"}
        
        # Busca cadastro ativo para este número
        corretor = db.query(Corretor).filter(
            Corretor.phone == phone,
            Corretor.status.in_(["iniciado", "documentos_pendentes", "aguardando_dados"])
        ).order_by(Corretor.created_at.desc()).first()
        
        if not corretor:
            # Envia mensagem orientando a iniciar cadastro primeiro
            background_tasks.add_task(
                send_text_message,
                phone=phone,
                text="📋 Para enviar documentos, primeiro inicie seu cadastro em: https://praticodocumentos.com.br/corretor"
            )
            return {"success": False, "message": "Cadastro não encontrado"}
        
        # Extrai URL da mídia
        media_url = None
        if has_image:
            media_url = message["imageMessage"].get("url") or message["imageMessage"].get("mediaUrl")
        elif has_document:
            media_url = message["documentMessage"].get("url") or message["documentMessage"].get("mediaUrl")
        
        if not media_url:
            return {"success": False, "message": "URL da mídia não encontrada"}
        
        # Processa documento em background
        background_tasks.add_task(
            processar_documento,
            corretor_id=corretor.id,
            cadastro_id=corretor.cadastro_id,
            phone=phone,
            media_url=media_url,
            db_session_factory=get_db
        )
        
        # Envia confirmação imediata
        background_tasks.add_task(
            send_text_message,
            phone=phone,
            text="📎 Documento recebido! Estou processando..."
        )
        
        return {
            "success": True,
            "message": "Documento recebido e em processamento",
            "cadastro_id": corretor.cadastro_id
        }
        
    except Exception as e:
        print(f"[DOCUMENTO WEBHOOK] Erro: {e}")
        return {"success": False, "error": str(e)}


@router.post("/dados-pessoais", response_model=DadosPessoaisResponse)
async def receber_dados_pessoais(
    request: DadosPessoaisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Recebe dados pessoais do corretor após extração OCR.
    
    Valida:
    1. CRECI na UF informada
    2. Cria conta Asaas para split de pagamentos
    """
    try:
        # Busca cadastro
        corretor = db.query(Corretor).filter(
            Corretor.cadastro_id == request.cadastro_id
        ).first()
        
        if not corretor:
            raise HTTPException(status_code=404, detail="Cadastro não encontrado")
        
        # Atualiza dados
        corretor.nome = request.nome
        corretor.cpf = request.cpf
        corretor.data_nascimento = request.data_nascimento
        corretor.creci_numero = request.creci_numero
        corretor.creci_uf = request.creci_uf.upper()
        corretor.email = request.email
        corretor.status = "validando_creci"
        db.commit()
        
        # Valida CRECI em background
        creci_result = await validate_creci(
            numero=request.creci_numero,
            uf=request.creci_uf
        )
        
        if not creci_result.get("valido", False):
            corretor.status = "creci_invalido"
            db.commit()
            return DadosPessoaisResponse(
                success=False,
                creci_valido=False,
                message=f"CRECI inválido: {creci_result.get('mensagem', 'Não foi possível validar')}"
            )
        
        corretor.creci_validado = True
        corretor.status = "criando_asaas"
        db.commit()
        
        # Cria conta no Asaas
        asaas_result = await create_asaas_account(
            nome=request.nome,
            cpf=request.cpf,
            email=request.email,
            phone=corretor.phone
        )
        
        if asaas_result.get("success", False):
            corretor.asaas_customer_id = asaas_result.get("customer_id")
            corretor.asaas_wallet_id = asaas_result.get("wallet_id")
            corretor.status = "conta_criada"
            db.commit()
            
            # Envia notificação
            background_tasks.add_task(
                send_text_message,
                phone=corretor.phone,
                text=f"""
✅ Dados validados e conta criada!

Seu CRECI foi validado com sucesso.
Sua conta para recebimento de comissões está configurada.

Próximo passo: assinatura do contrato de parceria.
                """.strip()
            )
            
            return DadosPessoaisResponse(
                success=True,
                creci_valido=True,
                asaas_account={
                    "customer_id": asaas_result.get("customer_id"),
                    "wallet_id": asaas_result.get("wallet_id")
                },
                message="Dados validados e conta Asaas criada com sucesso!"
            )
        else:
            corretor.status = "erro_asaas"
            db.commit()
            return DadosPessoaisResponse(
                success=False,
                creci_valido=True,
                message=f"Erro ao criar conta Asaas: {asaas_result.get('error', 'Erro desconhecido')}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[DADOS PESSOAIS] Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{cadastro_id}", response_model=CadastroStatusResponse)
async def consultar_status(
    cadastro_id: str,
    db: Session = Depends(get_db)
):
    """
    Consulta status completo do cadastro do corretor.
    """
    try:
        corretor = db.query(Corretor).filter(
            Corretor.cadastro_id == cadastro_id
        ).first()
        
        if not corretor:
            raise HTTPException(status_code=404, detail="Cadastro não encontrado")
        
        # Calcula progresso
        progresso = 0
        documentos = {
            "rg_cnh": corretor.doc_rg_status or "pendente",
            "creci": corretor.doc_creci_status or "pendente",
            "comprovante": corretor.doc_comprovante_status or "pendente"
        }
        
        # Conta documentos enviados
        docs_enviados = sum(1 for d in documentos.values() if d in ["recebido", "processado"])
        progresso += (docs_enviados / 3) * 40  # 40% para documentos
        
        if corretor.creci_validado:
            progresso += 30  # 30% para validação CRECI
        
        if corretor.asaas_wallet_id:
            progresso += 20  # 20% para conta Asaas
        
        if corretor.contrato_assinado:
            progresso += 10  # 10% para contrato
        
        return CadastroStatusResponse(
            cadastro_id=cadastro_id,
            status=corretor.status,
            progresso=int(progresso),
            documentos=documentos,
            dados_pessoais={
                "nome": corretor.nome,
                "cpf": corretor.cpf,
                "creci": f"{corretor.creci_numero}/{corretor.creci_uf}" if corretor.creci_numero else None,
                "email": corretor.email
            } if corretor.nome else None,
            contrato_gerado=corretor.contrato_gerado,
            contrato_url=corretor.contrato_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== FUNÇÕES AUXILIARES ====================

def processar_documento(
    corretor_id: int,
    cadastro_id: str,
    phone: str,
    media_url: str,
    db_session_factory
):
    """
    Processa documento recebido:
    1. Baixa imagem
    2. Identifica tipo via OCR
    3. Extrai dados
    4. Atualiza banco
    5. Envia confirmação
    """
    from app.db.session import SessionLocal
    db = SessionLocal()
    
    try:
        corretor = db.query(Corretor).filter(Corretor.id == corretor_id).first()
        if not corretor:
            print(f"[PROCESSAR] Corretor {corretor_id} não encontrado")
            return
        
        # Baixa imagem
        import requests
        response = requests.get(media_url, timeout=30)
        if response.status_code != 200:
            print(f"[PROCESSAR] Erro ao baixar imagem: {response.status_code}")
            return
        
        image_bytes = response.content
        print(f"[PROCESSAR] Imagem baixada: {len(image_bytes)} bytes")
        
        # Identifica tipo de documento via OCR
        ocr_result = extract_document_data(image_bytes)
        doc_type = ocr_result.get("document_type", "unknown")
        
        print(f"[PROCESSAR] Tipo detectado: {doc_type}")
        
        # Atualiza cadastro conforme tipo
        if doc_type in ["rg", "cnh"]:
            corretor.doc_rg_url = media_url
            corretor.doc_rg_status = "processado"
            corretor.doc_rg_data = json.dumps(ocr_result.get("data", {}))
            
            # Extrai dados se possível
            if "nome" in ocr_result.get("data", {}):
                corretor.nome_temp = ocr_result["data"]["nome"]
            if "cpf" in ocr_result.get("data", {}):
                corretor.cpf_temp = ocr_result["data"]["cpf"]
                
        elif doc_type == "creci":
            corretor.doc_creci_url = media_url
            corretor.doc_creci_status = "processado"
            corretor.doc_creci_data = json.dumps(ocr_result.get("data", {}))
            
            # Extrai número e UF do CRECI
            if "creci_numero" in ocr_result.get("data", {}):
                corretor.creci_numero_temp = ocr_result["data"]["creci_numero"]
            if "creci_uf" in ocr_result.get("data", {}):
                corretor.creci_uf_temp = ocr_result["data"]["creci_uf"]
                
        elif doc_type == "comprovante":
            corretor.doc_comprovante_url = media_url
            corretor.doc_comprovante_status = "processado"
            corretor.doc_comprovante_data = json.dumps(ocr_result.get("data", {}))
        
        # Atualiza status geral
        if corretor.doc_rg_status == "processado" and corretor.doc_creci_status == "processado" and corretor.doc_comprovante_status == "processado":
            corretor.status = "aguardando_dados"
        else:
            corretor.status = "documentos_pendentes"
        
        db.commit()
        
        # Envia confirmação
        tipo_nome = {"rg": "RG", "cnh": "CNH", "creci": "CRECI", "comprovante": "Comprovante de Residência"}.get(doc_type, "Documento")
        send_text_message(
            phone=phone,
            text=f"✅ {tipo_nome} processado com sucesso!\n\nDados extraídos via OCR."
        )
        
        # Se todos documentos enviados, solicita confirmação de dados
        if corretor.status == "aguardando_dados":
            send_text_message(
                phone=phone,
                text=f"""
🎉 Todos os documentos recebidos!

Dados extraídos:
👤 Nome: {corretor.nome_temp or 'Não identificado'}
🆔 CPF: {corretor.cpf_temp or 'Não identificado'}
🏷️ CRECI: {corretor.creci_numero_temp or 'Não identificado'}/{corretor.creci_uf_temp or ''}

Por favor, confirme ou corrija estes dados para prosseguir.
                """.strip()
            )
        
        print(f"[PROCESSAR] Documento {doc_type} processado para {cadastro_id}")
        
    except Exception as e:
        print(f"[PROCESSAR] Erro: {e}")
    finally:
        db.close()
