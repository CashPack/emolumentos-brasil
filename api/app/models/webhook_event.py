import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text, UniqueConstraint

from app.db.base import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider = Column(String, nullable=False)  # asaas|rmchat
    external_id = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    raw = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_webhook_provider_external_id"),
    )
