#!/usr/bin/env python3
"""
Script de teste para o webhook do Asaas
"""
import os
import sys
import json
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import getenv
from app.routers.webhooks_asaas import _validate_asaas

def test_token_validation():
    """Testa a validação do token do Asaas"""
    print("🔍 Testando validação do token do Asaas...")
    
    # Simular requisição com token correto
    from fastapi import Request
    from unittest.mock import Mock
    
    # Teste 1: Token correto
    print("\n✅ Teste 1: Token correto")
    request = Mock()
    request.headers = {"access-token": "pratico_webhook_2024_abc123"}
    
    try:
        # Precisamos simular o ambiente
        os.environ["ASAAS_WEBHOOK_TOKEN"] = "pratico_webhook_2024_abc123"
        _validate_asaas(request)
        print("✅ Token válido - validação passou")
    except Exception as e:
        print(f"❌ Falha na validação: {e}")
    
    # Teste 2: Token incorreto
    print("\n❌ Teste 2: Token incorreto")
    request = Mock()
    request.headers = {"access-token": "token-incorreto"}
    
    try:
        _validate_asaas(request)
        print("❌ Token inválido - validação deveria falhar")
    except Exception as e:
        print(f"✅ Token inválido capturado: {e}")
    
    # Teste 3: Sem token
    print("\n❌ Teste 3: Sem token")
    request = Mock()
    request.headers = {}
    
    try:
        _validate_asaas(request)
        print("❌ Sem token - validação deveria falhar")
    except Exception as e:
        print(f"✅ Sem token capturado: {e}")

def test_environment_variables():
    """Testa se as variáveis de ambiente estão acessíveis"""
    print("\n🔍 Testando variáveis de ambiente...")
    
    try:
        token = getenv("ASAAS_WEBHOOK_TOKEN")
        print(f"✅ ASAAS_WEBHOOK_TOKEN: {token}")
    except Exception as e:
        print(f"❌ Falha ao obter ASAAS_WEBHOOK_TOKEN: {e}")
    
    try:
        db_url = getenv("DATABASE_URL")
        print(f"✅ DATABASE_URL: {db_url[:50]}..." if db_url else "❌ DATABASE_URL: vazia")
    except Exception as e:
        print(f"❌ Falha ao obter DATABASE_URL: {e}")

if __name__ == "__main__":
    print("🧪 Iniciando testes do webhook do Asaas...")
    test_token_validation()
    test_environment_variables()
    print("\n🏁 Testes concluídos!")