"""
Modelos para gestão de documentos (modelos de contratos, escrituras, procurações)
"""
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import enum


class TipoModelo(str, enum.Enum):
    CONTRATO_PARCEIRO = "contrato_parceiro"
    ESCRITURA = "escritura"
    PROCURACAO = "procuracao"
    OUTROS = "outros"


class ModeloDocumento(Base):
    """Modelos de documentos (contratos, escrituras, procurações)"""
    __tablename__ = "modelos_documentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tipo = Column(Enum(TipoModelo), nullable=False, default=TipoModelo.OUTROS)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    
    # Se cartorio_id for NULL, é um modelo global (disponível para todos)
    cartorio_id = Column(UUID(as_uuid=True), ForeignKey("cartorios.id"), nullable=True)
    
    arquivo_path = Column(String(500), nullable=False)  # Caminho do arquivo no storage
    versao_atual = Column(Integer, default=1)
    ativo = Column(Boolean, default=True)
    
    # Metadados extraídos do documento (placeholders, campos, etc.)
    metadados = Column(JSON, default=dict)
    
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    criado_por = Column(String(100), nullable=True)  # ID do usuário que criou


class VersaoModelo(Base):
    """Histórico de versões dos modelos"""
    __tablename__ = "versoes_modelos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    modelo_id = Column(UUID(as_uuid=True), ForeignKey("modelos_documentos.id"), nullable=False)
    
    arquivo_path = Column(String(500), nullable=False)
    versao = Column(Integer, nullable=False)
    motivo_alteracao = Column(Text, nullable=True)
    
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    criado_por = Column(String(100), nullable=True)


class Cartorio(Base):
    """Cartórios parceiros (referência para FK)"""
    __tablename__ = "cartorios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(18), nullable=True)
    ativo = Column(Boolean, default=True)
    
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
