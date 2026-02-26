# Calculadora de Emolumentos Notariais - Brasil 2026
# ATENÇÃO: dataset hardcoded abaixo (23 UFs) é LEGACY e foi substituído pela
# fonte oficial: Pratico_Emolumentos_v5.xlsx (27 UFs) — Escritura com valor econômico.
# Use o módulo emolumentos_v5.py.

import json
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class EmolumentosEstado:
    estado: str
    escritura_sem_valor: float
    escritura_com_valor_ate_10k: float
    procuracao_sem_valor: float
    procuracao_previdenciaria: float
    reconhecimento_firma: float
    certidao_1a_folha: float
    testamento_sem_bens: float
    observacao: str = ""

# Dados dos 23 estados
TABELA_EMOLUMENTOS = {
    "AL": EmolumentosEstado(
        estado="Alagoas",
        escritura_sem_valor=42.80,
        escritura_com_valor_ate_10k=100.00,
        procuracao_sem_valor=22.43,
        procuracao_previdenciaria=22.43,
        reconhecimento_firma=3.15,
        certidao_1a_folha=20.00,
        testamento_sem_bens=150.00,
        observacao="Campeão nacional - custo mais baixo do Brasil"
    ),
    "PB": EmolumentosEstado(
        estado="Paraíba",
        escritura_sem_valor=85.18,
        escritura_com_valor_ate_10k=200.00,
        procuracao_sem_valor=85.18,
        procuracao_previdenciaria=85.18,
        reconhecimento_firma=17.04,
        certidao_1a_folha=17.04,
        testamento_sem_bens=851.76,
        observacao="2º mais barato do país"
    ),
    "CE": EmolumentosEstado(
        estado="Ceará",
        escritura_sem_valor=92.78,
        escritura_com_valor_ate_10k=250.00,
        procuracao_sem_valor=92.78,
        procuracao_previdenciaria=92.78,
        reconhecimento_firma=3.50,
        certidao_1a_folha=27.94,
        testamento_sem_bens=300.00,
        observacao="3º mais barato do país"
    ),
    "RR": EmolumentosEstado(
        estado="Roraima",
        escritura_sem_valor=74.90,
        escritura_com_valor_ate_10k=200.00,
        procuracao_sem_valor=31.41,
        procuracao_previdenciaria=31.41,
        reconhecimento_firma=3.62,
        certidao_1a_folha=37.46,
        testamento_sem_bens=200.00,
        observacao="4º lugar nacional - Surpreendente!"
    ),
    "SC": EmolumentosEstado(
        estado="Santa Catarina",
        escritura_sem_valor=87.65,
        escritura_com_valor_ate_10k=209.80,
        procuracao_sem_valor=62.59,
        procuracao_previdenciaria=62.59,
        reconhecimento_firma=10.00,
        certidao_1a_folha=56.15,
        testamento_sem_bens=300.00,
        observacao="Campeã do Sul"
    ),
    "RS": EmolumentosEstado(
        estado="Rio Grande do Sul",
        escritura_sem_valor=110.10,
        escritura_com_valor_ate_10k=222.80,
        procuracao_sem_valor=68.60,
        procuracao_previdenciaria=7.30,
        reconhecimento_firma=7.30,
        certidao_1a_folha=13.60,
        testamento_sem_bens=430.20,
        observacao="Excelente custo-benefício"
    ),
    "SE": EmolumentosEstado(
        estado="Sergipe",
        escritura_sem_valor=146.58,
        escritura_com_valor_ate_10k=303.09,
        procuracao_sem_valor=71.67,
        procuracao_previdenciaria=11.94,
        reconhecimento_firma=4.65,
        certidao_1a_folha=61.08,
        testamento_sem_bens=143.32,
        observacao="Intermediário"
    ),
    "ES": EmolumentosEstado(
        estado="Espírito Santo",
        escritura_sem_valor=136.86,
        escritura_com_valor_ate_10k=300.00,
        procuracao_sem_valor=53.17,
        procuracao_previdenciaria=53.17,
        reconhecimento_firma=4.29,
        certidao_1a_folha=17.18,
        testamento_sem_bens=400.00,
        observacao="Melhor do Sudeste"
    ),
    "MA": EmolumentosEstado(
        estado="Maranhão",
        escritura_sem_valor=149.57,
        escritura_com_valor_ate_10k=300.00,
        procuracao_sem_valor=150.00,
        procuracao_previdenciaria=150.00,
        reconhecimento_firma=10.00,
        certidao_1a_folha=50.00,
        testamento_sem_bens=500.00,
        observacao="Intermediário"
    ),
    "AC": EmolumentosEstado(
        estado="Acre",
        escritura_sem_valor=171.90,
        escritura_com_valor_ate_10k=350.00,
        procuracao_sem_valor=56.30,
        procuracao_previdenciaria=56.30,
        reconhecimento_firma=4.90,
        certidao_1a_folha=37.80,
        testamento_sem_bens=450.00,
        observacao="Intermediário"
    ),
    "MS": EmolumentosEstado(
        estado="Mato Grosso do Sul",
        escritura_sem_valor=185.34,
        escritura_com_valor_ate_10k=400.00,
        procuracao_sem_valor=87.71,
        procuracao_previdenciaria=87.71,
        reconhecimento_firma=15.00,
        certidao_1a_folha=41.03,
        testamento_sem_bens=837.53,
        observacao="Melhor do Centro-Oeste"
    ),
    "GO": EmolumentosEstado(
        estado="Goiás",
        escritura_sem_valor=189.29,
        escritura_com_valor_ate_10k=400.00,
        procuracao_sem_valor=55.07,
        procuracao_previdenciaria=55.07,
        reconhecimento_firma=7.11,
        certidao_1a_folha=55.07,
        testamento_sem_bens=500.00,
        observacao="Intermediário"
    ),
    "AP": EmolumentosEstado(
        estado="Amapá",
        escritura_sem_valor=209.12,
        escritura_com_valor_ate_10k=450.00,
        procuracao_sem_valor=78.45,
        procuracao_previdenciaria=78.45,
        reconhecimento_firma=5.21,
        certidao_1a_folha=65.35,
        testamento_sem_bens=550.00,
        observacao="Caro"
    ),
    "RN": EmolumentosEstado(
        estado="Rio Grande do Norte",
        escritura_sem_valor=235.54,
        escritura_com_valor_ate_10k=500.00,
        procuracao_sem_valor=30.15,
        procuracao_previdenciaria=30.15,
        reconhecimento_firma=12.00,
        certidao_1a_folha=60.00,
        testamento_sem_bens=600.00,
        observacao="Caro"
    ),
    "PE": EmolumentosEstado(
        estado="Pernambuco",
        escritura_sem_valor=237.84,
        escritura_com_valor_ate_10k=500.00,
        procuracao_sem_valor=96.15,
        procuracao_previdenciaria=39.48,
        reconhecimento_firma=5.79,
        certidao_1a_folha=13.54,
        testamento_sem_bens=946.07,
        observacao="Certidão mais barata do país"
    ),
    "RO": EmolumentosEstado(
        estado="Rondônia",
        escritura_sem_valor=285.70,
        escritura_com_valor_ate_10k=550.00,
        procuracao_sem_valor=38.08,
        procuracao_previdenciaria=19.08,
        reconhecimento_firma=3.80,
        certidao_1a_folha=20.30,
        testamento_sem_bens=600.00,
        observacao="Procuração competitiva"
    ),
    "BA": EmolumentosEstado(
        estado="Bahia",
        escritura_sem_valor=271.60,
        escritura_com_valor_ate_10k=550.00,
        procuracao_sem_valor=118.58,
        procuracao_previdenciaria=118.58,
        reconhecimento_firma=7.20,
        certidao_1a_folha=118.78,
        testamento_sem_bens=700.00,
        observacao="Caro"
    ),
    "PI": EmolumentosEstado(
        estado="Piauí",
        escritura_sem_valor=299.91,
        escritura_com_valor_ate_10k=600.00,
        procuracao_sem_valor=44.33,
        procuracao_previdenciaria=44.33,
        reconhecimento_firma=15.00,
        certidao_1a_folha=49.89,
        testamento_sem_bens=750.00,
        observacao="Caro"
    ),
    "AM": EmolumentosEstado(
        estado="Amazonas",
        escritura_sem_valor=300.00,
        escritura_com_valor_ate_10k=600.00,
        procuracao_sem_valor=87.25,
        procuracao_previdenciaria=87.25,
        reconhecimento_firma=11.80,
        certidao_1a_folha=48.63,
        testamento_sem_bens=800.00,
        observacao="Muito caro"
    ),
    "RJ": EmolumentosEstado(
        estado="Rio de Janeiro",
        escritura_sem_valor=331.90,
        escritura_com_valor_ate_10k=700.00,
        procuracao_sem_valor=150.00,
        procuracao_previdenciaria=150.00,
        reconhecimento_firma=20.00,
        certidao_1a_folha=34.52,
        testamento_sem_bens=900.00,
        observacao="Muito caro"
    ),
    "SP": EmolumentosEstado(
        estado="São Paulo",
        escritura_sem_valor=352.36,
        escritura_com_valor_ate_10k=822.17,
        procuracao_sem_valor=92.34,
        procuracao_previdenciaria=92.34,
        reconhecimento_firma=8.83,
        certidao_1a_folha=5.12,
        testamento_sem_bens=607.47,
        observacao="Maior estado - certidão mais barata"
    ),
    "TO": EmolumentosEstado(
        estado="Tocantins",
        escritura_sem_valor=114.02,
        escritura_com_valor_ate_10k=247.97,
        procuracao_sem_valor=88.35,
        procuracao_previdenciaria=44.12,
        reconhecimento_firma=10.30,
        certidao_1a_folha=56.15,
        testamento_sem_bens=344.84,
        observacao="Intermediário"
    ),
    "DF": EmolumentosEstado(
        estado="Distrito Federal",
        escritura_sem_valor=410.56,
        escritura_com_valor_ate_10k=900.00,
        procuracao_sem_valor=59.12,
        procuracao_previdenciaria=59.12,
        reconhecimento_firma=25.00,
        certidao_1a_folha=80.00,
        testamento_sem_bens=1000.00,
        observacao="MAIS CARO DO PAÍS - Evitar"
    ),
}

class CalculadoraEmolumentos:
    def __init__(self):
        self.tabela = TABELA_EMOLUMENTOS
    
    def get_estado(self, uf: str) -> Optional[EmolumentosEstado]:
        """Retorna os dados de um estado específico"""
        return self.tabela.get(uf.upper())
    
    def calcular_escritura(self, uf: str, com_valor: bool = False, valor: float = 0) -> dict:
        """Calcula o valor da escritura"""
        estado = self.get_estado(uf)
        if not estado:
            return {"erro": "Estado não encontrado"}
        
        if com_valor and valor > 0:
            # Simplificação - usar faixa de até 10k como referência
            base = estado.escritura_com_valor_ate_10k
            if valor > 10000:
                base = base * (valor / 10000) * 0.5  # Estimativa
        else:
            base = estado.escritura_sem_valor
        
        return {
            "estado": estado.estado,
            "uf": uf.upper(),
            "tipo": "Com valor" if com_valor else "Sem valor",
            "valor_declarado": valor if com_valor else 0,
            "emolumentos": round(base, 2),
            "observacao": estado.observacao
        }
    
    def calcular_procuracao(self, uf: str, previdenciaria: bool = False) -> dict:
        """Calcula o valor da procuração"""
        estado = self.get_estado(uf)
        if not estado:
            return {"erro": "Estado não encontrado"}
        
        valor = estado.procuracao_previdenciaria if previdenciaria else estado.procuracao_sem_valor
        tipo = "Previdenciária" if previdenciaria else "Geral"
        
        return {
            "estado": estado.estado,
            "uf": uf.upper(),
            "tipo": tipo,
            "emolumentos": round(valor, 2),
            "observacao": estado.observacao
        }
    
    def calcular_certidao(self, uf: str, folhas: int = 1) -> dict:
        """Calcula o valor da certidão"""
        estado = self.get_estado(uf)
        if not estado:
            return {"erro": "Estado não encontrado"}
        
        valor = estado.certidao_1a_folha
        if folhas > 1:
            valor = valor + (valor * 0.5 * (folhas - 1))  # 50% por folha adicional
        
        return {
            "estado": estado.estado,
            "uf": uf.upper(),
            "folhas": folhas,
            "emolumentos": round(valor, 2),
            "observacao": estado.observacao
        }
    
    def ranking_escrituras(self) -> list:
        """Retorna o ranking de estados por custo de escritura sem valor"""
        estados = sorted(self.tabela.values(), key=lambda x: x.escritura_sem_valor)
        return [(e.estado, e.escritura_sem_valor, e.observacao) for e in estados]
    
    def estados_recomendados(self, top_n: int = 10) -> list:
        """Retorna os estados mais recomendados para expansão"""
        ranking = self.ranking_escrituras()
        return ranking[:top_n]
    
    def comparar_estados(self, ufs: list) -> dict:
        """Compara múltiplos estados"""
        resultado = {}
        for uf in ufs:
            estado = self.get_estado(uf)
            if estado:
                resultado[uf.upper()] = {
                    "nome": estado.estado,
                    "escritura_s_valor": estado.escritura_sem_valor,
                    "procuracao": estado.procuracao_sem_valor,
                    "certidao": estado.certidao_1a_folha,
                    "reconhecimento_firma": estado.reconhecimento_firma,
                    "total_servicos_basicos": round(
                        estado.escritura_sem_valor + 
                        estado.procuracao_sem_valor + 
                        estado.certidao_1a_folha + 
                        estado.reconhecimento_firma, 2
                    )
                }
        return resultado
    
    def gerar_relatorio(self, uf: str) -> str:
        """Gera um relatório detalhado para um estado"""
        estado = self.get_estado(uf)
        if not estado:
            return "Estado não encontrado"
        
        relatorio = f"""
╔══════════════════════════════════════════════════════════════╗
║  RELATÓRIO DE EMOLUMENTOS - {estado.estado.upper()} ({uf.upper()})
╚══════════════════════════════════════════════════════════════╝

📋 ESCRITURAS:
   • Sem valor declarado:        R$ {estado.escritura_sem_valor:.2f}
   • Com valor (até R$ 10.000):  R$ {estado.escritura_com_valor_ate_10k:.2f}

📋 PROCURAÇÕES:
   • Procuração geral:           R$ {estado.procuracao_sem_valor:.2f}
   • Procuração previdenciária:  R$ {estado.procuracao_previdenciaria:.2f}

📋 OUTROS SERVIÇOS:
   • Reconhecimento de firma:    R$ {estado.reconhecimento_firma:.2f}
   • Certidão (1ª folha):        R$ {estado.certidao_1a_folha:.2f}
   • Testamento (sem bens):      R$ {estado.testamento_sem_bens:.2f}

💡 OBSERVAÇÃO: {estado.observacao}

📊 CUSTO TOTAL DOS 4 SERVIÇOS BÁSICOS:
   R$ {estado.escritura_sem_valor + estado.procuracao_sem_valor + estado.certidao_1a_folha + estado.reconhecimento_firma:.2f}

═══════════════════════════════════════════════════════════════
        """
        return relatorio

# Função de demonstração
def demonstracao():
    """Demonstra o uso da calculadora"""
    calc = CalculadoraEmolumentos()
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     CALCULADORA DE EMOLUMENTOS NOTARIAIS - BRASIL 2026       ║")
    print("║                    23 Estados Analisados                     ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Top 5 estados mais baratos
    print("🏆 TOP 5 ESTADOS MAIS COMPETITIVOS:")
    print("-" * 60)
    for i, (estado, valor, obs) in enumerate(calc.estados_recomendados(5), 1):
        print(f"{i}º {estado:.<30} R$ {valor:>8.2f} - {obs}")
    
    print("\n" + "="*60)
    print("📊 COMPARAÇÃO: AL vs SP vs DF")
    print("="*60)
    comparacao = calc.comparar_estados(["AL", "SP", "DF"])
    for uf, dados in comparacao.items():
        print(f"\n{uf} - {dados['nome']}:")
        print(f"   Escritura: R$ {dados['escritura_s_valor']:.2f}")
        print(f"   Procuração: R$ {dados['procuracao']:.2f}")
        print(f"   Total 4 serviços: R$ {dados['total_servicos_basicos']:.2f}")
    
    print("\n" + "="*60)
    print("📋 RELATÓRIO DETALHADO - AL (Alagoas)")
    print("="*60)
    print(calc.gerar_relatorio("AL"))

if __name__ == "__main__":
    demonstracao()
