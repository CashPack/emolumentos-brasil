"""
Modelo para Cadastro de Corretores (Módulo 0) - Fluxo Definitivo
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.base import Base


class Corretor(Base):
    """Cadastro de corretores parceiros - Fluxo Definitivo"""
    __tablename__ = "corretores"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identificação
    cadastro_id = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    
    # Dados Pessoais (extraídos do OCR ou informados)
    nome = Column(String, nullable=True)
    cpf = Column(String, nullable=True)
    data_nascimento = Column(String, nullable=True)
    
    # CRECI
    creci_numero = Column(String, nullable=True)
    creci_uf = Column(String, nullable=True)
    creci_validado = Column(Boolean, default=False)
    
    # Endereço (completo e estruturado)
    endereco_logradouro = Column(String, nullable=True)
    endereco_numero = Column(String, nullable=True)
    endereco_complemento = Column(String, nullable=True)
    endereco_bairro = Column(String, nullable=True)
    endereco_cep = Column(String, nullable=True)
    endereco_cidade = Column(String, nullable=True)
    endereco_uf = Column(String, nullable=True)
    endereco_completo = Column(String, nullable=True)  # Texto completo para exibição
    
    # Estado Civil
    estado_civil = Column(String, nullable=True)  # solteiro, casado, divorciado, viuvo
    
    # Contato
    email = Column(String, nullable=True)
    
    # Documentos temporários (URLs)
    temp_doc1_url = Column(String, nullable=True)  # RG ou CNH
    temp_doc2_url = Column(String, nullable=True)  # CRECI
    temp_doc3_url = Column(String, nullable=True)  # Comprovante (se opção 2 escolhida)
    
    # Dados extraídos do OCR (JSON)
    dados_extraidos = Column(Text, nullable=True)
    pendencias = Column(Text, nullable=True)  # JSON array de pendências
    
    # Asaas
    asaas_customer_id = Column(String, nullable=True)
    asaas_wallet_id = Column(String, nullable=True)
    
    # Contrato
    contrato_gerado = Column(Boolean, default=False)
    contrato_url = Column(String, nullable=True)
    contrato_pdf_path = Column(String, nullable=True)
    
    # Aceite do contrato (simplificado)
    contrato_aceito = Column(Boolean, default=False)
    contrato_aceito_em = Column(DateTime(timezone=True), nullable=True)
    contrato_aceito_ip = Column(String, nullable=True)
    
    # Status do cadastro (fluxo definitivo)
    status = Column(String, default="aguardando_doc1")
    # Estados:
    # aguardando_doc1 - Aguardando RG ou CNH
    # aguardando_doc2 - Aguardando CRECI
    # aguardando_escolha_endereco - Perguntando preferência de endereço
    # aguardando_endereco_digitado - Aguardando digitação do endereço
    # aguardando_comprovante - Aguardando foto do comprovante
    # aguardando_estado_civil - Aguardando estado civil
    # processando - OCR em lote
    # aguardando_correcoes - Aguardando correções de pendências
    # aguardando_email - Aguardando email
    # criando_asaas - Criando conta
    # gerando_contrato - Gerando PDF
    # aguardando_aceite - Aguardando digitar ACEITO
    # ativo - Cadastro completo
    # creci_invalido, erro_asaas - Estados de erro
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ativo_desde = Column(DateTime(timezone=True), nullable=True)

    def is_ativo(self):
        """Verifica se cadastro está ativo"""
        return self.status == "ativo" and self.contrato_aceito

    def get_endereco_completo(self):
        """Retorna endereço formatado"""
        partes = [
            self.endereco_logradouro,
            self.endereco_numero,
            self.endereco_complemento,
            self.endereco_bairro,
            self.endereco_cidade,
            self.endereco_uf,
            self.endereco_cep
        ]
        return ", ".join(filter(None, partes))
