#!/usr/bin/env python3
"""
Script de teste simples para o webhook do Asaas
"""
import os
import json
from pathlib import Path

# Adicionar o diretório raiz do projeto ao path
project_root = Path(__file__).parent

def test_token_logic():
    """Testa a lógica de validação do token diretamente"""
    print("🔍 Testando lógica de validação do token...")
    
    # Simular a função de validação
    def validate_asaas_token(headers: dict, expected_token: str):
        """Simulação da função _validate_asaas"""
        token = headers.get("access-token") or headers.get("asaas-access-token")
        if not expected_token:
            return {"error": "missing_ASAAS_WEBHOOK_TOKEN", "status": 500}
        if not token or token != expected_token:
            return {"error": "invalid_asaas_webhook_token", "status": 401}
        return {"ok": True, "status": 200}
    
    # Teste 1: Token correto
    print("\n✅ Teste 1: Token correto")
    headers = {"access-token": "pratico_webhook_2024_abc123"}
    result = validate_asaas_token(headers, "pratico_webhook_2024_abc123")
    print(f"Resultado: {result}")
    
    # Teste 2: Token incorreto
    print("\n❌ Teste 2: Token incorreto")
    headers = {"access-token": "token-incorreto"}
    result = validate_asaas_token(headers, "pratico_webhook_2024_abc123")
    print(f"Resultado: {result}")
    
    # Teste 3: Sem token
    print("\n❌ Teste 3: Sem token")
    headers = {}
    result = validate_asaas_token(headers, "pratico_webhook_2024_abc123")
    print(f"Resultado: {result}")
    
    # Teste 4: Token com espaços
    print("\n❌ Teste 4: Token com espaços")
    headers = {"access-token": " pratico_webhook_2024_abc123 "}
    result = validate_asaas_token(headers, "pratico_webhook_2024_abc123")
    print(f"Resultado: {result}")

def test_render_env():
    """Testa o que sabemos sobre o ambiente do Render"""
    print("\n🔍 Informações sobre o ambiente...")
    
    # Token que deveria estar configurado
    expected_token = "pratico_webhook_2024_abc123"
    print(f"Token esperado: '{expected_token}'")
    
    # Verificar se há problemas comuns
    print("\n📋 Possíveis problemas identificados:")
    print("1. A API pode estar esperando exatamente 'pratico_webhook_2024_abc123'")
    print("2. Qualquer espaço extra pode causar falha na validação")
    print("3. O case sensitivity é importante")
    print("4. O token no Asaas deve ser idêntico ao do Render")

if __name__ == "__main__":
    print("🧪 Iniciando testes simples do webhook do Asaas...")
    test_token_logic()
    test_render_env()
    print("\n🏁 Testes concluídos!")