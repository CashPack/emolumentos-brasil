from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.emoluments import EmolumentBracket, EmolumentTable, TableStatus
from app.models.user import User
from app.routers.deps import get_current_user
from app.services.xlsx_v5_parser import parse_v5_xlsx

router = APIRouter(prefix="/emoluments", tags=["emoluments"])


@router.get("/tables")
def list_tables(uf: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(EmolumentTable)
    if uf:
        q = q.filter(EmolumentTable.uf == uf.upper())
    if status:
        q = q.filter(EmolumentTable.status == status)
    q = q.order_by(EmolumentTable.uf.asc(), EmolumentTable.year.desc(), EmolumentTable.created_at.desc())
    return [
        {
            "id": t.id,
            "uf": t.uf,
            "year": t.year,
            "status": t.status,
            "source_name": t.source_name,
            "source_hash": t.source_hash,
            "created_at": t.created_at,
        }
        for t in q.limit(500).all()
    ]


@router.get("/tables/{table_id}/brackets")
def list_brackets(table_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = db.query(EmolumentTable).filter(EmolumentTable.id == table_id).first()
    if not t:
        raise HTTPException(404, "table_not_found")
    bs = db.query(EmolumentBracket).filter(EmolumentBracket.table_id == table_id, EmolumentBracket.active == True).order_by(EmolumentBracket.range_from.asc()).all()
    return [
        {
            "id": b.id,
            "range_from": float(b.range_from),
            "range_to": float(b.range_to),
            "amount": float(b.amount),
            "active": b.active,
        }
        for b in bs
    ]


@router.put("/brackets/{bracket_id}")
def update_bracket(bracket_id: str, payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    b = db.query(EmolumentBracket).filter(EmolumentBracket.id == bracket_id).first()
    if not b:
        raise HTTPException(404, "bracket_not_found")
    for k in ("range_from", "range_to", "amount", "active"):
        if k in payload:
            setattr(b, k, payload[k])
    db.add(b)
    db.commit()
    return {"ok": True}


@router.post("/import/v5")
def import_v5(
    year: int = 2026,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(400, "file_must_be_xlsx")
    content = file.file.read()
    file_hash, by_uf = parse_v5_xlsx(content)
    if len(by_uf) < 27:
        # Aceita menos se a planilha mudar, mas alerta
        raise HTTPException(400, f"ufs_parsed={len(by_uf)} (expected 27)")

    # archive previous active tables for that year
    db.query(EmolumentTable).filter(EmolumentTable.year == year, EmolumentTable.status == TableStatus.active).update({EmolumentTable.status: TableStatus.archived})

    created = 0
    for uf, brackets in by_uf.items():
        t = EmolumentTable(
            uf=uf,
            year=year,
            valid_from=date(year, 1, 1),
            valid_to=None,
            source_name=file.filename,
            source_hash=file_hash,
            status=TableStatus.active,
            created_by=user.id,
        )
        for i, br in enumerate(brackets):
            t.brackets.append(
                EmolumentBracket(
                    range_from=br.range_from,
                    range_to=br.range_to,
                    amount=br.amount,
                    sort_order=i,
                    active=True,
                )
            )
        db.add(t)
        created += 1

    db.commit()
    return {"ok": True, "tables_created": created, "source_hash": file_hash}
