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


def extract_document_data(image_bytes: bytes) -> Dict[str, Any]:
    """
    Extrai dados de documentos usando OCR (Google Document AI ou similar)
    
    Args:
        image_bytes: Bytes da imagem do documento
        
    Returns:
        Dict com:
        - document_type: rg, cnh, creci, comprovante, unknown
        - data: dados extraídos (nome, cpf, etc)
        - confidence: nível de confiança
    """
    # TODO: Implementar integração real com Google Document AI
    # Por enquanto, analisa texto para identificar tipo de documento
    
    # Detecta tipo de documento baseado em padrões do OCR
    # Nota: implementação real vai usar a API do Google
    
    detected_type = detect_document_type(image_bytes)
    
    return {
        "document_type": detected_type,
        "data": {},
        "confidence": 0.0,
        "raw_text": "",
        "message": "OCR não implementado - usar modelo local"
    }


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
