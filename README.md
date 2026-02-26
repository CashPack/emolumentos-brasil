# Emolumentos Brasil — Prático (v5)

## Fonte oficial
- `legacy/data/Pratico_Emolumentos_v5.xlsx`

## Escopo atual
- **Escritura pública com valor econômico** (por faixas De/Até/Emolumento) para **27 UFs (26 estados + DF)**.

## Como rodar (Python 3)

### Cálculo simples
```bash
python3 -c "from calculadora_emolumentos_v5 import CalculadoraEmolumentosV5; c=CalculadoraEmolumentosV5('legacy/data/Pratico_Emolumentos_v5.xlsx'); print(c.calcular_escritura_valor('SP', 500000))"
```

### Ranking para um valor
```bash
python3 calculadora_emolumentos_v5.py
```

## Estrutura
- `calculadora_emolumentos_v5.py` — interface de cálculo (v5)
- `emolumentos_v5.py` — parser do XLSX (sem dependências)
- `calculadora_emolumentos.py` — **LEGACY** (não usar como fonte)

## Pastas
- `legacy/data/` — PDFs/HTML/TXTs antigos + a planilha v5
- `legacy/reports/` — relatórios e comparativos antigos
- `legacy/docs/` — materiais e fluxo do negócio (HTML)
- `legacy/company/` — documentos da empresa
