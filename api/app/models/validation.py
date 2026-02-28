"""
Modelo para validação de contatos (Módulo 3)
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base


class ContactValidation(Base):
    """Registro de validação de contato via WhatsApp"""
    __tablename__ = "contact_validations"

    id = Column(Integer, primary_key=True, index=True)
    validation_id = Column(String, unique=True, index=True, nullable=False)
    order_id = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    code = Column(String, nullable=False)  # Código de 4 dígitos
    status = Column(String, default="pending")  # pending, validated, expired, failed
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    webhook_received = Column(Boolean, default=False)
    webhook_data = Column(String, nullable=True)  # JSON string

    def is_expired(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now > expires

    def can_retry(self):
        return self.attempts < self.max_attempts and not self.is_expired()
