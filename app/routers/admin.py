from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Booking
from app.services.bookings import mark_booking_confirmed
from app.services.google_calendar import create_event

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(x_admin_secret: str | None = Header(default=None)):
    if not x_admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")


def cleanup_expired_pending_bookings(db: Session, tenant_id: str):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)

    expired = (
        db.query(Booking)
        .filter(Booking.tenant_id == tenant_id)
        .filter(Booking.status == "pending")
        .filter(Booking.created_at < cutoff)
        .all()
    )

    for booking in expired:
        db.delete(booking)

    db.commit()


@router.get("/bookings")
def list_bookings(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    cleanup_expired_pending_bookings(db, tenant_id)

    bookings = (
        db.query(Booking)
        .filter(Booking.tenant_id == tenant_id)
        .order_by(Booking.requested_start.desc())
        .all()
    )

    return [
        {
            "id": b.id,
            "tenant_id": b.tenant_id,
            "name": b.name,
            "email": b.email,
            "requested_start": b.requested_start.isoformat() if b.requested_start else None,
            "duration_minutes": b.duration_minutes,
            "status": b.status,
            "calendar_event_id": b.calendar_event_id,
            "google_meet_link": b.google_meet_link,
            "created_at": b.created_at.isoformat() if getattr(b, "created_at", None) else None,
        }
        for b in bookings
    ]


@router.delete("/bookings/{booking_id}")
def delete_booking(
    booking_id: str,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .filter(Booking.tenant_id == tenant_id)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    db.delete(booking)
    db.commit()

    return {"ok": True, "message": "Booking deleted"}


@router.post("/bookings/{booking_id}/confirm")
def confirm_booking_manually(
    booking_id: str,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .filter(Booking.tenant_id == tenant_id)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == "confirmed":
        return {
            "ok": True,
            "message": "Booking already confirmed",
            "calendar_event_id": booking.calendar_event_id,
            "meet_link": booking.google_meet_link,
        }

    event_id, meet_link = create_event(booking)

    booking.google_meet_link = meet_link

    booking = mark_booking_confirmed(
        db=db,
        booking=booking,
        calendar_event_id=event_id,
    )

    return {
        "ok": True,
        "message": "Booking confirmed",
        "booking_id": booking.id,
        "calendar_event_id": event_id,
        "meet_link": meet_link,
    }

from pydantic import BaseModel
from sqlalchemy import text
from app.security import verify_password


class AdminLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def admin_login(
    payload: AdminLoginRequest,
    db: Session = Depends(get_db),
):
    user = db.execute(
    text("""
        SELECT id, tenant_id, username, password_hash, role
        FROM admin_users
        WHERE username = :username
    """),
    {"username": payload.username},
    ).mappings().fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "ok": True,
        "user_id": user.id,
        "username": user.username,
        "tenant_id": user.tenant_id,
        "role": user.role,
    }