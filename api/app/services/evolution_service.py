"""
Serviço de integração com Evolution API (WhatsApp)
"""
import os
import requests
from typing import Optional, Dict, Any

# Configuração da Evolution API
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://72.61.59.75:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "pratico-wpp")


def send_validation_message(phone: str, code: str, name: str = "") -> Dict[str, Any]:
    """
    Envia mensagem de validação via WhatsApp usando Evolution API
    
    Args:
        phone: Número do telefone (formato: 5511999999999)
        code: Código de 4 dígitos
        name: Nome do usuário (opcional)
    
    Returns:
        Dict com status do envio
    """
    # Formata mensagem
    greeting = f"Olá {name}, " if name else "Olá, "
    message = f"""
{greeting}
Recebemos uma solicitação para validar seu número na PRÁTICO Documentos.

*Código de validação: {code}*

Este código expira em 5 minutos.
Se você não solicitou essa validação, ignore esta mensagem.
    """.strip()

    # Prepara payload para Evolution API
    payload = {
        "number": phone,
        "text": message,
        "delay": 1200  # Delay para parecer mais natural
    }

    try:
        url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 201:
            return {
                "success": True,
                "message": "Mensagem enviada com sucesso",
                "data": response.json()
            }
        else:
            return {
                "success": False,
                "message": f"Erro na Evolution API: {response.status_code}",
                "data": response.text
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao enviar mensagem: {str(e)}",
            "data": None
        }


def check_whatsapp_number(phone: str) -> Dict[str, Any]:
    """
    Verifica se o número existe no WhatsApp
    
    Args:
        phone: Número do telefone (formato: 5511999999999)
    
    Returns:
        Dict com status da verificação
    """
    try:
        url = f"{EVOLUTION_API_URL}/chat/check-exists/{EVOLUTION_INSTANCE}?number={phone}"
        headers = {"apikey": EVOLUTION_API_KEY}

        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "exists": data.get("exists", False),
                "data": data
            }
        else:
            return {
                "success": False,
                "exists": False,
                "message": f"Erro: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "exists": False,
            "message": str(e)
        }
