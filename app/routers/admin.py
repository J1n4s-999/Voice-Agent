from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Booking

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_secret: str | None = Header(default=None)):
    if not x_admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/bookings")
def list_bookings(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    bookings = (
        db.query(Booking)
        .order_by(Booking.requested_start.desc())
        .all()
    )

    return [
        {
            "id": b.id,
            "name": b.name,
            "email": b.email,
            "requested_start": b.requested_start.isoformat() if b.requested_start else None,
            "duration_minutes": b.duration_minutes,
            "status": b.status,
            "calendar_event_id": b.calendar_event_id,
            "created_at": b.created_at.isoformat() if getattr(b, "created_at", None) else None,
        }
        for b in bookings
    ]