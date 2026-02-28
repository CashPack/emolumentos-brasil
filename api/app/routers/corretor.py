"""
Módulo 0 - Cadastro de Corretores (Fluxo Final Guiado)
Endpoint para onboarding de corretores parceiros via WhatsApp
Fluxo: Doc1 → Doc2 → Doc3 → Endereço → Processamento em Lote
"""
import os
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import (
    APIRouter, Request, Depends, HTTPException, 
    BackgroundTasks
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.corretor import Corretor
from app.services.evolution_service import send_text_message
from app.services.ocr_service import extract_document_data
from app.services.creci_validator import validate_creci
from app.services.asaas_service import create_asaas_account
from app.services.contract_generator import generate_partnership_contract, CorretorData

router = APIRouter(prefix="/api/corretor", tags=["Module 0 - Cadastro Corretor"])

# ==================== CONFIGURAÇÕES ====================
PROCESSING_DELAY = 30  # segundos para processar em lote

# ==================== MODELOS ====================

class StartCadastroRequest(BaseModel):
    phone: str


class ConfirmarDadosRequest(BaseModel):
    cadastro_id: str
    campo: str  # nome, cpf, data_nascimento, creci_numero, creci_uf, endereco
    valor: str


class FinalizarCadastroRequest(BaseModel):
    cadastro_id: str
    email: str
    confirmacao_dados: bool  # Confirma que todos os dados estão corretos


# ==================== ENDPOINT: INICIAR CADASTRO ====================

@router.post("/iniciar")
async def iniciar_cadastro(
    request: StartCadastroRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Inicia cadastro e solicita primeiro documento (RG ou CNH)"""
    try:
        cadastro_id = str(uuid.uuid4())[:8]
        
        corretor = Corretor(
            cadastro_id=cadastro_id,
            phone=request.phone,
            status="aguardando_doc1",  # Estado inicial
            created_at=datetime.utcnow()
        )
        db.add(corretor)
        db.commit()
        
        mensagem = """
👋 Bem-vindo à PRÁTICO Documentos!

Vou te auxiliar no cadastro de corretor parceiro. Serão apenas alguns passos rápidos!

📎 *PASSO 1/4: Documento de Identidade*

Envie foto do seu documento:
• RG (frente e verso), OU
• CNH (frente e verso)

💡 Envie as fotos uma de cada vez, em mensagens separadas.
        """.strip()
        
        background_tasks.add_task(send_text_message, phone=request.phone, text=mensagem)
        
        return {
            "success": True,
            "cadastro_id": cadastro_id,
            "status": "aguardando_doc1",
            "message": "Cadastro iniciado. Aguardando RG ou CNH."
        }
        
    except Exception as e:
        print(f"[INICIAR] Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WEBHOOK: RECEBER DOCUMENTOS ====================

@router.post("/webhook/documento")
async def receber_documento_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Webhook para receber documentos via WhatsApp.
    Gerencia fluxo: doc1 → doc2 → doc3 → endereço → processamento
    """
    try:
        data = await request.json()
        event = data.get("event", "")
        message_data = data.get("data", {})
        
        if event != "messages.upsert":
            return {"success": True, "message": "Evento ignorado"}
        
        message = message_data.get("message", {})
        remote_jid = message.get("remoteJid", "")
        phone = remote_jid.split("@")[0]
        
        # Verifica se é imagem
        has_image = "imageMessage" in message
        has_document = "documentMessage" in message
        is_text = "conversation" in message or "extendedTextMessage" in message
        
        # Busca cadastro ativo
        corretor = db.query(Corretor).filter(
            Corretor.phone == phone,
            Corretor.status.like("aguardando_%")
        ).order_by(Corretor.created_at.desc()).first()
        
        if not corretor:
            background_tasks.add_task(
                send_text_message, 
                phone=phone, 
                text="📋 Cadastro não encontrado. Inicie em: https://praticodocumentos.com.br/corretor"
            )
            return {"success": False, "message": "Cadastro não encontrado"}
        
        # Processa conforme estado atual
        if corretor.status == "aguardando_doc1" and (has_image or has_document):
            return await processar_doc1(corretor, message, phone, background_tasks, db)
            
        elif corretor.status == "aguardando_doc2" and (has_image or has_document):
            return await processar_doc2(corretor, message, phone, background_tasks, db)
            
        elif corretor.status == "aguardando_doc3" and (has_image or has_document):
            return await processar_doc3(corretor, message, phone, background_tasks, db)
            
        elif corretor.status == "aguardando_endereco":
            return await processar_endereco(corretor, message, phone, is_text, background_tasks, db)
            
        elif corretor.status == "aguardando_correcoes" and is_text:
            return await processar_correcao(corretor, message, phone, background_tasks, db)
        
        return {"success": True, "message": "Mensagem recebida fora do fluxo esperado"}
        
    except Exception as e:
        print(f"[WEBHOOK] Erro: {e}")
        return {"success": False, "error": str(e)}


# ==================== PROCESSAMENTO POR ETAPA ====================

async def processar_doc1(corretor, message, phone, background_tasks, db):
    """Processa primeiro documento (RG ou CNH)"""
    try:
        # Extrai URL
        media_url = message.get("imageMessage", {}).get("url") or message.get("documentMessage", {}).get("url")
        if not media_url:
            background_tasks.add_task(
                send_text_message, phone=phone, text="❌ Não consegui receber a imagem. Tente enviar novamente."
            )
            return {"success": False, "message": "URL não encontrada"}
        
        # Salva e marca como recebido
        corretor.temp_doc1_url = media_url
        corretor.status = "aguardando_doc2"
        db.commit()
        
        # Confirma recebimento e solicita próximo
        mensagem = """
✅ Documento de identidade recebido!

📎 *PASSO 2/4: Carteira CRECI*

Envie foto da sua carteira do CRECI (frente e verso).
        """.strip()
        
        background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
        
        return {"success": True, "status": "aguardando_doc2", "message": "Doc1 recebido, aguardando CRECI"}
        
    except Exception as e:
        print(f"[DOC1] Erro: {e}")
        background_tasks.add_task(send_text_message, phone=phone, text="❌ Erro ao processar. Tente novamente.")
        return {"success": False, "error": str(e)}


async def processar_doc2(corretor, message, phone, background_tasks, db):
    """Processa segundo documento (CRECI)"""
    try:
        media_url = message.get("imageMessage", {}).get("url") or message.get("documentMessage", {}).get("url")
        if not media_url:
            background_tasks.add_task(send_text_message, phone=phone, text="❌ Não consegui receber a imagem.")
            return {"success": False, "message": "URL não encontrada"}
        
        corretor.temp_doc2_url = media_url
        corretor.status = "aguardando_doc3"
        db.commit()
        
        mensagem = """
✅ Carteira CRECI recebida!

📎 *PASSO 3/4: Comprovante de Residência*

Envie foto de um comprovante de residência em seu nome.
        """.strip()
        
        background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
        
        return {"success": True, "status": "aguardando_doc3", "message": "Doc2 recebido, aguardando comprovante"}
        
    except Exception as e:
        print(f"[DOC2] Erro: {e}")
        return {"success": False, "error": str(e)}


async def processar_doc3(corretor, message, phone, background_tasks, db):
    """Processa terceiro documento (Comprovante)"""
    try:
        media_url = message.get("imageMessage", {}).get("url") or message.get("documentMessage", {}).get("url")
        if not media_url:
            background_tasks.add_task(send_text_message, phone=phone, text="❌ Não consegui receber a imagem.")
            return {"success": False, "message": "URL não encontrada"}
        
        corretor.temp_doc3_url = media_url
        corretor.status = "aguardando_endereco"
        corretor.all_docs_received_at = datetime.utcnow()
        db.commit()
        
        mensagem = """
✅ Comprovante de residência recebido!

📍 *PASSO 4/4: Endereço*

Qual seu endereço completo?

Digite manualmente ou digite *EXTRAIR* para tentarmos extrair do comprovante (pode não ser preciso).
        """.strip()
        
        background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
        
        return {"success": True, "status": "aguardando_endereco", "message": "Doc3 recebido, aguardando endereço"}
        
    except Exception as e:
        print(f"[DOC3] Erro: {e}")
        return {"success": False, "error": str(e)}


async def processar_endereco(corretor, message, phone, is_text, background_tasks, db):
    """Processa entrada do endereço"""
    try:
        # Extrai texto da mensagem
        text = ""
        if "conversation" in message:
            text = message["conversation"]
        elif "extendedTextMessage" in message:
            text = message["extendedTextMessage"].get("text", "")
        
        text_upper = text.strip().upper()
        
        if text_upper == "EXTRAIR":
            # Marca para extrair do comprovante via OCR
            corretor.endereco_fonte = "ocr"
            corretor.endereco = None
        else:
            # Usa texto digitado
            corretor.endereco_fonte = "digitado"
            corretor.endereco = text.strip()
        
        corretor.status = "processando"
        db.commit()
        
        mensagem = f"""
✅ Todos os dados recebidos!

⏱️ Processando seus documentos... (aprox. {PROCESSING_DELAY}s)

Aguarde enquanto extraio as informações automaticamente.
        """.strip()
        
        background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
        
        # Agenda processamento em lote
        background_tasks.add_task(
            processar_todos_documentos,
            corretor_id=corretor.id,
            phone=phone
        )
        
        return {"success": True, "status": "processando", "message": "Iniciando processamento em lote"}
        
    except Exception as e:
        print(f"[ENDERECO] Erro: {e}")
        return {"success": False, "error": str(e)}


# ==================== PROCESSAMENTO EM LOTE ====================

async def processar_todos_documentos(corretor_id: int, phone: str):
    """Processa todos os documentos em lote após timeout"""
    # Aguarda processamento
    await asyncio.sleep(PROCESSING_DELAY)
    
    from app.db.session import SessionLocal
    db = SessionLocal()
    
    try:
        corretor = db.query(Corretor).filter(Corretor.id == corretor_id).first()
        if not corretor:
            return
        
        resultados = {
            "nome": None,
            "cpf": None,
            "data_nascimento": None,
            "creci_numero": None,
            "creci_uf": None,
            "endereco": corretor.endereco  # Já temos se foi digitado
        }
        
        # Processa doc1 (RG/CNH)
        if corretor.temp_doc1_url:
            try:
                import requests
                resp = requests.get(corretor.temp_doc1_url, timeout=30)
                if resp.status_code == 200:
                    ocr = extract_document_data(resp.content)
                    data = ocr.get("data", {})
                    resultados["nome"] = data.get("nome")
                    resultados["cpf"] = data.get("cpf")
                    resultados["data_nascimento"] = data.get("data_nascimento")
            except Exception as e:
                print(f"[PROCESS] Erro OCR doc1: {e}")
        
        # Processa doc2 (CRECI)
        if corretor.temp_doc2_url:
            try:
                import requests
                resp = requests.get(corretor.temp_doc2_url, timeout=30)
                if resp.status_code == 200:
                    ocr = extract_document_data(resp.content)
                    data = ocr.get("data", {})
                    resultados["creci_numero"] = data.get("creci_numero")
                    resultados["creci_uf"] = data.get("creci_uf")
            except Exception as e:
                print(f"[PROCESS] Erro OCR doc2: {e}")
        
        # Processa doc3 (Comprovante) - só se endereço não foi digitado
        if corretor.endereco_fonte == "ocr" and corretor.temp_doc3_url:
            try:
                import requests
                resp = requests.get(corretor.temp_doc3_url, timeout=30)
                if resp.status_code == 200:
                    ocr = extract_document_data(resp.content)
                    data = ocr.get("data", {})
                    resultados["endereco"] = data.get("endereco")
            except Exception as e:
                print(f"[PROCESS] Erro OCR doc3: {e}")
        
        # Salva resultados
        corretor.dados_extraidos = json.dumps(resultados)
        corretor.status = "aguardando_correcoes"
        db.commit()
        
        # Monta resposta com dados e pendências
        mensagem = montar_resposta_processamento(resultados)
        send_text_message(phone, mensagem)
        
    except Exception as e:
        print(f"[PROCESS] Erro: {e}")
        send_text_message(phone, "❌ Erro ao processar documentos. Por favor, tente novamente ou contate o suporte.")
    finally:
        db.close()


def montar_resposta_processamento(dados: Dict) -> str:
    """Monta mensagem com dados extraídos e instruções para correção"""
    msg = "✅ *Processamento concluído!*\n\n"
    msg += "📋 *Dados identificados:*\n\n"
    
    if dados.get("nome"):
        msg += f"👤 Nome: *{dados['nome']}*\n"
    else:
        msg += "👤 Nome: ❌ Não identificado\n"
    
    if dados.get("cpf"):
        cpf = dados["cpf"]
        cpf_fmt = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        msg += f"🆔 CPF: *{cpf_fmt}*\n"
    else:
        msg += "🆔 CPF: ❌ Não identificado\n"
    
    if dados.get("data_nascimento"):
        msg += f"🎂 Nascimento: *{dados['data_nascimento']}*\n"
    
    if dados.get("creci_numero"):
        uf = dados.get("creci_uf", "UF")
        msg += f"🏷️ CRECI: *{dados['creci_numero']}/{uf}*\n"
    else:
        msg += "🏷️ CRECI: ❌ Não identificado\n"
    
    if dados.get("endereco"):
        end = dados["endereco"][:50] + "..." if len(dados["endereco"]) > 50 else dados["endereco"]
        msg += f"📍 Endereço: *{end}*\n"
    else:
        msg += "📍 Endereço: ❌ Não identificado\n"
    
    msg += "\n✏️ *Para corrigir ou completar dados:*\n"
    msg += "Digite: CAMPO: valor\n"
    msg += "_Exemplos:_\n"
    
    if not dados.get("nome"):
        msg += "• NOME: João Silva\n"
    if not dados.get("cpf"):
        msg += "• CPF: 12345678900\n"
    if not dados.get("creci_numero"):
        msg += "• CRECI: 12345/SP\n"
    if not dados.get("endereco"):
        msg += "• ENDERECO: Rua Exemplo, 123 - Centro\n"
    
    msg += "\n✅ *Quando todos os dados estiverem corretos, digite:* CONFIRMAR\n"
    msg += "_E informe seu email para finalizar o cadastro._"
    
    return msg


# ==================== CORREÇÃO DE DADOS ====================

async def processar_correcao(corretor, message, phone, background_tasks, db):
    """Processa correção de dados enviada pelo usuário"""
    try:
        # Extrai texto
        text = ""
        if "conversation" in message:
            text = message["conversation"]
        elif "extendedTextMessage" in message:
            text = message["extendedTextMessage"].get("text", "")
        
        text_upper = text.strip().upper()
        
        # Verifica se é confirmação final
        if text_upper == "CONFIRMAR" or "CONFIRMAR" in text_upper:
            background_tasks.add_task(
                send_text_message, 
                phone=phone, 
                text="📧 Perfeito! Agora informe seu email para criarmos sua conta:"
            )
            return {"success": True, "acao": "solicitar_email"}
        
        # Verifica se é email (contém @)
        if "@" in text and "." in text:
            return await finalizar_cadastro_completo(corretor, text.strip(), phone, background_tasks, db)
        
        # Processa correção no formato "CAMPO: valor"
        if ":" in text:
            partes = text.split(":", 1)
            campo = partes[0].strip().upper()
            valor = partes[1].strip()
            
            # Recupera dados atuais
            dados = json.loads(corretor.dados_extraidos or "{}")
            
            # Mapeia campos
            mapeamento = {
                "NOME": "nome",
                "CPF": "cpf",
                "DATA_NASCIMENTO": "data_nascimento",
                "NASCIMENTO": "data_nascimento",
                "CRECI": "creci_numero",
                "ENDERECO": "endereco",
                "ENDEREÇO": "endereco"
            }
            
            campo_padrao = mapeamento.get(campo)
            if campo_padrao:
                # Se for CRECI, separa número e UF
                if campo_padrao == "creci_numero" and "/" in valor:
                    partes_creci = valor.split("/")
                    dados["creci_numero"] = partes_creci[0].strip()
                    dados["creci_uf"] = partes_creci[1].strip() if len(partes_creci) > 1 else "SP"
                else:
                    dados[campo_padrao] = valor
                
                corretor.dados_extraidos = json.dumps(dados)
                db.commit()
                
                background_tasks.add_task(
                    send_text_message,
                    phone=phone,
                    text=f"✅ *{campo}* atualizado para: {valor}\n\nContinue corrigindo ou digite CONFIRMAR quando estiver tudo certo."
                )
                
                return {"success": True, "campo_atualizado": campo_padrao}
            else:
                background_tasks.add_task(
                    send_text_message,
                    phone=phone,
                    text=f"❌ Campo *{campo}* não reconhecido.\n\nCampos válidos: NOME, CPF, DATA_NASCIMENTO, CRECI, ENDERECO"
                )
                return {"success": False, "erro": "Campo não reconhecido"}
        else:
            background_tasks.add_task(
                send_text_message,
                phone=phone,
                text="❓ Não entendi. Use o formato: CAMPO: valor\nOu digite CONFIRMAR se estiver tudo certo."
            )
            return {"success": False, "erro": "Formato inválido"}
            
    except Exception as e:
        print(f"[CORRECAO] Erro: {e}")
        return {"success": False, "error": str(e)}


# ==================== FINALIZAÇÃO ====================

async def finalizar_cadastro_completo(corretor, email, phone, background_tasks, db):
    """Finaliza cadastro: valida CRECI, cria Asaas, gera contrato"""
    try:
        dados = json.loads(corretor.dados_extraidos or "{}")
        
        # Verifica dados mínimos
        faltando = []
        if not dados.get("nome"):
            faltando.append("NOME")
        if not dados.get("cpf"):
            faltando.append("CPF")
        if not dados.get("creci_numero"):
            faltando.append("CRECI")
        
        if faltando:
            send_text_message(
                phone,
                f"❌ Ainda faltam dados obrigatórios: {', '.join(faltando)}\n\nPor favor, complete antes de confirmar."
            )
            return {"success": False, "faltando": faltando}
        
        # Atualiza cadastro
        corretor.nome = dados["nome"]
        corretor.cpf = dados["cpf"]
        corretor.data_nascimento = dados.get("data_nascimento")
        corretor.creci_numero = dados["creci_numero"]
        corretor.creci_uf = dados.get("creci_uf", "SP")
        corretor.endereco = dados.get("endereco")
        corretor.email = email
        corretor.status = "validando_creci"
        db.commit()
        
        # Valida CRECI
        creci_valid = await validate_creci(corretor.creci_numero, corretor.creci_uf)
        
        if not creci_valid.get("valido", False):
            corretor.status = "creci_invalido"
            db.commit()
            send_text_message(
                phone,
                f"❌ *CRECI não validado:* {creci_valid.get('mensagem', 'Registro não encontrado')}\n\nVerifique o número e UF, ou contate o suporte."
            )
            return {"success": False, "erro": "CRECI inválido"}
        
        corretor.creci_validado = True
        corretor.status = "criando_asaas"
        db.commit()
        
        # Cria conta Asaas
        asaas = await create_asaas_account(
            nome=corretor.nome,
            cpf=corretor.cpf,
            email=corretor.email,
            phone=corretor.phone,
            external_reference=corretor.cadastro_id
        )
        
        if asaas.get("success"):
            corretor.asaas_customer_id = asaas.get("customer_id")
            corretor.asaas_wallet_id = asaas.get("wallet_id")
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
            corretor.contrato_url = contrato.get("assinatura_url", "https://praticodocumentos.com.br/contratos/pendentes")
            corretor.status = "aguardando_assinatura"
            db.commit()
            
            # Mensagem de sucesso
            mensagem = f"""
🎉 *CADASTRO QUASE COMPLETO!*

✅ Dados validados
✅ CRECI confirmado
✅ Conta Asaas criada  
✅ Contrato gerado

📄 *Próximo passo:* Assine o contrato digital
Link: {corretor.contrato_url}

Após assinar, seu cadastro estará *ATIVO* e você poderá começar a indicar clientes!

💰 Comissões de até 35% sobre a economia gerada.
            """.strip()
            
            send_text_message(phone, mensagem)
            
            return {"success": True, "status": "aguardando_assinatura"}
        else:
            corretor.status = "erro_asaas"
            db.commit()
            send_text_message(phone, f"❌ Erro ao criar conta: {asaas.get('error', 'Tente novamente')}")
            return {"success": False, "erro": "Falha Asaas"}
            
    except Exception as e:
        print(f"[FINALIZAR] Erro: {e}")
        send_text_message(phone, "❌ Erro ao finalizar cadastro. Entre em contato com o suporte.")
        return {"success": False, "error": str(e)}


# ==================== STATUS E CONSULTAS ====================

@router.get("/status/{cadastro_id}")
async def consultar_status(cadastro_id: str, db: Session = Depends(get_db)):
    """Consulta status completo do cadastro"""
    try:
        corretor = db.query(Corretor).filter(Corretor.cadastro_id == cadastro_id).first()
        if not corretor:
            raise HTTPException(status_code=404, detail="Cadastro não encontrado")
        
        dados = json.loads(corretor.dados_extraidos or "{}")
        
        progresso = {
            "aguardando_doc1": 10,
            "aguardando_doc2": 25,
            "aguardando_doc3": 40,
            "aguardando_endereco": 50,
            "processando": 60,
            "aguardando_correcoes": 70,
            "validando_creci": 80,
            "criando_asaas": 85,
            "gerando_contrato": 90,
            "aguardando_assinatura": 95,
            "ativo": 100
        }.get(corretor.status, 0)
        
        return {
            "cadastro_id": cadastro_id,
            "status": corretor.status,
            "progresso": progresso,
            "dados": dados,
            "contrato_url": corretor.contrato_url,
            "cadastro_ativo": corretor.status == "ativo"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/assinatura/{cadastro_id}")
async def registrar_assinatura(
    cadastro_id: str,
    db: Session = Depends(get_db)
):
    """Webhook para confirmar assinatura do contrato"""
    try:
        corretor = db.query(Corretor).filter(Corretor.cadastro_id == cadastro_id).first()
        if not corretor:
            raise HTTPException(status_code=404, detail="Cadastro não encontrado")
        
        corretor.contrato_assinado = True
        corretor.contrato_assinado_at = datetime.utcnow()
        corretor.status = "ativo"
        corretor.ativo_desde = datetime.utcnow()
        db.commit()
        
        # Mensagem de boas-vindas
        send_text_message(
            corretor.phone,
            f"""
🎉 *PARABÉNS, {corretor.nome}!*

✅ Seu cadastro está *ATIVO*!

Você agora é um corretor parceiro PRÁTICO Documentos.

💰 *Como ganhar comissões:*
1. Indique clientes para escrituras digitais
2. Eles economizam até 70% vs cartório local
3. Você ganha até 35% da economia!

🔗 Seu painel: https://admin.praticodocumentos.com.br

🚀 Comece a indicar agora mesmo!
            """.strip()
        )
        
        return {"success": True, "message": "Cadastro ativado com sucesso!"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
