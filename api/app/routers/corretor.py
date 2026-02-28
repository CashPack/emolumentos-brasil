"""
Módulo 0 - Cadastro de Corretores (Fluxo Final Guiado)
Fluxo: Doc1 (RG/CNH) → Doc2 (CRECI) → Escolha Endereço → Doc3/Endereço → Estado Civil → Processamento Lote
"""
import os
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
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

PROCESSING_DELAY = 30

# ==================== ENDPOINT: INICIAR ====================

@router.post("/iniciar")
async def iniciar_cadastro(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Inicia cadastro e solicita RG ou CNH"""
    try:
        data = await request.json()
        phone = data.get("phone", "")
        
        cadastro_id = str(uuid.uuid4())[:8]
        
        corretor = Corretor(
            cadastro_id=cadastro_id,
            phone=phone,
            status="aguardando_doc1",
            created_at=datetime.utcnow()
        )
        db.add(corretor)
        db.commit()
        
        mensagem = """
👋 Bem-vindo à PRÁTICO Documentos!

Vou te auxiliar no cadastro de corretor parceiro.

📎 *PASSO 1/5: Documento de Identidade*

Envie seu documento:
• RG (frente e verso), OU
• CNH (frente e verso)

💡 Formatos aceitos: foto (JPG/PNG) ou arquivo PDF

Envie uma foto/página por vez.
        """.strip()
        
        background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
        
        return {"success": True, "cadastro_id": cadastro_id, "status": "aguardando_doc1"}
        
    except Exception as e:
        print(f"[INICIAR] Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WEBHOOK: RECEBER DOCUMENTOS ====================

@router.post("/webhook/documento")
async def receber_documento_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Webhook para receber documentos via WhatsApp - gerencia fluxo passo a passo"""
    try:
        data = await request.json()
        event = data.get("event", "")
        message_data = data.get("data", {})
        
        if event != "messages.upsert":
            return {"success": True, "message": "Evento ignorado"}
        
        message = message_data.get("message", {})
        remote_jid = message.get("remoteJid", "")
        phone = remote_jid.split("@")[0]
        
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
                send_text_message, phone=phone,
                text="📋 Cadastro não encontrado. Inicie em: https://praticodocumentos.com.br/corretor"
            )
            return {"success": False, "message": "Cadastro não encontrado"}
        
        # Roteia conforme estado
        if corretor.status == "aguardando_doc1" and (has_image or has_document):
            return await processar_doc1(corretor, message, phone, background_tasks, db)
        elif corretor.status == "aguardando_doc2" and (has_image or has_document):
            return await processar_doc2(corretor, message, phone, background_tasks, db)
        elif corretor.status == "aguardando_escolha_endereco":
            return await processar_escolha_endereco(corretor, message, phone, is_text, background_tasks, db)
        elif corretor.status == "aguardando_doc3" and (has_image or has_document):
            return await processar_doc3(corretor, message, phone, background_tasks, db)
        elif corretor.status == "aguardando_endereco_digitado" and is_text:
            return await processar_endereco_digitado(corretor, message, phone, background_tasks, db)
        elif corretor.status == "aguardando_estado_civil" and is_text:
            return await processar_estado_civil(corretor, message, phone, background_tasks, db)
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
        media_url = message.get("imageMessage", {}).get("url") or message.get("documentMessage", {}).get("url")
        if not media_url:
            background_tasks.add_task(send_text_message, phone=phone, text="❌ Não consegui receber a imagem. Tente enviar novamente.")
            return {"success": False, "message": "URL não encontrada"}
        
        corretor.temp_doc1_url = media_url
        corretor.status = "aguardando_doc2"
        db.commit()
        
        mensagem = """
✅ Documento de identidade recebido!

📎 *PASSO 2/5: Carteira CRECI*

Envie foto da sua carteira do CRECI (frente e verso).

💡 Formatos aceitos: foto (JPG/PNG) ou arquivo PDF
        """.strip()
        
        background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
        return {"success": True, "status": "aguardando_doc2"}
        
    except Exception as e:
        print(f"[DOC1] Erro: {e}")
        return {"success": False, "error": str(e)}


async def processar_doc2(corretor, message, phone, background_tasks, db):
    """Processa segundo documento (CRECI)"""
    try:
        media_url = message.get("imageMessage", {}).get("url") or message.get("documentMessage", {}).get("url")
        if not media_url:
            background_tasks.add_task(send_text_message, phone=phone, text="❌ Não consegui receber a imagem.")
            return {"success": False, "message": "URL não encontrada"}
        
        corretor.temp_doc2_url = media_url
        corretor.status = "aguardando_escolha_endereco"
        db.commit()
        
        mensagem = """
✅ Carteira CRECI recebida!

📍 *PASSO 3/5: Endereço*

Como você prefere informar seu endereço?

1️⃣ *Digitar manualmente*
2️⃣ *Enviar foto do comprovante* (nossa IA extrai)

Responda com o número *1* ou *2*.
        """.strip()
        
        background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
        return {"success": True, "status": "aguardando_escolha_endereco"}
        
    except Exception as e:
        print(f"[DOC2] Erro: {e}")
        return {"success": False, "error": str(e)}


async def processar_escolha_endereco(corretor, message, phone, is_text, background_tasks, db):
    """Processa escolha do método de endereço"""
    try:
        text = ""
        if "conversation" in message:
            text = message["conversation"]
        elif "extendedTextMessage" in message:
            text = message["extendedTextMessage"].get("text", "")
        
        escolha = text.strip()
        
        if escolha == "1":
            # Opção 1: Digitar manualmente
            corretor.status = "aguardando_endereco_digitado"
            db.commit()
            
            mensagem = """
✏️ *Digite seu endereço completo:*

Formato: Rua/Av, número, complemento, bairro, cidade - UF, CEP

_Exemplo: Av. Paulista, 1000, apto 42, Jardins, São Paulo - SP, 01310-100_
            """.strip()
            
            background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
            return {"success": True, "status": "aguardando_endereco_digitado"}
            
        elif escolha == "2":
            # Opção 2: Enviar foto do comprovante
            corretor.status = "aguardando_doc3"
            db.commit()
            
            mensagem = """
📎 *Envie foto do comprovante de residência*

Pode ser conta de luz, água, telefone, etc. Em seu nome ou de parente próximo.
            """.strip()
            
            background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
            return {"success": True, "status": "aguardando_doc3"}
        else:
            # Resposta inválida
            background_tasks.add_task(
                send_text_message,
                phone=phone,
                text="❓ Não entendi. Responda com *1* (digitar) ou *2* (enviar foto)."
            )
            return {"success": False, "erro": "Escolha inválida"}
            
    except Exception as e:
        print(f"[ESCOLHA] Erro: {e}")
        return {"success": False, "error": str(e)}


async def processar_endereco_digitado(corretor, message, phone, background_tasks, db):
    """Processa endereço digitado manualmente"""
    try:
        text = ""
        if "conversation" in message:
            text = message["conversation"]
        elif "extendedTextMessage" in message:
            text = message["extendedTextMessage"].get("text", "")
        
        endereco = text.strip()
        
        # Salva endereço
        corretor.endereco_completo = endereco
        corretor.endereco_fonte = "digitado"
        corretor.status = "aguardando_estado_civil"
        db.commit()
        
        mensagem = """
✅ Endereço registrado!

💍 *PASSO 4/5: Estado Civil*

Informe seu estado civil:

1️⃣ Solteiro(a)
2️⃣ Casado(a)
3️⃣ Divorciado(a)
4️⃣ Viúvo(a)

Responda com o número correspondente.
        """.strip()
        
        background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
        return {"success": True, "status": "aguardando_estado_civil"}
        
    except Exception as e:
        print(f"[ENDERECO] Erro: {e}")
        return {"success": False, "error": str(e)}


async def processar_estado_civil(corretor, message, phone, background_tasks, db):
    """Processa estado civil"""
    try:
        text = ""
        if "conversation" in message:
            text = message["conversation"]
        elif "extendedTextMessage" in message:
            text = message["extendedTextMessage"].get("text", "")
        
        escolha = text.strip()
        
        mapa = {
            "1": "solteiro",
            "2": "casado",
            "3": "divorciado",
            "4": "viuvo"
        }
        
        if escolha not in mapa:
            background_tasks.add_task(
                send_text_message,
                phone=phone,
                text="❓ Responda com 1, 2, 3 ou 4."
            )
            return {"success": False, "erro": "Escolha inválida"}
        
        corretor.estado_civil = mapa[escolha]
        corretor.status = "processando"
        db.commit()
        
        mensagem = f"""
✅ Estado civil: {mapa[escolha].replace('_', ' ').title()}

⏱️ *Processando seus documentos...* (aprox. {PROCESSING_DELAY}s)

Estou extraindo todas as informações automaticamente.
        """.strip()
        
        background_tasks.add_task(send_text_message, phone=phone, text=mensagem)
        
        # Agenda processamento
        background_tasks.add_task(
            processar_todos_documentos,
            corretor_id=corretor.id,
            phone=phone
        )
        
        return {"success": True, "status": "processando"}
        
    except Exception as e:
        print(f"[ESTADO_CIVIL] Erro: {e}")
        return {"success": False, "error": str(e)}


async def processar_correcao(corretor, message, phone, background_tasks, db):
    """Processa correção de dados enviada pelo usuário"""
    try:
        text = ""
        if "conversation" in message:
            text = message["conversation"]
        elif "extendedTextMessage" in message:
            text = message["extendedTextMessage"].get("text", "")
        
        text_upper = text.strip().upper()
        
        # Verifica se é confirmação final
        if text_upper == "CONFIRMAR" or "CONFIRMAR" in text_upper:
            # Verifica se ainda há pendências
            pendencias = json.loads(corretor.pendencias or "[]")
            if pendencias:
                background_tasks.add_task(
                    send_text_message,
                    phone=phone,
                    text=f"⚠️ Ainda há pendências: {', '.join(pendencias)}. Corrija antes de confirmar."
                )
                return {"success": False, "acao": "pendencias_restantes"}
            
            background_tasks.add_task(
                send_text_message,
                phone=phone,
                text="📧 Perfeito! Agora informe seu email para finalizar o cadastro:"
            )
            corretor.status = "aguardando_email"
            db.commit()
            return {"success": True, "acao": "solicitar_email"}
        
        # Verifica se é email
        if "@" in text and "." in text and " " not in text.strip():
            return await finalizar_cadastro(corretor, text.strip(), phone, background_tasks, db)
        
        # Processa correção no formato "CAMPO: valor"
        if ":" in text:
            partes = text.split(":", 1)
            campo = partes[0].strip().upper()
            valor = partes[1].strip()
            
            # Recupera dados atuais
            dados = json.loads(corretor.dados_extraidos or "{}")
            pendencias = json.loads(corretor.pendencias or "[]")
            
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
                
                # Remove da lista de pendências se existir
                if campo_padrao in pendencias:
                    pendencias.remove(campo_padrao)
                
                corretor.dados_extraidos = json.dumps(dados)
                corretor.pendencias = json.dumps(pendencias)
                db.commit()
                
                background_tasks.add_task(
                    send_text_message,
                    phone=phone,
                    text=f"✅ *{campo}* atualizado!\n\nContinue corrigindo ou digite CONFIRMAR quando estiver tudo certo."
                )
                
                return {"success": True, "campo_atualizado": campo_padrao}
            else:
                background_tasks.add_task(
                    send_text_message,
                    phone=phone,
                    text=f"❌ Campo *{campo}* não reconhecido.\nUse: NOME, CPF, DATA_NASCIMENTO, CRECI, ENDERECO"
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


async def finalizar_cadastro(corretor, email, phone, background_tasks, db):
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
                f"❌ Dados obrigatórios faltando: {', '.join(faltando)}. Corrija antes de finalizar."
            )
            corretor.status = "aguardando_correcoes"
            db.commit()
            return {"success": False, "faltando": faltando}
        
        # Atualiza cadastro
        corretor.nome = dados["nome"]
        corretor.cpf = dados["cpf"]
        corretor.data_nascimento = dados.get("data_nascimento")
        corretor.creci_numero = dados["creci_numero"]
        corretor.creci_uf = dados.get("creci_uf", "SP")
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
                f"❌ *CRECI não validado:* {creci_valid.get('mensagem', 'Registro não encontrado')}\nVerifique e corrija."
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
            corretor.contrato_url = contrato.get("assinatura_url", "https://praticodocumentos.com.br/contratos")
            corretor.status = "aguardando_aceite"
            db.commit()
            
            # Mensagem de sucesso com contrato
            mensagem = f"""
🎉 *CADASTRO QUASE COMPLETO!*

✅ Dados validados
✅ CRECI confirmado
✅ Conta Asaas criada  
✅ Contrato gerado

📄 *CONTRATO DE PARCERIA*

Leia atentamente o contrato em: {corretor.contrato_url}

💡 *Resumo:*
• Comissão de até 35% sobre economia gerada
• Pagamento via Asaas (automático)
• Vigência indeterminada
• Rescisão com 30 dias de aviso

✅ *Para aceitar, digite:* **ACEITO**

Após o aceite, seu cadastro estará *ATIVO*!
            """.strip()
            
            send_text_message(phone, mensagem)
            return {"success": True, "status": "aguardando_aceite"}
        else:
            corretor.status = "erro_asaas"
            db.commit()
            send_text_message(phone, f"❌ Erro ao criar conta: {asaas.get('error', 'Tente novamente')}")
            return {"success": False, "erro": "Falha Asaas"}
            
    except Exception as e:
        print(f"[FINALIZAR] Erro: {e}")
        send_text_message(phone, "❌ Erro ao finalizar. Contate o suporte.")
        return {"success": False, "error": str(e)}


# ==================== PROCESSAMENTO EM LOTE ====================

async def processar_todos_documentos(corretor_id: int, phone: str):
    """Processa todos os documentos em lote após timeout - suporta múltiplos formatos"""
    await asyncio.sleep(PROCESSING_DELAY)
    
    from app.db.session import SessionLocal
    db = SessionLocal()
    
    try:
        corretor = db.query(Corretor).filter(Corretor.id == corretor_id).first()
        if not corretor:
            return
        
        resultados = {"nome": None, "cpf": None, "data_nascimento": None, 
                     "creci_numero": None, "creci_uf": None, "endereco": None}
        
        # Processa doc1 (RG/CNH)
        if corretor.temp_doc1_url:
            try:
                import requests
                resp = requests.get(corretor.temp_doc1_url, timeout=30)
                if resp.status_code == 200:
                    content_type = resp.headers.get('content-type', '')
                    file_ext = corretor.temp_doc1_url.split('.')[-1].lower() if '.' in corretor.temp_doc1_url else ''
                    
                    # Identifica tipo de arquivo
                    is_pdf = 'pdf' in content_type or file_ext == 'pdf'
                    is_image = any(img in content_type for img in ['image/jpeg', 'image/png', 'image/jpg'])
                    
                    print(f"[PROCESS] Doc1 - Tipo: {'PDF' if is_pdf else 'Imagem' if is_image else 'Desconhecido'}")
                    
                    # Processa conforme tipo
                    if is_pdf:
                        # Para PDFs, tenta extrair texto direto primeiro, se falhar usa OCR
                        ocr = extract_document_data(resp.content, force_ocr=False)
                    else:
                        # Para imagens, sempre usa OCR
                        ocr = extract_document_data(resp.content, force_ocr=True)
                    
                    data = ocr.get("data", {})
                    resultados["nome"] = data.get("nome")
                    resultados["cpf"] = data.get("cpf")
                    resultados["data_nascimento"] = data.get("data_nascimento")
            except Exception as e:
                print(f"[PROCESS] Erro doc1: {e}")
        
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
                print(f"[PROCESS] Erro doc2: {e}")
        
        # Processa doc3 (Comprovante) se endereço não foi digitado
        if corretor.endereco_fonte == "ocr" and corretor.temp_doc3_url:
            try:
                import requests
                resp = requests.get(corretor.temp_doc3_url, timeout=30)
                if resp.status_code == 200:
                    ocr = extract_document_data(resp.content)
                    data = ocr.get("data", {})
                    resultados["endereco"] = data.get("endereco")
            except Exception as e:
                print(f"[PROCESS] Erro doc3: {e}")
        elif corretor.endereco_fonte == "digitado":
            resultados["endereco"] = corretor.endereco
        
        # Salva resultados
        corretor.dados_extraidos = json.dumps(resultados)
        
        # Identifica pendências
        pendencias = []
        if not resultados["nome"]:
            pendencias.append("nome")
        if not resultados["cpf"]:
            pendencias.append("cpf")
        if not resultados["creci_numero"]:
            pendencias.append("creci_numero")
        if not resultados["endereco"]:
            pendencias.append("endereco")
        
        corretor.pendencias = json.dumps(pendencias)
        
        if pendencias:
            corretor.status = "aguardando_correcoes"
        else:
            corretor.status = "aguardando_email"
        
        db.commit()
        
        # Envia resposta
        mensagem = montar_resposta_processamento(resultados, pendencias)
        send_text_message(phone, mensagem)
        
    except Exception as e:
        print(f"[PROCESS] Erro: {e}")
        send_text_message(phone, "❌ Erro ao processar. Tente novamente ou contate o suporte.")
    finally:
        db.close()


def montar_resposta_processamento(dados: dict, pendencias: list) -> str:
    """Monta mensagem com dados extraídos e pendências"""
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
    
    if pendencias:
        msg += "\n⚠️ *Precisamos corrigir:*\n"
        for p in pendencias:
            msg += f"• {p.replace('_', ' ').title()}\n"
        msg += "\n✏️ *Para corrigir, digite:*\nCAMPO: valor\n_Ex: NOME: João Silva_\n\n✅ Quando estiver tudo certo, digite: *CONFIRMAR*"
    else:
        msg += "\n🎉 *Todos os dados identificados!*\n\n✅ Digite *CONFIRMAR* e informe seu email para finalizar."
    
    return msg


# ==================== STATUS E CONSULTAS ====================

@router.get("/status/{cadastro_id}")
async def consultar_status(cadastro_id: str, db: Session = Depends(get_db)):
    """Consulta status completo do cadastro"""
    try:
        corretor = db.query(Corretor).filter(Corretor.cadastro_id == cadastro_id).first()
        if not corretor:
            raise HTTPException(status_code=404, detail="Cadastro não encontrado")
        
        dados = json.loads(corretor.dados_extraidos or "{}")
        pendencias = json.loads(corretor.pendencias or "[]")
        
        progresso = {
            "aguardando_doc1": 10, "aguardando_doc2": 25, "aguardando_escolha_endereco": 35,
            "aguardando_doc3": 40, "aguardando_endereco_digitado": 40, "aguardando_estado_civil": 45,
            "processando": 50, "aguardando_correcoes": 60, "aguardando_email": 70,
            "criando_asaas": 80, "gerando_contrato": 85, "aguardando_aceite": 90, "ativo": 100
        }.get(corretor.status, 0)
        
        return {
            "cadastro_id": cadastro_id,
            "status": corretor.status,
            "progresso": progresso,
            "dados": dados,
            "pendencias": pendencias,
            "contrato_url": corretor.contrato_url,
            "cadastro_ativo": corretor.status == "ativo"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/aceite/{cadastro_id}")
async def registrar_aceite(cadastro_id: str, request: Request, db: Session = Depends(get_db)):
    """Webhook para registrar aceite do contrato"""
    try:
        data = await request.json()
        corretor = db.query(Corretor).filter(Corretor.cadastro_id == cadastro_id).first()
        
        if not corretor:
            raise HTTPException(status_code=404, detail="Cadastro não encontrado")
        
        corretor.contrato_aceito = True
        corretor.contrato_aceito_em = datetime.utcnow()
        corretor.contrato_aceito_ip = data.get("ip", request.client.host if request.client else None)
        corretor.status = "ativo"
        corretor.ativo_desde = datetime.utcnow()
        db.commit()
        
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
