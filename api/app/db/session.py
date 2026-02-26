from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL

# Render typically provides DATABASE_URL like "postgres://...".
# SQLAlchemy defaults to psycopg2 for "postgresql://" unless a driver is specified.
# We standardize to psycopg (v3) which we ship as dependency (psycopg[binary]).

def _normalize_db_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


engine = create_engine(_normalize_db_url(DATABASE_URL), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
