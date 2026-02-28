"""
Serviço de integração com Asaas (Pagamentos)
Cria contas de corretores e gerencia split de pagamentos
"""
import os
import requests
from typing import Dict, Any, Optional

# Configuração Asaas
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY", "")
ASAAS_API_URL = os.getenv("ASAAS_API_URL", "https://api.asaas.com/v3")
ASAAS_ENV = os.getenv("ASAAS_ENV", "sandbox")  # sandbox ou production


def get_headers():
    """Retorna headers padrão para chamadas Asaas"""
    return {
        "access_token": ASAAS_API_KEY,
        "Content-Type": "application/json"
    }


async def create_asaas_account(
    nome: str,
    cpf: str,
    email: str,
    phone: str,
    external_reference: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cria conta de cliente no Asaas para o corretor
    
    Args:
        nome: Nome completo do corretor
        cpf: CPF (somente números)
        email: Email
        phone: Telefone
        external_reference: ID externo (nosso cadastro_id)
        
    Returns:
        Dict com customer_id e wallet_id (se configurado)
    """
    try:
        # Verifica se já existe cliente com este CPF
        existing = await find_customer_by_cpf(cpf)
        if existing:
            print(f"[ASAAS] Cliente já existe: {existing['id']}")
            return {
                "success": True,
                "customer_id": existing["id"],
                "wallet_id": existing.get("walletId"),
                "message": "Conta já existente"
            }
        
        # Cria novo cliente
        payload = {
            "name": nome,
            "cpfCnpj": cpf,
            "email": email,
            "mobilePhone": phone,
            "notificationDisabled": False,
            "externalReference": external_reference
        }
        
        response = requests.post(
            f"{ASAAS_API_URL}/customers",
            json=payload,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "customer_id": data["id"],
                "wallet_id": data.get("walletId"),
                "message": "Conta criada com sucesso"
            }
        else:
            error_msg = response.json().get("errors", [{}])[0].get("description", "Erro desconhecido")
            return {
                "success": False,
                "error": error_msg,
                "message": f"Erro ao criar conta: {error_msg}"
            }
            
    except Exception as e:
        print(f"[ASAAS] Erro: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Erro na comunicação com Asaas: {str(e)}"
        }


async def find_customer_by_cpf(cpf: str) -> Optional[Dict[str, Any]]:
    """Busca cliente no Asaas pelo CPF"""
    try:
        response = requests.get(
            f"{ASAAS_API_URL}/customers?cpfCnpj={cpf}",
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0]
        
        return None
    except Exception as e:
        print(f"[ASAAS] Erro ao buscar cliente: {e}")
        return None


async def create_payment_with_split(
    customer_id: str,
    value: float,
    description: str,
    due_date: str,
    split_wallets: list
) -> Dict[str, Any]:
    """
    Cria cobrança com split de pagamento
    
    Args:
        customer_id: ID do cliente pagador (comprador/vendedor)
        value: Valor total
        description: Descrição
        due_date: Data de vencimento (YYYY-MM-DD)
        split_wallets: Lista de wallets para divisão
            [
                {"walletId": "id_corretor", "percentualValue": 15},
                {"walletId": "id_cartorio", "percentualValue": 85}
            ]
            
    Returns:
        Dict com ID da cobrança e dados do split
    """
    try:
        payload = {
            "customer": customer_id,
            "billingType": "PIX",  # ou BOLETO, CREDIT_CARD
            "value": value,
            "dueDate": due_date,
            "description": description,
            "split": split_wallets
        }
        
        response = requests.post(
            f"{ASAAS_API_URL}/payments",
            json=payload,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "payment_id": data["id"],
                "status": data["status"],
                "invoice_url": data.get("invoiceUrl"),
                "split": data.get("split"),
                "pix_code": data.get("pixCode")
            }
        else:
            return {
                "success": False,
                "error": response.text
            }
            
    except Exception as e:
        print(f"[ASAAS] Erro ao criar pagamento: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_wallet_balance(wallet_id: str) -> Dict[str, Any]:
    """
    Consulta saldo de uma carteira (wallet)
    """
    try:
        response = requests.get(
            f"{ASAAS_API_URL}/wallets/{wallet_id}/balance",
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "balance": response.json()
            }
        else:
            return {
                "success": False,
                "error": response.text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def transfer_to_bank_account(
    wallet_id: str,
    value: float,
    bank_account_id: str
) -> Dict[str, Any]:
    """
    Transfere valor da carteira Asaas para conta bancária
    """
    try:
        payload = {
            "walletId": wallet_id,
            "value": value,
            "bankAccountId": bank_account_id
        }
        
        response = requests.post(
            f"{ASAAS_API_URL}/transfers",
            json=payload,
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "transfer_id": data["id"],
                "status": data["status"]
            }
        else:
            return {
                "success": False,
                "error": response.text
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
