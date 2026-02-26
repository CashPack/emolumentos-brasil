from fastapi import APIRouter, Depends

from app.models.user import User
from app.routers.deps import get_current_user

router = APIRouter(tags=["users"])


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "active": user.active}
