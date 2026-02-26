import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_whatsapp = Column(String, nullable=True)

    asaas_customer_id = Column(String, nullable=True)
    asaas_charge_id = Column(String, nullable=True)

    rmchat_conversation_id = Column(String, nullable=True)

    status = Column(String, nullable=False, default="LEAD_NOVO")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
