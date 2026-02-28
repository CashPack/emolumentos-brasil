"""
Serviço de extração de dados de documentos via Google Document AI (OCR)
"""
import os
import json
import requests
from typing import Dict, Any, Optional

# TODO: Configurar Google Document AI
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
# DOCUMENT_AI_ENDPOINT = os.getenv("DOCUMENT_AI_ENDPOINT", "")


def extract_document_data(file_bytes: bytes, force_ocr: bool = False, file_type: str = "auto") -> Dict[str, Any]:
    """
    Extrai dados de documentos usando OCR (Google Document AI ou similar)
    Suporta: JPG, PNG, PDF (nativo e escaneado)
    
    Args:
        file_bytes: Bytes do arquivo
        force_ocr: Se True, sempre usa OCR (ignora texto nativo de PDFs)
        file_type: Tipo de arquivo ('auto', 'image', 'pdf')
        
    Returns:
        Dict com dados extraídos
    """
    try:
        # Detecta tipo de arquivo se não informado
        if file_type == "auto":
            file_type = detect_file_type(file_bytes)
        
        print(f"[OCR] Tipo detectado: {file_type}, Force OCR: {force_ocr}")
        
        # Se for PDF e não forçar OCR, tenta extrair texto nativo primeiro
        if file_type == "pdf" and not force_ocr:
            texto_nativo = extract_text_from_pdf(file_bytes)
            if texto_nativo and len(texto_nativo.strip()) > 100:  # Se tem texto suficiente
                print(f"[OCR] PDF nativo detectado, {len(texto_nativo)} caracteres")
                return process_extracted_text(texto_nativo, file_type)
            else:
                print("[OCR] PDF escaneado ou sem texto, aplicando OCR")
        
        # Aplica OCR (para imagens e PDFs escaneados)
        # TODO: Implementar chamada real ao Google Document AI
        return {
            "document_type": "unknown",
            "data": {},
            "confidence": 0.0,
            "raw_text": "",
            "file_type": file_type,
            "message": "OCR via Google Document AI - implementação pendente"
        }
        
    except Exception as e:
        print(f"[OCR] Erro: {e}")
        return {
            "document_type": "unknown",
            "data": {},
            "confidence": 0.0,
            "raw_text": "",
            "error": str(e)
        }


def detect_file_type(file_bytes: bytes) -> str:
    """Detecta tipo de arquivo pelos magic numbers"""
    # PDF começa com %PDF
    if file_bytes[:4] == b'%PDF':
        return "pdf"
    # JPEG começa com FF D8
    elif file_bytes[:2] == b'\xff\xd8':
        return "image"
    # PNG começa com 89 50 4E 47
    elif file_bytes[:4] == b'\x89PNG':
        return "image"
    else:
        return "unknown"


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extrai texto nativo de PDF (sem OCR)"""
    try:
        import PyPDF2
        from io import BytesIO
        
        pdf_file = BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        
        return texto
    except Exception as e:
        print(f"[OCR] Erro ao extrair texto de PDF: {e}")
        return ""


def process_extracted_text(text: str, file_type: str) -> Dict[str, Any]:
    """Processa texto extraído e identifica documento"""
    import re
    
    text_upper = text.upper()
    
    # Detecta tipo de documento
    doc_type = "unknown"
    if any(kw in text_upper for kw in ['REGISTRO GERAL', 'CARTEIRA DE IDENTIDADE', 'IDENTIDADE']):
        doc_type = "rg"
    elif any(kw in text_upper for kw in ['CARTEIRA NACIONAL DE HABILITAÇÃO', 'CNH', 'HABILITAÇÃO']):
        doc_type = "cnh"
    elif any(kw in text_upper for kw in ['CRECI', 'CORRETOR', 'IMÓVEIS']):
        doc_type = "creci"
    elif any(kw in text_upper for kw in ['CONTA DE LUZ', 'CONTA DE ÁGUA', 'TELEFONE', 'ENERGIA']):
        doc_type = "comprovante"
    
    # Extrai dados comuns
    dados = {}
    
    # Nome (padrões comuns)
    nome_match = re.search(r'NOME[:\s]+([A-Z\s]+)(?=CPF|NASC|IDENT|$)', text_upper, re.MULTILINE)
    if nome_match:
        dados["nome"] = nome_match.group(1).strip().title()
    
    # CPF
    cpf_match = re.search(r'(\d{3}\.?\d{3}\.?\d{3}-?\d{2})', text)
    if cpf_match:
        dados["cpf"] = cpf_match.group(1).replace('.', '').replace('-', '')
    
    # Data de nascimento
    data_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
    if data_match:
        dados["data_nascimento"] = data_match.group(1)
    
    return {
        "document_type": doc_type,
        "data": dados,
        "confidence": 0.8,
        "raw_text": text[:1000],  # Primeiros 1000 caracteres
        "file_type": file_type,
        "extraction_method": "native_pdf"
    }


def detect_document_type(image_bytes: bytes) -> str:
    """
    Tenta identificar tipo de documento baseado em características
    """
    # Placeholder - implementação real vai analisar o OCR
    return "unknown"


def detect_document_type(image_bytes: bytes) -> str:
    """
    Tenta identificar tipo de documento baseado em características
    """
    # Placeholder - implementação real vai analisar o OCR
    return "unknown"


def extract_rg_data(text: str) -> Dict[str, Any]:
    """Extrai dados de RG a partir do texto OCR"""
    import re
    
    data = {}
    
    # Padrões comuns em RG
    cpf_match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', text)
    if cpf_match:
        data["cpf"] = cpf_match.group().replace(".", "").replace("-", "")
    
    # Nome (linha após "NOME" ou similar)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'NOME' in line.upper() and i + 1 < len(lines):
            data["nome"] = lines[i + 1].strip()
            break
    
    return data


def extract_cnh_data(text: str) -> Dict[str, Any]:
    """Extrai dados de CNH a partir do texto OCR"""
    import re
    
    data = {}
    
    # CPF
    cpf_match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', text)
    if cpf_match:
        data["cpf"] = cpf_match.group().replace(".", "").replace("-", "")
    
    # Nome
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if 'NOME' in line.upper() or 'NOME\/S' in line.upper():
            if i + 1 < len(lines):
                data["nome"] = lines[i + 1].strip()
            break
    
    return data


def extract_creci_data(text: str) -> Dict[str, Any]:
    """Extrai dados de carteira CRECI a partir do texto OCR"""
    import re
    
    data = {}
    
    # Número do CRECI (formato: 12345 ou CRECI 12345)
    creci_match = re.search(r'CRECI[\s:-]*(\d+)', text, re.IGNORECASE)
    if creci_match:
        data["creci_numero"] = creci_match.group(1)
    else:
        # Tenta pegar qualquer número de 4-6 dígitos
        num_match = re.search(r'\b\d{5,6}\b', text)
        if num_match:
            data["creci_numero"] = num_match.group()
    
    # UF (estado)
    ufs = ['AC', 'AL', 'AM', 'AP', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MG', 
           'MS', 'MT', 'PA', 'PB', 'PE', 'PI', 'PR', 'RJ', 'RN', 'RO', 'RR', 
           'RS', 'SC', 'SE', 'SP', 'TO']
    
    for uf in ufs:
        if uf in text.upper():
            data["creci_uf"] = uf
            break
    
    return data


def extract_comprovante_data(text: str) -> Dict[str, Any]:
    """Extrai dados de comprovante de residência"""
    data = {}
    
    # Pega todo o texto como endereço
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # Procura linhas que parecem endereço (contém números, CEP, etc)
    for line in lines:
        if any(x in line.upper() for x in ['RUA', 'AV', 'AVENIDA', 'R.', 'ENDEREÇO']):
            data["endereco"] = line
            break
    
    # CEP
    import re
    cep_match = re.search(r'\d{5}-?\d{3}', text)
    if cep_match:
        data["cep"] = cep_match.group().replace("-", "")
    
    return data


# Integração futura com Google Document AI
def process_with_google_document_ai(image_bytes: bytes) -> Dict[str, Any]:
    """
    Processa documento usando Google Document AI
    
    TODO: Implementar quando tiver conta GCP configurada
    """
    # from google.cloud import documentai
    
    # client = documentai.DocumentProcessorServiceClient()
    # processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
    
    # document = {"content": image_bytes, "mime_type": "image/jpeg"}
    # request = {"name": processor_name, "document": document}
    # result = client.process_document(request=request)
    
    # return parse_document_ai_result(result)
    
    return {
        "document_type": "unknown",
        "data": {},
        "error": "Google Document AI não configurado"
    }
