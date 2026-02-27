# 🚀 INSTRUÇÕES DE DEPLOY - Correção Worker Asaas

**Data:** 2026-02-27  
**Correção:** Converter payload string → dict no worker  
**Status:** ✅ Código corrigido no workspace

---

## ✅ O QUE FOI FEITO

1. **Arquivo alterado:**
   - `/data/.openclaw/workspace/emolumentos-brasil/api/app/workers/webhook_tasks.py`

2. **Alterações:**
   - Adicionado import `json`
   - Função `processar_pagamento_recebido` agora aceita `payload` como qualquer tipo
   - Adicionada conversão automática: `if isinstance(payload, str): payload = json.loads(payload)`
   - Logging da conversão para debug

3. **Committado:**
   - Hash: `81a8c57`
   - Mensagem: "fix: converter payload string para dict no webhook worker"

---

## 🔧 COMO FAZER O DEPLOY NO RENDER

### **Opção 1: Via GitHub (Recomendado)**

Se você tem acesso ao GitHub e pode fazer push:

```bash
cd /data/.openclaw/workspace/emolumentos-brasil/api
git push origin main
```

O Render vai detectar automaticamente e fazer deploy.

---

### **Opção 2: Via Dashboard Render**

1. **Acessar o Render:**
   - URL: https://dashboard.render.com
   - Projeto: API FastAPI (pratico-documentos)

2. **Manual Deploy:**
   - Vá até a página do serviço API
   - Clique em "Manual Deploy" ou "Deploy"
   - O Render vai buscar o código mais recente do GitHub
   - Aguardar 2-5 minutos

3. **Verificar Deploy:**
   - Logs do Render
   - Confirmar que build foi bem-sucedido
   - Verificar se não há erros

---

### **Opção 3: Via Git (se configurado)**

Se o repositório já está conectado ao Render:

```bash
# Verificar status
git status

# Verificar mudanças
git log -1

# Fazer deploy (o Render puxa automaticamente)
git push origin main
```

---

## ⏱️ TEMPO ESTIMADO

- **Build Render:** 2-5 minutos
- **Total:** ~5-10 minutos

---

## ✅ VERIFICAÇÃO PÓS-DEPLOY

### **1. Verificar logs do Render:**

```bash
# Acessar dashboard Render
# URL: https://dashboard.render.com
# Projeto → Logs
# Procurar por:
# - "Payload convertido de string para dict"
# - "✅ Pagamento processado com sucesso"
```

### **2. Testar novamente:**

1. Criar nova cobrança de R$ 5,00 no Asaas
2. Pagar via PIX
3. Verificar logs do Render
4. Confirmar:
   - ✅ Webhook recebido
   - ✅ Payload convertido
   - ✅ Status atualizado
   - ✅ WhatsApp disparado

---

## 📋 CHECKLIST PÓS-DEPLOY

- [ ] Deploy iniciado no Render
- [ ] Build concluído sem erros
- [ ] Logs mostram "Payload convertido"
- [ ] Nova cobrança testada
- [ ] Pagamento processado com sucesso
- [ ] WhatsApp enviado corretamente

---

## 🚨 SE ALGO DAR ERRADO

### **Erro no build:**
```bash
# Verificar requirements.txt
cat requirements.txt

# Garantir que json está no padrão Python (não precisa instalar)
# json é parte do Python padrão
```

### **Erro no deploy:**
```bash
# Verificar se o branch está correto
git branch

# Verificar remote
git remote -v

# Forçar push (se necessário)
git push -f origin main
```

---

## 📞 SUPORTE

Se houver problemas:
1. Verificar logs completos do Render
2. Capturar screenshot dos erros
3. Enviar para análise

---

**Status atual:** ✅ Pronto para deploy  
**Próximo passo:** Fazer deploy no Render e testar novamente! 🚀
