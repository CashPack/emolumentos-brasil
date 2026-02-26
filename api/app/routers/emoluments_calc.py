from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.emoluments import EmolumentBracket, EmolumentTable, TableStatus

router = APIRouter(prefix="/calc", tags=["calc"])


@router.get("/deed")
def calc_deed(uf: str, property_value: float, db: Session = Depends(get_db)):
    uf = uf.strip().upper()
    t = (
        db.query(EmolumentTable)
        .filter(EmolumentTable.uf == uf, EmolumentTable.status == TableStatus.active)
        .order_by(EmolumentTable.year.desc(), EmolumentTable.created_at.desc())
        .first()
    )
    if not t:
        raise HTTPException(404, "active_table_not_found")

    bs = (
        db.query(EmolumentBracket)
        .filter(EmolumentBracket.table_id == t.id, EmolumentBracket.active == True)
        .order_by(EmolumentBracket.range_from.asc())
        .all()
    )
    for b in bs:
        if float(b.range_from) <= property_value <= float(b.range_to):
            return {
                "uf": uf,
                "year": t.year,
                "property_value": property_value,
                "emolumento": float(b.amount),
                "faixa": {"de": float(b.range_from), "ate": float(b.range_to)},
                "table_id": t.id,
            }

    # fallback: above last range
    if bs and property_value > float(bs[-1].range_to):
        b = bs[-1]
        return {
            "uf": uf,
            "year": t.year,
            "property_value": property_value,
            "emolumento": float(b.amount),
            "faixa": {"de": float(b.range_from), "ate": float(b.range_to)},
            "table_id": t.id,
            "observacao": "Valor acima do teto da tabela; usando última faixa.",
        }

    raise HTTPException(400, "no_bracket_for_value")


@router.get("/deed-economy")
def calc_deed_economy(uf: str, property_value: float, db: Session = Depends(get_db)):
    """Retorna economia vs menor emolumento entre UFs para o mesmo valor."""
    base = calc_deed(uf=uf, property_value=property_value, db=db)

    # find min across all active tables
    from app.models.emoluments import EmolumentTable, EmolumentBracket, TableStatus

    tables = (
        db.query(EmolumentTable)
        .filter(EmolumentTable.status == TableStatus.active)
        .order_by(EmolumentTable.uf.asc())
        .all()
    )

    best = None
    for t in tables:
        bs = (
            db.query(EmolumentBracket)
            .filter(EmolumentBracket.table_id == t.id, EmolumentBracket.active == True)
            .order_by(EmolumentBracket.range_from.asc())
            .all()
        )
        for b in bs:
            if float(b.range_from) <= property_value <= float(b.range_to):
                cand = {
                    "uf": t.uf,
                    "emolumento": float(b.amount),
                    "faixa": {"de": float(b.range_from), "ate": float(b.range_to)},
                    "table_id": t.id,
                }
                if best is None or cand["emolumento"] < best["emolumento"]:
                    best = cand
                break
        else:
            # fallback: above last range
            if bs and property_value > float(bs[-1].range_to):
                cand = {
                    "uf": t.uf,
                    "emolumento": float(bs[-1].amount),
                    "faixa": {"de": float(bs[-1].range_from), "ate": float(bs[-1].range_to)},
                    "table_id": t.id,
                    "observacao": "Valor acima do teto da tabela; usando última faixa.",
                }
                if best is None or cand["emolumento"] < best["emolumento"]:
                    best = cand

    if not best:
        raise HTTPException(500, "no_active_tables")

    economia = round(float(base["emolumento"]) - float(best["emolumento"]), 2)
    return {
        "input": {"uf": uf.strip().upper(), "property_value": property_value},
        "local": base,
        "best": best,
        "economia": economia,
        "economia_pct": (round((economia / float(base["emolumento"])) * 100, 2) if float(base["emolumento"]) else 0),
    }
