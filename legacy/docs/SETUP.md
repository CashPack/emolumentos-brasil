# 📂 Shared Repository Setup

Your private workspace for storing emolument tables is ready!

## 📍 Location
`/data/.openclaw/workspace/shared_repo/`

## 📋 Purpose
Store all state-level emolument tables for:
- Cost comparison analysis  
- Pilot city identification  
- Revenue projection modeling  

## 📤 Submission Format
Use the following structure when pasting tables:

```
---INÍCIO [ESTADO]---
[full table content]
---FIM [ESTADO]---
```

Example for Rio Grande do Sul:
```
---INÍCIO RS---
UF | Cartório | Emolumento (R$) | TaxaProcurador (R$)
RS | Cartório_X | 2.473,70 | 110,10
RS | Cartório_Y | 2.800,00 | 120,00
---FIM RS---
```

## ✅ What Happens Next
1. I’ll store your content in `/data/.openclaw/workspace/shared_repo/[ESTADO].txt`
2. I’ll extract emolument values and calculate savings
3. I’ll identify optimal pilot cities (small towns with cost‑strained cartórios)
4. I’ll generate a ready‑to‑use report (Markdown/CSV)

## 🚀 Ready When You Are
Just paste your first table between the markers above, and I’ll begin processing it immediately. 🚀