"""
Modelo para Cadastro de Corretores (Módulo 0)
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.base import Base


class Corretor(Base):
    """Cadastro de corretores parceiros"""
    __tablename__ = "corretores"

    id = Column(Integer, primary_key=True, index=True)
    
    # Identificação
    cadastro_id = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)
    
    # Dados Pessoais
    nome = Column(String, nullable=True)
    cpf = Column(String, nullable=True)
    data_nascimento = Column(String, nullable=True)
    
    # CRECI
    creci_numero = Column(String, nullable=True)
    creci_uf = Column(String, nullable=True)
    creci_validado = Column(Boolean, default=False)
    
    # Endereço
    email = Column(String, nullable=True)
    
    # Documentos - RG/CNH
    doc_rg_url = Column(String, nullable=True)
    doc_rg_status = Column(String, default="pendente")  # pendente, recebido, processado, erro
    doc_rg_data = Column(Text, nullable=True)  # JSON string
    
    # Documentos - CRECI
    doc_creci_url = Column(String, nullable=True)
    doc_creci_status = Column(String, default="pendente")
    doc_creci_data = Column(Text, nullable=True)
    
    # Documentos - Comprovante
    doc_comprovante_url = Column(String, nullable=True)
    doc_comprovante_status = Column(String, default="pendente")
    doc_comprovante_data = Column(Text, nullable=True)
    
    # Dados temporários extraídos do OCR
    nome_temp = Column(String, nullable=True)
    cpf_temp = Column(String, nullable=True)
    creci_numero_temp = Column(String, nullable=True)
    creci_uf_temp = Column(String, nullable=True)
    
    # Asaas
    asaas_customer_id = Column(String, nullable=True)
    asaas_wallet_id = Column(String, nullable=True)
    
    # Campos para fluxo guiado (Doc1 → Doc2 → Doc3 → Endereço)
    temp_doc1_url = Column(String, nullable=True)  # RG/CNH
    temp_doc2_url = Column(String, nullable=True)  # CRECI
    temp_doc3_url = Column(String, nullable=True)  # Comprovante
    endereco = Column(String, nullable=True)
    endereco_fonte = Column(String, nullable=True)  # 'digitado' ou 'ocr'
    all_docs_received_at = Column(DateTime(timezone=True), nullable=True)
    
    # Dados extraídos do OCR (JSON)
    dados_extraidos = Column(Text, nullable=True)
    
    # Status do cadastro
    status = Column(String, default="aguardando_doc1")
    # aguardando_doc1, aguardando_doc2, aguardando_doc3, aguardando_endereco,
    # processando, aguardando_correcoes, validando_creci, creci_invalido,
    # criando_asaas, gerando_contrato, aguardando_assinatura, ativo, erro_asaas
    
    # Contrato
    contrato_gerado = Column(Boolean, default=False)
    contrato_url = Column(String, nullable=True)
    contrato_assinado = Column(Boolean, default=False)
    contrato_assinado_at = Column(DateTime(timezone=True), nullable=True)
    
    # Campos para fluxo otimizado de coleta única
    last_document_received_at = Column(DateTime(timezone=True), nullable=True)
    temp_documents = Column(Text, nullable=True)  # JSON array de documentos acumulados
    dados_extraidos = Column(Text, nullable=True)  # JSON com dados do OCR
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ativo_desde = Column(DateTime(timezone=True), nullable=True)

    def is_complete(self):
        """Verifica se cadastro está completo"""
        return (
            self.nome and
            self.cpf and
            self.creci_validado and
            self.asaas_wallet_id and
            self.contrato_assinado
        )


class DocumentStatus:
    PENDENTE = "pendente"
    RECEBIDO = "recebido"
    PROCESSADO = "processado"
    ERRO = "erro"
