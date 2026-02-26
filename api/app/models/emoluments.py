import enum
import uuid
from datetime import datetime, date

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class TableStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    archived = "archived"


class EmolumentTable(Base):
    __tablename__ = "emolument_tables"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    uf = Column(String(2), index=True, nullable=False)
    year = Column(Integer, nullable=False)
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    source_name = Column(Text, nullable=True)
    source_hash = Column(Text, nullable=True)
    status = Column(Enum(TableStatus), nullable=False, default=TableStatus.draft)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    brackets = relationship("EmolumentBracket", back_populates="table", cascade="all, delete-orphan")


class EmolumentBracket(Base):
    __tablename__ = "emolument_brackets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    table_id = Column(String, ForeignKey("emolument_tables.id"), index=True, nullable=False)
    range_from = Column(Numeric(14, 2), nullable=False)
    range_to = Column(Numeric(14, 2), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    sort_order = Column(Integer, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    table = relationship("EmolumentTable", back_populates="brackets")
