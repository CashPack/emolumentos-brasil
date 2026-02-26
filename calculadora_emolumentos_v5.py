"""Calculadora (v5) — Prático Emolumentos.

Fonte oficial: Pratico_Emolumentos_v5.xlsx
Escopo atual: apenas ESCRITURA PÚBLICA COM VALOR ECONÔMICO.

Uso:
    from calculadora_emolumentos_v5 import CalculadoraEmolumentosV5
    calc = CalculadoraEmolumentosV5()
    calc.calcular_escritura_valor('SP', 500000)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from emolumentos_v5 import PlanilhaEmolumentosV5


@dataclass
class ResultadoEscrituraValor:
    uf: str
    valor: float
    emolumento: float
    faixa_de: float
    faixa_ate: float
    fonte: str
    observacao: str = ""


class CalculadoraEmolumentosV5:
    def __init__(self, xlsx_path: Optional[str] = None):
        if xlsx_path is None:
            # assume que roda na raiz do repositório
            xlsx_path = os.path.join(os.path.dirname(__file__), "legacy", "data", "Pratico_Emolumentos_v5.xlsx")
        self.xlsx_path = xlsx_path
        self._planilha = PlanilhaEmolumentosV5(self.xlsx_path)

    def calcular_escritura_valor(self, uf: str, valor: float) -> Dict[str, object]:
        """Retorna o emolumento da escritura com valor, baseado na faixa da planilha."""
        return self._planilha.calcular_escritura_por_valor(uf, valor)

    def ranking_por_valor(self, valor: float) -> List[Tuple[str, float]]:
        """Ranking (UF, emolumento) para um valor específico.

        Observação: usa as abas por UF (27 UFs). Mais lento que uma tabela já consolidada,
        mas é a forma mais fiel.
        """
        ufs = [
            "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA",
            "PB","PE","PR","PI","RJ","RN","RS","RO","RR","SC","SE","SP","TO",
        ]
        out = []
        for uf in ufs:
            r = self.calcular_escritura_valor(uf, valor)
            if "emolumento" in r:
                out.append((uf, float(r["emolumento"])))
        out.sort(key=lambda x: x[1])
        return out


if __name__ == "__main__":
    calc = CalculadoraEmolumentosV5()
    v = 500000
    for uf in ["SP", "RS", "DF", "AL"]:
        print(uf, calc.calcular_escritura_valor(uf, v))
    print("\nTop 10 (R$ 500.000):")
    for uf, emo in calc.ranking_por_valor(v)[:10]:
        print(uf, emo)
