#!/bin/bash
# Script de deploy para correção do webhook Asaas
# Data: 2026-02-27
# Correção: Converter payload string → dict no worker

echo "🚀 INICIANDO DEPLOY - CORREÇÃO WORKER ASAAS"
echo ""

# 1. Verificar se estamos no diretório correto
cd /data/.openclaw/workspace/emolumentos-brasil/api || {
    echo "❌ Erro: Não é possível acessar diretório da API"
    exit 1
}

# 2. Verificar mudanças
echo "📝 Verificando mudanças..."
git status

# 3. Adicionar mudanças
echo ""
echo "➕ Adicionando mudanças..."
git add app/workers/webhook_tasks.py

# 4. Commit
echo ""
echo "💾 Commitando..."
git commit -m "fix: converter payload string para dict no webhook worker

- Adicionar tratamento automático de payload string→dict
- Melhorar resiliência do worker para diferentes formatos
- Logar conversão para debug"

# 5. Push para main
echo ""
echo "📤 Enviando para remote..."
git push origin main

# 6. Aguardar deploy do Render
echo ""
echo "⏳ Render iniciando deploy automático..."
echo "Tempo estimado: 2-5 minutos"
echo ""
echo "✅ Deploy iniciado com sucesso!"
echo ""
echo "PRÓXIMOS PASSOS:"
echo "1. Aguardar deploy terminar (logs do Render)"
echo "2. Criar nova cobrança de teste"
echo "3. Pagar via PIX"
echo "4. Verificar se processamento funciona"
