from sqlalchemy.orm import Session

from app.core.config import SEED_ADMIN_EMAIL, SEED_ADMIN_NAME, SEED_ADMIN_PASSWORD
from app.core.security import hash_password
from app.models.user import User, UserRole


def ensure_admin(db: Session) -> dict:
    """Garante que existe um usuário admin seedado.

    MVP-friendly: se o usuário já existir, atualiza nome e senha conforme ENV.
    Isso evita ficar travado quando o seed inicial rodou com valores antigos.
    """
    email = (SEED_ADMIN_EMAIL or "").strip().lower()
    if not email:
        return {"created": False, "updated": False, "reason": "missing_seed_email"}

    user = db.query(User).filter(User.email == email).first()
    if user:
        user.name = SEED_ADMIN_NAME
        user.password_hash = hash_password(SEED_ADMIN_PASSWORD)
        user.role = UserRole.admin
        user.active = True
        db.add(user)
        db.commit()
        return {"created": False, "updated": True, "email": user.email}

    user = User(
        name=SEED_ADMIN_NAME,
        email=email,
        password_hash=hash_password(SEED_ADMIN_PASSWORD),
        role=UserRole.admin,
        active=True,
    )
    db.add(user)
    db.commit()
    return {"created": True, "updated": False, "email": user.email}
