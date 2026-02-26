from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginJson(BaseModel):
    # aceita tanto username quanto email (o front pode mandar um ou outro)
    username: str | None = None
    email: str | None = None
    password: str


@router.post("/login")
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login padrão OAuth2 (application/x-www-form-urlencoded).

    Use este endpoint quando o client usa o fluxo OAuth2PasswordBearer.
    """
    identifier = form.username.strip().lower()
    user = db.query(User).filter(User.email == identifier).first()
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    if not verify_password(form.password.strip(), user.password_hash):
        raise HTTPException(status_code=401, detail="invalid_credentials")
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login-json")
def login_json(body: LoginJson, db: Session = Depends(get_db)):
    """Login via JSON (application/json).

    Exemplo:
      {"email":"...","password":"..."}
    ou
      {"username":"...","password":"..."}
    """
    identifier = (body.email or body.username or "").strip().lower()
    if not identifier:
        raise HTTPException(status_code=400, detail="missing_identifier")

    user = db.query(User).filter(User.email == identifier).first()
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="invalid_credentials")
    ok = verify_password(body.password.strip(), user.password_hash)
    if not ok:
        # debug temporário (sem vazar senha): comprimento e prefixo do hash
        print(
            f"[auth] login-json mismatch user={user.email} active={user.active} "
            f"pwd_len={len(body.password)} hash_prefix={user.password_hash[:10]}"
        )
        raise HTTPException(status_code=401, detail="invalid_credentials")

    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}
