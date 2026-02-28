"""
Módulo 0 - Cadastro de Corretores (Fluxo Otimizado - Coleta Única)
Endpoint para onboarding de corretores parceiros via WhatsApp
"""
import os
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import (
    APIRouter, Request, Depends, HTTPException, 
    BackgroundTasks, File, UploadFile, Form
)
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.corretor import Corretor, DocumentStatus
from app.services.evolution_service import send_text_message
from app.services.ocr_service import extract_document_data, detect_document_type
from app.services.creci_validator import validate_creci
from app.services.asaas_service import create_asaas_account
from app.services.contract_generator import generate_partnership_contract, CorretorData

router = APIRouter(prefix="/api/corretor", tags=["Module 0 - Cadastro Corretor"])

# ==================== CONFIGURAÇÕES ====================
DOCUMENT_COLLECTION_TIMEOUT = 30  # segundos para aguardar mais documentos
MIN_DOCUMENTS_REQUIRED = 3  # RG/CNH, CRECI, Comprovante

# ==================== MODELOS DE REQUISIÇÃO/RESPOSTA ====================

class StartCadastroRequest(BaseModel):
    phone: str
    name: Optional[str] = None


class StartCadastroResponse(BaseModel):
    success: bool
    cadastro_id: str
    message: str
    next_step: str


class ConfirmDataRequest(BaseModel):
    cadastro_id: str
    confirmacoes: Dict[str, bool]  # {"nome": true, "cpf": true, ...}
    correcoes: Optional[Dict[str, str]] = None  # {"nome": "Nome Correto"}
    email: str  # Email necessário para Asaas


class ConfirmDataResponse(BaseModel):
    success: bool
    creci_valido: bool
    asaas_account: Optional[dict] = None
    message: str
    pendencias: Optional[List[str]] = None


class CadastroStatusResponse(BaseModel):
    cadastro_id: str
    status: str
    progresso: int
    documentos_recebidos: List[str]
    dados_extraidos: Optional[Dict]
    pendencias: List[str]
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
    Inicia processo de cadastro de corretor com fluxo otimizado de coleta única.
    """
    try:
        cadastro_id = str(uuid.uuid4())[:8]
        
        corretor = Corretor(
            cadastro_id=cadastro_id,
            phone=request.phone,
            nome=request.name or "",
            status="aguardando_documentos",
            created_at=datetime.utcnow(),
            doc_rg_status="pendente",
            doc_creci_status="pendente",
            doc_comprovante_status="pendente"
        )
        db.add(corretor)
        db.commit()
        
        # Mensagem otimizada - instruções de coleta única
        mensagem = f"""
👋 Bem-vindo à PRÁTICO Documentos!

Sou seu assistente para cadastro de corretor parceiro. 

📋 Para agilizar seu cadastro, envie *TODOS OS DOCUMENTOS DE UMA VEZ*:

1️⃣ *RG ou CNH* (foto da frente E verso)
2️⃣ *Carteira do CRECI* (foto da frente E verso)  
3️⃣ *Comprovante de residência* (foto)

💡 *Dica:* Envie tudo em sequência, sem esperar resposta entre um e outro. Assim que receber todos, processo automaticamente!

Seu código de cadastro: *{cadastro_id}*

⏱️ Tempo estimado: 2 minutos
        """.strip()
        
        background_tasks.add_task(
            send_text_message,
            phone=request.phone,
            text=mensagem
        )
        
        return StartCadastroResponse(
            success=True,
            cadastro_id=cadastro_id,
            message="Cadastro iniciado. Envie todos os documentos de uma vez.",
            next_step="enviar_todos_documentos"
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
    Webhook para receber documentos enviados via WhatsApp.
    Acumula documentos e processa em lote após timeout.
    """
    try:
        data = await request.json()
        event = data.get("event", "")
        message_data = data.get("data", {})
        
        if event not in ["messages.upsert"]:
            return {"success": True, "message": "Evento ignorado"}
        
        message = message_data.get("message", {})
        remote_jid = message.get("remoteJid", "")
        phone = remote_jid.split("@")[0]
        
        has_image = "imageMessage" in message
        has_document = "documentMessage" in message
        
        if not has_image and not has_document:
            return {"success": True, "message": "Mensagem sem mídia"}
        
        # Busca ou cria cadastro ativo
        corretor = db.query(Corretor).filter(
            Corretor.phone == phone,
            Corretor.status.in_(["iniciado", "aguardando_documentos", "recebendo_documentos"])
        ).order_by(Corretor.created_at.desc()).first()
        
        if not corretor:
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
        
        # Atualiza status para "recebendo_documentos"
        corretor.status = "recebendo_documentos"
        corretor.last_document_received_at = datetime.utcnow()
        db.commit()
        
        # Acumula documento temporariamente
        # Os documentos são armazenados em uma lista temporária no banco
        documentos_pendentes = json.loads(corretor.temp_documents or "[]")
        documentos_pendentes.append({
            "url": media_url,
            "received_at": datetime.utcnow().isoformat()
        })
        corretor.temp_documents = json.dumps(documentos_pendentes)
        db.commit()
        
        # Agenda processamento em lote após timeout
        # Se já existe uma tarefa agendada, cancela e recria
        background_tasks.add_task(
            processar_documentos_em_lote,
            corretor_id=corretor.id,
            cadastro_id=corretor.cadastro_id,
            phone=phone,
            delay_seconds=DOCUMENT_COLLECTION_TIMEOUT,
            db_session_factory=get_db
        )
        
        # Conta documentos recebidos
        count = len(documentos_pendentes)
        
        if count == 1:
            mensagem = f"📎 Documento {count} recebido! Aguardando mais {MIN_DOCUMENTS_REQUIRED - 1}..."
        elif count < MIN_DOCUMENTS_REQUIRED:
            mensagem = f"📎 Documento {count} recebido! Envie mais {MIN_DOCUMENTS_REQUIRED - count}..."
        else:
            mensagem = f"✅ {count} documentos recebidos! Processando em {DOCUMENT_COLLECTION_TIMEOUT}s..."
        
        background_tasks.add_task(
            send_text_message,
            phone=phone,
            text=mensagem
        )
        
        return {
            "success": True,
            "message": f"Documento {count} acumulado",
            "total_recebidos": count,
            "cadastro_id": corretor.cadastro_id
        }
        
    except Exception as e:
        print(f"[DOCUMENTO WEBHOOK] Erro: {e}")
        return {"success": False, "error": str(e)}


async def processar_documentos_em_lote(
    corretor_id: int,
    cadastro_id: str,
    phone: str,
    delay_seconds: int,
    db_session_factory
):
    """
    Processa todos os documentos acumulados em lote.
    Aguarda timeout e então processa tudo de uma vez.
    """
    # Aguarda timeout para receber mais documentos
    await asyncio.sleep(delay_seconds)
    
    from app.db.session import SessionLocal
    db = SessionLocal()
    
    try:
        corretor = db.query(Corretor).filter(Corretor.id == corretor_id).first()
        if not corretor or corretor.status != "recebendo_documentos":
            print(f"[LOTE] Cadastro {cadastro_id} não está mais em recebimento")
            return
        
        # Recupera documentos acumulados
        documentos = json.loads(corretor.temp_documents or "[]")
        
        if not documentos:
            send_text_message(phone, "⚠️ Nenhum documento recebido. Por favor, envie os documentos.")
            return
        
        print(f"[LOTE] Processando {len(documentos)} documentos para {cadastro_id}")
        
        # Processa cada documento
        resultados = {
            "rg_cnh": [],
            "creci": [],
            "comprovante": [],
            "nao_identificado": []
        }
        
        dados_extraidos = {
            "nome": None,
            "cpf": None,
            "data_nascimento": None,
            "creci_numero": None,
            "creci_uf": None,
            "endereco": None
        }
        
        for idx, doc in enumerate(documentos):
            try:
                # Baixa imagem
                import requests
                response = requests.get(doc["url"], timeout=30)
                if response.status_code != 200:
                    continue
                
                image_bytes = response.content
                
                # Detecta tipo via OCR
                ocr_result = extract_document_data(image_bytes)
                doc_type = ocr_result.get("document_type", "unknown")
                extracted = ocr_result.get("data", {})
                
                print(f"[LOTE] Doc {idx+1}: tipo={doc_type}")
                
                # Categoriza documento
                if doc_type in ["rg", "cnh"]:
                    resultados["rg_cnh"].append(doc)
                    corretor.doc_rg_url = doc["url"]
                    corretor.doc_rg_status = "processado"
                    
                    # Extrai dados pessoais
                    if not dados_extraidos["nome"] and "nome" in extracted:
                        dados_extraidos["nome"] = extracted["nome"]
                    if not dados_extraidos["cpf"] and "cpf" in extracted:
                        dados_extraidos["cpf"] = extracted["cpf"]
                    if not dados_extraidos["data_nascimento"] and "data_nascimento" in extracted:
                        dados_extraidos["data_nascimento"] = extracted["data_nascimento"]
                        
                elif doc_type == "creci":
                    resultados["creci"].append(doc)
                    corretor.doc_creci_url = doc["url"]
                    corretor.doc_creci_status = "processado"
                    
                    if not dados_extraidos["creci_numero"] and "creci_numero" in extracted:
                        dados_extraidos["creci_numero"] = extracted["creci_numero"]
                    if not dados_extraidos["creci_uf"] and "creci_uf" in extracted:
                        dados_extraidos["creci_uf"] = extracted["creci_uf"]
                        
                elif doc_type == "comprovante":
                    resultados["comprovante"].append(doc)
                    corretor.doc_comprovante_url = doc["url"]
                    corretor.doc_comprovante_status = "processado"
                    
                    if not dados_extraidos["endereco"] and "endereco" in extracted:
                        dados_extraidos["endereco"] = extracted["endereco"]
                else:
                    resultados["nao_identificado"].append(doc)
                    
            except Exception as e:
                print(f"[LOTE] Erro ao processar doc {idx+1}: {e}")
        
        # Salva dados extraídos temporiamente
        corretor.dados_extraidos = json.dumps(dados_extraidos)
        corretor.status = "dados_extraidos"
        db.commit()
        
        # Monta lista de pendências
        pendencias = []
        if not resultados["rg_cnh"]:
            pendencias.append("RG ou CNH não identificado")
        if not resultados["creci"]:
            pendencias.append("Carteira CRECI não identificada")
        if not resultados["comprovante"]:
            pendencias.append("Comprovante de residência não identificado")
        if not dados_extraidos["nome"]:
            pendencias.append("Nome não extraído dos documentos")
        if not dados_extraidos["cpf"]:
            pendencias.append("CPF não extraído dos documentos")
        if not dados_extraidos["creci_numero"]:
            pendencias.append("Número do CRECI não extraído")
        
        # Monta resposta para o usuário
        mensagem = montar_mensagem_confirmacao(dados_extraidos, pendencias, len(documentos))
        send_text_message(phone, mensagem)
        
        print(f"[LOTE] Processamento completo. Pendências: {len(pendencias)}")
        
    except Exception as e:
        print(f"[LOTE] Erro: {e}")
        send_text_message(phone, "❌ Erro ao processar documentos. Tente novamente ou entre em contato com o suporte.")
    finally:
        db.close()


def montar_mensagem_confirmacao(dados: Dict, pendencias: List[str], total_docs: int) -> str:
    """Monta mensagem de confirmação com dados extraídos e pendências"""
    
    msg = f"✅ {total_docs} documentos processados!\n\n"
    msg += "📋 *Dados identificados:*\n\n"
    
    if dados["nome"]:
        msg += f"👤 Nome: *{dados['nome']}*\n"
    if dados["cpf"]:
        cpf_formatado = f"{dados['cpf'][:3]}.{dados['cpf'][3:6]}.{dados['cpf'][6:9]}-{dados['cpf'][9:]}"
        msg += f"🆔 CPF: *{cpf_formatado}*\n"
    if dados["data_nascimento"]:
        msg += f"🎂 Nascimento: *{dados['data_nascimento']}*\n"
    if dados["creci_numero"]:
        uf = dados.get("creci_uf", "UF")
        msg += f"🏷️ CRECI: *{dados['creci_numero']}/{uf}*\n"
    if dados["endereco"]:
        msg += f"📍 Endereço: *{dados['endereco'][:50]}...*\n"
    
    if pendencias:
        msg += "\n⚠️ *Precisamos corrigir:*\n"
        for idx, p in enumerate(pendencias, 1):
            msg += f"{idx}. {p}\n"
        msg += "\n📎 *Envie os documentos faltantes ou digite os dados:*\n"
        msg += "_Exemplo: NOME: João Silva, CPF: 12345678900_"
    else:
        msg += "\n🎉 *Todos os dados identificados!*\n"
        msg += "Por favor, confirme seu email para prosseguir:"
    
    return msg


@router.post("/confirmar-dados", response_model=ConfirmDataResponse)
async def confirmar_dados(
    request: ConfirmDataRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Recebe confirmações/correções dos dados e finaliza cadastro.
    Valida CRECI, cria conta Asaas e gera contrato.
    """
    try:
        corretor = db.query(Corretor).filter(
            Corretor.cadastro_id == request.cadastro_id
        ).first()
        
        if not corretor:
            raise HTTPException(status_code=404, detail="Cadastro não encontrado")
        
        # Recupera dados extraídos
        dados_extraidos = json.loads(corretor.dados_extraidos or "{}")
        
        # Aplica confirmações e correções
        dados_finais = {}
        for campo, confirmado in request.confirmacoes.items():
            if confirmado:
                dados_finais[campo] = dados_extraidos.get(campo)
            elif request.correcoes and campo in request.correcoes:
                dados_finais[campo] = request.correcoes[campo]
        
        # Verifica se tem dados mínimos
        campos_obrigatorios = ["nome", "cpf", "creci_numero"]
        faltando = [c for c in campos_obrigatorios if not dados_finais.get(c)]
        
        if faltando:
            return ConfirmDataResponse(
                success=False,
                creci_valido=False,
                message=f"Dados incompletos. Faltando: {', '.join(faltando)}",
                pendencias=faltando
            )
        
        # Atualiza cadastro
        corretor.nome = dados_finais["nome"]
        corretor.cpf = dados_finais["cpf"]
        corretor.data_nascimento = dados_finais.get("data_nascimento")
        corretor.creci_numero = dados_finais["creci_numero"]
        corretor.creci_uf = dados_finais.get("creci_uf", "SP")
        corretor.email = request.email
        corretor.status = "validando_creci"
        db.commit()
        
        # Valida CRECI
        creci_result = await validate_creci(
            numero=corretor.creci_numero,
            uf=corretor.creci_uf
        )
        
        if not creci_result.get("valido", False):
            corretor.status = "creci_invalido"
            db.commit()
            return ConfirmDataResponse(
                success=False,
                creci_valido=False,
                message=f"CRECI inválido: {creci_result.get('mensagem', 'Não foi possível validar')}",
                pendencias=["CRECI inválido - verifique número e UF"]
            )
        
        corretor.creci_validado = True
        corretor.status = "criando_asaas"
        db.commit()
        
        # Cria conta Asaas
        asaas_result = await create_asaas_account(
            nome=corretor.nome,
            cpf=corretor.cpf,
            email=corretor.email,
            phone=corretor.phone,
            external_reference=corretor.cadastro_id
        )
        
        if asaas_result.get("success", False):
            corretor.asaas_customer_id = asaas_result.get("customer_id")
            corretor.asaas_wallet_id = asaas_result.get("wallet_id")
            corretor.status = "gerando_contrato"
            db.commit()
            
            # Gera contrato
            corretor_data = CorretorData(
                nome=corretor.nome,
                cpf=corretor.cpf,
                creci_numero=corretor.creci_numero,
                creci_uf=corretor.creci_uf,
                email=corretor.email,
                phone=corretor.phone
            )
            
            contrato = generate_partnership_contract(corretor_data)
            corretor.contrato_gerado = True
            corretor.contrato_url = contrato.get("assinatura_url")
            corretor.status = "aguardando_assinatura"
            db.commit()
            
            # Mensagem de sucesso
            background_tasks.add_task(
                send_text_message,
                phone=corretor.phone,
                text=f"""
🎉 Cadastro quase completo!

✅ Dados validados
✅ CRECI confirmado  
✅ Conta Asaas criada
✅ Contrato gerado

📄 *Próximo passo:* Assine o contrato digital

Link para assinatura: {contrato.get('assinatura_url') or 'Em breve'}

Após assinar, seu cadastro estará ativo e você poderá começar a indicar clientes!
                """.strip()
            )
            
            return ConfirmDataResponse(
                success=True,
                creci_valido=True,
                asaas_account={
                    "customer_id": asaas_result.get("customer_id"),
                    "wallet_id": asaas_result.get("wallet_id")
                },
                message="Cadastro finalizado! Aguardando assinatura do contrato."
            )
        else:
            corretor.status = "erro_asaas"
            db.commit()
            return ConfirmDataResponse(
                success=False,
                creci_valido=True,
                message=f"Erro ao criar conta Asaas: {asaas_result.get('error', 'Erro desconhecido')}",
                pendencias=["Erro na criação da conta de pagamentos"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CONFIRMAR] Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{cadastro_id}", response_model=CadastroStatusResponse)
async def consultar_status(
    cadastro_id: str,
    db: Session = Depends(get_db)
):
    """Consulta status completo do cadastro do corretor."""
    try:
        corretor = db.query(Corretor).filter(
            Corretor.cadastro_id == cadastro_id
        ).first()
        
        if not corretor:
            raise HTTPException(status_code=404, detail="Cadastro não encontrado")
        
        # Calcula progresso
        progresso = 0
        docs_recebidos = []
        
        if corretor.doc_rg_status == "processado":
            docs_recebidos.append("RG/CNH")
            progresso += 20
        if corretor.doc_creci_status == "processado":
            docs_recebidos.append("CRECI")
            progresso += 20
        if corretor.doc_comprovante_status == "processado":
            docs_recebidos.append("Comprovante")
            progresso += 10
        if corretor.dados_extraidos:
            progresso += 20
        if corretor.creci_validado:
            progresso += 15
        if corretor.asaas_wallet_id:
            progresso += 10
        if corretor.contrato_gerado:
            progresso += 5
        
        # Identifica pendências
        pendencias = []
        dados = json.loads(corretor.dados_extraidos or "{}")
        
        if corretor.status in ["aguardando_documentos", "recebendo_documentos"]:
            if corretor.doc_rg_status != "processado":
                pendencias.append("RG ou CNH")
            if corretor.doc_creci_status != "processado":
                pendencias.append("Carteira CRECI")
            if corretor.doc_comprovante_status != "processado":
                pendencias.append("Comprovante de residência")
        elif corretor.status == "dados_extraidos":
            if not dados.get("nome"):
                pendencias.append("Confirmação do nome")
            if not dados.get("cpf"):
                pendencias.append("Confirmação do CPF")
            if not dados.get("creci_numero"):
                pendencias.append("Confirmação do CRECI")
            if not corretor.email:
                pendencias.append("Email para cadastro")
        elif corretor.status == "aguardando_assinatura":
            pendencias.append("Assinatura do contrato")
        
        return CadastroStatusResponse(
            cadastro_id=cadastro_id,
            status=corretor.status,
            progresso=min(progresso, 100),
            documentos_recebidos=docs_recebidos,
            dados_extraidos=dados,
            pendencias=pendencias,
            contrato_gerado=corretor.contrato_gerado,
            contrato_url=corretor.contrato_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assinatura-contrato/{cadastro_id}")
async def registrar_assinatura_contrato(
    cadastro_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Webhook para receber confirmação de assinatura do contrato
    """
    try:
        corretor = db.query(Corretor).filter(
            Corretor.cadastro_id == cadastro_id
        ).first()
        
        if not corretor:
            raise HTTPException(status_code=404, detail="Cadastro não encontrado")
        
        corretor.contrato_assinado = True
        corretor.contrato_assinado_at = datetime.utcnow()
        corretor.status = "ativo"
        corretor.ativo_desde = datetime.utcnow()
        db.commit()
        
        # Envia mensagem de boas-vindas
        send_text_message(
            corretor.phone,
            f"""
🎉 *PARABÉNS! Seu cadastro está ATIVO!*

Bem-vindo à PRÁTICO Documentos, {corretor.nome}!

✅ Você agora pode indicar clientes e ganhar comissões de até 35%.

📱 *Como funciona:*
1. Indique clientes para escrituras digitais
2. Acompanhe pelo seu painel
3. Receba comissões automaticamente

🔗 Acesse seu painel: https://admin.praticodocumentos.com.br

🚀 Boa sorte e ótimas vendas!
            """.strip()
        )
        
        return {"success": True, "message": "Cadastro ativado com sucesso!"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
