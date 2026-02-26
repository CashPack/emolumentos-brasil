import os


def getenv(name: str, default: str | None = None) -> str:
    v = os.environ.get(name, default)
    if v is None:
        raise RuntimeError(f"Missing env var: {name}")
    return v


DATABASE_URL = getenv("DATABASE_URL")
JWT_SECRET = getenv("JWT_SECRET", "dev-secret")
JWT_ALG = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

# Seed admin
SEED_ADMIN_EMAIL = (os.environ.get("SEED_ADMIN_EMAIL", "admin@pratico.local") or "").strip().lower()
SEED_ADMIN_PASSWORD = (os.environ.get("SEED_ADMIN_PASSWORD", "ChangeMe-Now-123") or "").strip()
SEED_ADMIN_NAME = (os.environ.get("SEED_ADMIN_NAME", "Admin") or "").strip()
