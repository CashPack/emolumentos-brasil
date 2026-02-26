from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import JWT_ALG, JWT_SECRET
from app.db.session import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        sub = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_token")

    if not sub:
        raise HTTPException(status_code=401, detail="invalid_token")

    user = db.query(User).filter(User.id == sub).first()
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="invalid_token")
    return user
