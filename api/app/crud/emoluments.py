from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.emoluments import EmolumentBracket, EmolumentTable, TableStatus


def _uf(x: str) -> str:
    return (x or "").strip().upper()


def create_table(db: Session, *, uf: str, year: int, valid_from=None, valid_to=None, source_name=None, created_by=None) -> EmolumentTable:
    uf = _uf(uf)
    if len(uf) != 2:
        raise HTTPException(400, "invalid_uf")

    t = EmolumentTable(
        uf=uf,
        year=year,
        valid_from=valid_from,
        valid_to=valid_to,
        source_name=source_name,
        status=TableStatus.draft,
        created_by=created_by,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def add_bracket(db: Session, *, table_id: str, range_from: float, range_to: float, amount: float, sort_order=None) -> EmolumentBracket:
    if range_from > range_to:
        raise HTTPException(400, "range_from_gt_range_to")

    t = db.query(EmolumentTable).filter(EmolumentTable.id == table_id).first()
    if not t:
        raise HTTPException(404, "table_not_found")

    b = EmolumentBracket(
        table_id=table_id,
        range_from=range_from,
        range_to=range_to,
        amount=amount,
        sort_order=sort_order,
        active=True,
        updated_at=datetime.utcnow(),
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def activate_table(db: Session, *, table_id: str) -> EmolumentTable:
    t = db.query(EmolumentTable).filter(EmolumentTable.id == table_id).first()
    if not t:
        raise HTTPException(404, "table_not_found")

    # archive existing active for same uf/year
    db.query(EmolumentTable).filter(
        EmolumentTable.uf == t.uf,
        EmolumentTable.year == t.year,
        EmolumentTable.status == TableStatus.active,
    ).update({EmolumentTable.status: TableStatus.archived})

    t.status = TableStatus.active
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def archive_table(db: Session, *, table_id: str) -> EmolumentTable:
    t = db.query(EmolumentTable).filter(EmolumentTable.id == table_id).first()
    if not t:
        raise HTTPException(404, "table_not_found")
    t.status = TableStatus.archived
    db.add(t)
    db.commit()
    db.refresh(t)
    return t
