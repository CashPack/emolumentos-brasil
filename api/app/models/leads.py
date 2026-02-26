import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Numeric, String, Text

from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    profile = Column(String, nullable=True)  # broker|buyer|seller|other
    uf = Column(String(2), nullable=True)
    property_value = Column(Numeric(14, 2), nullable=True)
    message = Column(Text, nullable=True)
    consent = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
