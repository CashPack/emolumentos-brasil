"""
Gerador de Contratos de Parceria
Gera contratos de parceria entre PRÁTICO e corretores com dados oficiais
"""
from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class CorretorData:
    nome: str
    cpf: str
    creci_numero: str
    creci_uf: str
    email: str
    phone: str
    endereco: str = ""
    estado_civil: str = ""


# Dados oficiais da empresa (do contrato social)
EMPRESA = {
    "razao_social": "PRATICO DOCUMENTOS ON-LINE LTDA",
    "cnpj": "65.279.926/0001-03",
    "endereco": "Rua Armando Andrade, 97, Box:572, Bom Retiro, Joinville - SC, CEP 89.223-066",
    "representante": {
        "nome": "Joaquim Pereira Ramos Junior",
        "cpf": "077.520.447-17",
        "cargo": "Sócio Administrador"
    },
    "foro": "Joinville - SC"
}


def generate_partnership_contract(corretor: CorretorData) -> Dict[str, Any]:
    """
    Gera contrato de parceria comercial com dados oficiais da empresa
    
    Retorna:
        Dict com conteúdo HTML do contrato e dados para assinatura
    """
    data_hoje = datetime.now().strftime("%d/%m/%Y às %H:%M")
    data_iso = datetime.now().isoformat()
    
    # Formata CPF do corretor
    cpf_corretor = corretor.cpf
    if len(cpf_corretor) == 11:
        cpf_formatado = f"{cpf_corretor[:3]}.{cpf_corretor[3:6]}.{cpf_corretor[6:9]}-{cpf_corretor[9:]}"
    else:
        cpf_formatado = cpf_corretor
    
    contrato_html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Contrato de Parceria Comercial</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            line-height: 1.8;
            max-width: 800px;
            margin: 40px auto;
            padding: 40px;
            color: #333;
        }}
        h1 {{
            text-align: center;
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 40px;
            text-transform: uppercase;
        }}
        h2 {{
            font-size: 16px;
            font-weight: bold;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        h3 {{
            font-size: 14px;
            font-weight: bold;
            margin-top: 20px;
        }}
        .partes {{
            margin: 30px 0;
            text-align: justify;
        }}
        .clausula {{
            margin: 20px 0;
            text-align: justify;
        }}
        .assinatura {{
            margin-top: 80px;
            page-break-inside: avoid;
        }}
        .linha {{
            border-top: 1px solid #000;
            margin-top: 60px;
            width: 350px;
        }}
        .aceite-box {{
            background: #f5f5f5;
            padding: 20px;
            margin: 30px 0;
            border-left: 4px solid #333;
        }}
        strong {{
            font-weight: bold;
        }}
        ul {{
            margin-left: 20px;
        }}
        li {{
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <h1>CONTRATO DE PARCERIA COMERCIAL</h1>
    
    <div class="partes">
        <p>Por este instrumento particular, de um lado <strong>{EMPRESA['razao_social']}</strong>, 
        inscrita no CNPJ sob nº <strong>{EMPRESA['cnpj']}</strong>, com sede na {EMPRESA['endereco']}, 
        doravante denominada <strong>CONTRATANTE</strong>, neste ato representada por seu 
        {EMPRESA['representante']['cargo']} <strong>{EMPRESA['representante']['nome']}</strong>, 
        brasileiro, CPF nº <strong>{EMPRESA['representante']['cpf']}</strong>,</p>
        
        <p style="text-align: center; margin: 20px 0;"><strong>E</strong></p>
        
        <p>de outro lado <strong>{corretor.nome.upper()}</strong>, inscrito(a) no CPF sob nº 
        <strong>{cpf_formatado}</strong>, CRECI nº <strong>{corretor.creci_numero}/{corretor.creci_uf}</strong>, 
        {f"{corretor.estado_civil.replace('_', ' ')}, " if corretor.estado_civil else ""}
        residente e domiciliado(a) à <strong>{corretor.endereco or 'Endereço não informado'}</strong>, 
        doravante denominado(a) <strong>PARCEIRO</strong>,</p>
        
        <p>têm justo e acordado o presente <strong>CONTRATO DE PARCERIA COMERCIAL</strong>, 
        mediante as cláusulas e condições a seguir:</p>
    </div>
    
    <div class="clausula">
        <h2>CLÁUSULA 1ª - OBJETO</h2>
        <p>O presente contrato tem por objeto a parceria comercial entre as partes para a captação 
        de clientes interessados nos serviços de escrituração imobiliária oferecidos pela CONTRATANTE, 
        bem como em outros serviços correlatos que venham a ser oferecidos, com remuneração do PARCEIRO 
        conforme estabelecido na Cláusula 2ª.</p>
    </div>
    
    <div class="clausula">
        <h2>CLÁUSULA 2ª - REMUNERAÇÃO</h2>
        
        <h3>2.1</h3>
        <p>O PARCEIRO fará jus a uma comissão sobre a margem obtida em cada operação concretizada 
        por cliente por ele indicado, paga automaticamente via split de pagamentos Asaas.</p>
        
        <h3>2.2</h3>
        <p>O <strong>percentual da comissão será definido para cada operação</strong>, considerando fatores como:</p>
        <ul>
            <li>I. O estado de origem do imóvel;</li>
            <li>II. O estado do cartório parceiro onde a escritura será lavrada;</li>
            <li>III. O valor do imóvel;</li>
            <li>IV. Promoções ou condições especiais vigentes no momento da operação.</li>
        </ul>
        
        <h3>2.3</h3>
        <p>O percentual aplicável será <strong>comunicado ao PARCEIRO previamente à conclusão da operação</strong>, 
        podendo ser consultado a qualquer momento através do sistema ou painel do parceiro.</p>
        
        <h3>2.4</h3>
        <p>A CONTRATANTE poderá, a seu critério, <strong>alterar as tabelas de comissionamento</strong> 
        para novas operações, mediante comunicação prévia aos parceiros, garantidas as condições já 
        pactuadas para operações em andamento.</p>
    </div>
    
    <div class="clausula">
        <h2>CLÁUSULA 3ª - OBRIGAÇÕES DO PARCEIRO</h2>
        <ul>
            <li><strong>I.</strong> Indicar clientes potenciais para os serviços da CONTRATANTE;</li>
            <li><strong>II.</strong> Fornecer informações verídicas sobre os clientes indicados;</li>
            <li><strong>III.</strong> Auxiliar os clientes no processo de envio de documentos, quando necessário;</li>
            <li><strong>IV.</strong> Manter seus dados cadastrais atualizados junto à CONTRATANTE;</li>
            <li><strong>V.</strong> Agir com diligência e boa-fé em todas as interações com clientes e com a CONTRATANTE.</li>
        </ul>
    </div>
    
    <div class="clausula">
        <h2>CLÁUSULA 4ª - OBRIGAÇÕES DA CONTRATANTE</h2>
        <ul>
            <li><strong>I.</strong> Processar os pedidos de escritura dos clientes indicados dentro dos prazos estabelecidos;</li>
            <li><strong>II.</strong> Efetuar o pagamento das comissões devidas ao PARCEIRO conforme o estabelecido na Cláusula 2ª;</li>
            <li><strong>III.</strong> Disponibilizar ao PARCEIRO acesso a sistema ou painel para consulta de comissões e andamento dos processos;</li>
            <li><strong>IV.</strong> Fornecer suporte ao PARCEIRO durante todo o processo;</li>
            <li><strong>V.</strong> Manter o PARCEIRO informado sobre alterações nas condições de comissionamento.</li>
        </ul>
    </div>
    
    <div class="clausula">
        <h2>CLÁUSULA 5ª - VIGÊNCIA E RESCISÃO</h2>
        
        <h3>5.1</h3>
        <p>O presente contrato entra em vigor na data de sua aceitação e terá vigência por prazo indeterminado.</p>
        
        <h3>5.2</h3>
        <p>Qualquer das partes poderá resilir o contrato mediante notificação prévia de 30 (trinta) dias, 
        por escrito ou por meio eletrônico.</p>
        
        <h3>5.3</h3>
        <p>A rescisão não afetará o direito do PARCEIRO às comissões relativas a operações já concluídas 
        ou em andamento cuja indicação tenha sido realizada anteriormente.</p>
    </div>
    
    <div class="clausula">
        <h2>CLÁUSULA 6ª - DISPOSIÇÕES GERAIS</h2>
        
        <h3>I</h3>
        <p>O presente contrato não cria qualquer vínculo empregatício entre as partes, inexistindo relação 
        de subordinação, horário a cumprir ou exclusividade;</p>
        
        <h3>II</h3>
        <p>As partes declaram que a prestação de serviços se dará de forma autônoma, assumindo cada qual 
        seus próprios custos e riscos;</p>
        
        <h3>III</h3>
        <p>Este contrato poderá ser alterado a qualquer tempo mediante comum acordo entre as partes, 
        formalizado por aditivo contratual;</p>
        
        <h3>IV</h3>
        <p>Fica eleito o foro da Comarca de <strong>{EMPRESA['foro']}</strong> para dirimir quaisquer controvérsias 
        oriundas deste contrato, com expressa renúncia a qualquer outro, por mais privilegiado que seja.</p>
    </div>
    
    <div class="aceite-box">
        <h2>ACEITE DIGITAL</h2>
        <p><strong>Aceito digitalmente em:</strong> {data_hoje}</p>
        <p><strong>Data/hora ISO:</strong> {data_iso}</p>
        <p><strong>IP do aceite:</strong> [IP_SERÁ_REGISTRADO_NO_ACEITE]</p>
        <p><strong>Identificador do aceite:</strong> [ID_ACEITE]</p>
    </div>
    
    <p style="text-align: center; margin: 40px 0;">
        E, por estarem assim justos e contratados, as partes aceitam os termos deste instrumento.
    </p>
    
    <div class="assinatura">
        <div style="display: flex; justify-content: space-between; margin-top: 80px;">
            <div style="text-align: center; width: 45%;">
                <div class="linha"></div>
                <p><strong>{EMPRESA['razao_social']}</strong></p>
                <p>CNPJ: {EMPRESA['cnpj']}</p>
                <p style="margin-top: 10px;">{EMPRESA['representante']['nome']}</p>
                <p>{EMPRESA['representante']['cargo']}</p>
                <p>CPF: {EMPRESA['representante']['cpf']}</p>
            </div>
            
            <div style="text-align: center; width: 45%;">
                <div class="linha"></div>
                <p><strong>{corretor.nome.upper()}</strong></p>
                <p>CPF: {cpf_formatado}</p>
                <p>CRECI: {corretor.creci_numero}/{corretor.creci_uf}</p>
            </div>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    return {
        "success": True,
        "content_html": contrato_html,
        "dados_empresa": EMPRESA,
        "corretor": {
            "nome": corretor.nome,
            "cpf": cpf_formatado,
            "creci": f"{corretor.creci_numero}/{corretor.creci_uf}",
            "endereco": corretor.endereco
        },
        "data_geracao": data_iso,
        "assinatura_url": None,
        "texto_aceite": "Para aceitar este contrato, digite ACEITO"
    }


def get_contract_text_plain(corretor: CorretorData) -> str:
    """Retorna texto do contrato em formato plano (para WhatsApp/email)"""
    return f"""
📄 CONTRATO DE PARCERIA COMERCIAL

CONTRATANTE: {EMPRESA['razao_social']}
CNPJ: {EMPRESA['cnpj']}

PARCEIRO: {corretor.nome}
CPF: {corretor.cpf}
CRECI: {corretor.creci_numero}/{corretor.creci_uf}

RESUMO:
• Comissão variável definida por operação
• Pagamento via split Asaas
• Vigência indeterminada
• Rescisão com 30 dias de aviso
• Foro: {EMPRESA['foro']}

✅ Para aceitar, digite: ACEITO
""".strip()
