# TABELA SIMPLIFICADA - EMOLUMENTOS NOTARIAIS 2026
# 23 Estados Brasileiros

| UF | ESTADO | ESCRITURA (s/ valor) | PROCURAÇÃO | CERTIDÃO | RANKING | STATUS |
|----|--------|---------------------|------------|----------|---------|--------|
| AL | Alagoas | R$ 42,80 | R$ 22,43 | R$ 20,00 | 🥇 1º | 🏆 CAMPEÃO |
| PB | Paraíba | R$ 85,18 | R$ 85,18 | R$ 17,04 | 🥈 2º | Excelente |
| CE | Ceará | R$ 92,78 | R$ 92,78 | R$ 27,94 | 🥉 3º | Muito bom |
| RR | Roraima | R$ 74,90 | R$ 31,41 | R$ 37,46 | 4º | Surpreendente! |
| SC | Santa Catarina | R$ 87,65 | R$ 62,59 | R$ 56,15 | 5º | 🏆 Campeã Sul |
| RS | Rio Grande do Sul | R$ 110,10 | R$ 68,60 | R$ 13,60 | 6º | Excelente |
| SE | Sergipe | R$ 146,58 | R$ 71,67 | R$ 61,08 | 7º | Intermediário |
| ES | Espírito Santo | R$ 136,86 | R$ 53,17 | R$ 17,18 | 8º | Melhor Sudeste |
| MA | Maranhão | R$ 149,57 | R$ 150,00 | R$ 50,00 | 9º | Intermediário |
| AC | Acre | R$ 171,90 | R$ 56,30 | R$ 37,80 | 10º | Intermediário |
| MS | Mato Grosso do Sul | R$ 185,34 | R$ 87,71 | R$ 41,03 | 11º | Melhor CO |
| GO | Goiás | R$ 189,29 | R$ 55,07 | R$ 55,07 | 12º | Intermediário |
| AP | Amapá | R$ 209,12 | R$ 78,45 | R$ 65,35 | 13º | Caro |
| RN | Rio Grande do Norte | R$ 235,54 | R$ 30,15 | R$ 60,00 | 14º | Caro |
| PE | Pernambuco | R$ 237,84 | R$ 96,15 | R$ 13,54 | 15º | Certidão barata |
| RO | Rondônia | R$ 285,70 | R$ 38,08 | R$ 20,30 | 16º | Intermediário |
| BA | Bahia | R$ 271,60 | R$ 118,58 | R$ 118,78 | 17º | Caro |
| PI | Piauí | R$ 299,91 | R$ 44,33 | R$ 49,89 | 18º | Caro |
| AM | Amazonas | R$ 300,00 | R$ 87,25 | R$ 48,63 | 19º | Muito caro |
| RJ | Rio de Janeiro | R$ 331,90 | R$ 150,00 | R$ 34,52 | 20º | Muito caro |
| SP | São Paulo | R$ 352,36 | R$ 92,34 | R$ 5,12 | 21º | Maior estado |
| DF | Distrito Federal | R$ 410,56 | R$ 59,12 | R$ 80,00 | 22º | ❌ Evitar |
| TO | Tocantins | R$ 114,02 | R$ 88,35 | R$ 56,15 | Intermediário | Intermediário |

## 🧮 COMO USAR A CALCULADORA

### Exemplo 1: Calcular Escritura em AL
```python
from calculadora_emolumentos import CalculadoraEmolumentos

calc = CalculadoraEmolumentos()
resultado = calc.calcular_escritura("AL", com_valor=False)
print(resultado)
```

### Exemplo 2: Comparar Estados
```python
comparacao = calc.comparar_estados(["AL", "SC", "SP"])
print(comparacao)
```

### Exemplo 3: Ranking Completo
```python
ranking = calc.ranking_escrituras()
for estado, valor, obs in ranking:
    print(f"{estado}: R$ {valor:.2f}")
```

## 🎯 RECOMENDAÇÕES POR REGIÃO

### SUL (3 estados)
- 🥇 **SC** - R$ 87,65 - Campeã
- 🥈 **RS** - R$ 110,10 - Excelente
- PR - Dados parciais

### SUDESTE (3 estados)
- 🥇 **ES** - R$ 136,86 - Melhor da região
- 🥈 **SP** - R$ 352,36 - Maior estado
- 🥉 RJ - R$ 331,90 - Caro

### NORDESTE (9 estados)
- 🥇 **AL** - R$ 42,80 - Campeão nacional
- 🥈 **PB** - R$ 85,18 - 2º lugar
- 🥉 **CE** - R$ 92,78 - 3º lugar

### NORTE (5 estados)
- 🥇 **RR** - R$ 74,90 - 4º nacional
- 🥈 **AC** - R$ 171,90
- 🥉 **AP** - R$ 209,12

### CENTRO-OESTE (3 estados)
- 🥇 **MS** - R$ 185,34
- 🥈 **GO** - R$ 189,29
- 🥉 **DF** - R$ 410,56 - Evitar

## 💡 SERVIÇOS ESPECIAIS

### Procuração MAIS BARATA:
1. AL - R$ 22,43
2. RR - R$ 31,41
3. RO - R$ 38,08
4. PE (previdenciária) - R$ 39,48

### Certidão MAIS BARATA:
1. **SP** - R$ 5,12 🏆
2. **PE** - R$ 13,54
3. **RS** - R$ 13,60
4. **ES** - R$ 17,18

### Reconhecimento de Firma MAIS BARATO:
1. **AL** - R$ 3,15 🏆
2. **CE** - R$ 3,50
3. **RR** - R$ 3,62
4. **RO** - R$ 3,80

## 📊 ESTATÍSTICAS

- **Total de estados:** 23
- **Cobertura:** 92% do Brasil
- **Média nacional:** R$ 188,47 (escritura s/ valor)
- **Mais barato:** AL (R$ 42,80)
- **Mais caro:** DF (R$ 410,56)
- **Diferença:** 859% mais caro que AL

## 🔗 ARQUIVOS RELACIONADOS

- `calculadora_emolumentos.py` - Calculadora Python
- `CURRENT_TABLE.md` - Tabela completa
- `[UF].txt` - Tabelas individuais (23 arquivos)
