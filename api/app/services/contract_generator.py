"""
Gerador de Contratos de Parceria
Gera contratos de parceria entre PRÁTICO e corretores
"""
import os
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CorretorData:
    nome: str
    cpf: str
    creci_numero: str
    creci_uf: str
    email: str
    phone: str
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None


def generate_partnership_contract(corretor: CorretorData) -> Dict[str, Any]:
    """
    Gera contrato de parceria comercial
    
    Retorna:
        Dict com conteúdo HTML do contrato e dados para assinatura
    """
    data_hoje = datetime.now().strftime("%d de %B de %Y")
    
    contrato_html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Contrato de Parceria Comercial</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            font-size: 24px;
            margin-bottom: 30px;
        }}
        h2 {{
            font-size: 18px;
            margin-top: 30px;
        }}
        .partes {{
            margin: 30px 0;
        }}
        .clausula {{
            margin: 20px 0;
            text-align: justify;
        }}
        .assinatura {{
            margin-top: 60px;
            page-break-inside: avoid;
        }}
        .linha {{
            border-top: 1px solid #000;
            margin-top: 60px;
            width: 300px;
        }}
    </style>
</head>
<body>
    <h1>CONTRATO DE PARCERIA COMERCIAL</h1>
    
    <p style="text-align: right;">Rio de Janeiro, {data_hoje}</p>
    
    <div class="partes">
        <h2>IDENTIFICAÇÃO DAS PARTES</h2>
        
        <p><strong>CONTRATADA:</strong></p>
        <p>
            <strong>PRÁTICO DOCUMENTOS ON-LINE LTDA</strong><br>
            CNPJ: 55.267.233/0001-10<br>
            Endereço: Av. das Américas, 500 - Bloco 8 - Sala 510<br>
            Barra da Tijuca, Rio de Janeiro/RJ - CEP 22640-100<br>
            Representada por: Alexandre Silva Oliveira
        </p>
        
        <p style="margin-top: 30px;"><strong>PARCEIRO:</strong></p>
        <p>
            <strong>{corretor.nome}</strong><br>
            CPF: {corretor.cpf}<br>
            CRECI: {corretor.creci_numero}/{corretor.creci_uf}<br>
            E-mail: {corretor.email}<br>
            Telefone: {corretor.phone}
        </p>
    </div>
    
    <h2>CLÁUSULAS DO CONTRATO</h2>
    
    <div class="clausula">
        <strong>1. OBJETO</strong>
        <p>
            1.1. O presente contrato tem por objeto estabelecer uma parceria comercial entre as partes 
            para indicação de clientes interessados em serviços de escrituração digital de imóveis.
        </p>
        <p>
            1.2. O PARCEIRO atuará como indicador de potenciais clientes (compradores e vendedores de imóveis) 
            para a execução de serviços notariais pela CONTRATADA.
        </p>
    </div>
    
    <div class="clausula">
        <strong>2. DA REMUNERAÇÃO</strong>
        <p>
            2.1. O PARCEIRO receberá comissão de 35% (trinta e cinco por cento) sobre o valor 
            da economia gerada para o cliente em relação aos custos de cartórios tradicionais.
        </p>
        <p>
            2.2. O pagamento será efetuado via plataforma Asaas, mediante crédito na carteira 
            digital do PARCEIRO, em até 2 (dois) dias úteis após a confirmação do pagamento pelo cliente final.
        </p>
        <p>
            2.3. A CONTRATADA se compromete a fornecer relatório mensal de indicações e comissões geradas.
        </p>
    </div>
    
    <div class="clausula">
        <strong>3. DAS OBRIGAÇÕES DO PARCEIRO</strong>
        <p>
            3.1. Indicar clientes potenciais para serviços de escritura digital.
        </p>
        <p>
            3.2. Manter seu registro no CRECI ativo e regular durante toda a vigência deste contrato.
        </p>
        <p>
            3.3. Não praticar atos que possam prejudicar a imagem da CONTRATADA.
        </p>
        <p>
            3.4. Zelar pela satisfação do cliente indicado, prestando esclarecimentos iniciais sobre o funcionamento 
            do serviço da CONTRATADA.
        </p>
    </div>
    
    <div class="clausula">
        <strong>4. DAS OBRIGAÇÕES DA CONTRATADA</strong>
        <p>
            4.1. Executar os serviços de escrituração com qualidade e dentro dos prazos acordados com o cliente.
        </p>
        <p>
            4.2. Repassar as comissões conforme estabelecido na cláusula 2.
        </p>
        <p>
            4.3. Fornecer material de apoio e treinamento ao PARCEIRO para melhor desempenho de suas atividades.
        </p>
    </div>
    
    <div class="clausula">
        <strong>5. VIGÊNCIA E RESCISÃO</strong>
        <p>
            5.1. O presente contrato terá vigência por prazo indeterminado, podendo ser rescindido 
            por qualquer das partes mediante aviso prévio de 30 (trinta) dias.
        </p>
        <p>
            5.2. Em caso de rescisão, as comissões de indicações já efetivadas serão pagas normalmente.
        </p>
    </div>
    
    <div class="clausula">
        <strong>6. DISPOSIÇÕES GERAIS</strong>
        <p>
            6.1. As partes elegem o foro da Comarca do Rio de Janeiro/RJ para dirimir quaisquer 
            dúvidas ou controvérsias decorrentes do presente contrato.
        </p>
        <p>
            6.2. Este contrato representa o acordo integral entre as partes, substituindo 
            quaisquer negociações ou acordos anteriores.
        </p>
    </div>
    
    <div class="assinatura">
        <p style="text-align: center; margin-top: 60px;">
            Rio de Janeiro, {data_hoje}
        </p>
        
        <div style="display: flex; justify-content: space-between; margin-top: 80px;">
            <div style="text-align: center;">
                <div class="linha"></div>
                <p><strong>PRÁTICO DOCUMENTOS ON-LINE LTDA</strong><br>
                CNPJ: 55.267.233/0001-10</p>
            </div>
            
            <div style="text-align: center;">
                <div class="linha"></div>
                <p><strong>{corretor.nome}</strong><br>
                CPF: {corretor.cpf}<br>
                CRECI: {corretor.creci_numero}/{corretor.creci_uf}</p>
            </div>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    return {
        "success": True,
        "content_html": contrato_html,
        "corretor": {
            "nome": corretor.nome,
            "cpf": corretor.cpf,
            "creci": f"{corretor.creci_numero}/{corretor.creci_uf}"
        },
        "data_geracao": data_hoje,
        "assinatura_url": None  # Será preenchido quando integrar com ZapSign ou similar
    }


def generate_contract_pdf(corretor: CorretorData) -> bytes:
    """
    Gera PDF do contrato para download
    
    TODO: Implementar geração de PDF (usar weasyprint, pdfkit, etc)
    """
    # Placeholder - retorna HTML por enquanto
    contrato = generate_partnership_contract(corretor)
    return contrato["content_html"].encode('utf-8')


async def create_zapsign_contract(corretor: CorretorData) -> Dict[str, Any]:
    """
    Cria contrato na plataforma ZapSign para assinatura digital
    
    TODO: Integrar com ZapSign API quando tiver conta
    """
    # Placeholder - implementar integração real
    return {
        "success": False,
        "message": "Integração com ZapSign não configurada",
        "manual_url": "https://praticodocumentos.com.br/contratos/manual"
    }
