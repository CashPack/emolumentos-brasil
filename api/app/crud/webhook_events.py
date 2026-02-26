from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.webhook_event import WebhookEvent


def record_event(db: Session, *, provider: str, external_id: str, raw: str | None = None) -> bool:
    """Return True when recorded (new). False when duplicate."""
    ev = WebhookEvent(provider=provider, external_id=external_id, raw=raw)
    db.add(ev)
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False
