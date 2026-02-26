from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import emoluments as crud
from app.db.session import get_db
from app.models.emoluments import EmolumentBracket, EmolumentTable
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.emoluments import EmolumentBracketCreate, EmolumentBracketOut, EmolumentTableCreate, EmolumentTableOut

router = APIRouter(prefix="/admin/emoluments", tags=["emoluments-admin"])


@router.post("/tables", response_model=EmolumentTableOut)
def create_table(payload: EmolumentTableCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = crud.create_table(
        db,
        uf=payload.uf,
        year=payload.year,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        source_name=payload.source_name,
        created_by=user.id,
    )
    return EmolumentTableOut.model_validate(t, from_attributes=True)


@router.post("/tables/{table_id}/activate", response_model=EmolumentTableOut)
def activate_table(table_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = crud.activate_table(db, table_id=table_id)
    return EmolumentTableOut.model_validate(t, from_attributes=True)


@router.post("/tables/{table_id}/archive", response_model=EmolumentTableOut)
def archive_table(table_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = crud.archive_table(db, table_id=table_id)
    return EmolumentTableOut.model_validate(t, from_attributes=True)


@router.post("/tables/{table_id}/brackets", response_model=EmolumentBracketOut)
def add_bracket(table_id: str, payload: EmolumentBracketCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    b = crud.add_bracket(
        db,
        table_id=table_id,
        range_from=payload.range_from,
        range_to=payload.range_to,
        amount=payload.amount,
        sort_order=payload.sort_order,
    )
    return EmolumentBracketOut(
        id=b.id,
        table_id=b.table_id,
        range_from=float(b.range_from),
        range_to=float(b.range_to),
        amount=float(b.amount),
        sort_order=b.sort_order,
        active=b.active,
    )
