from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Booking


def create_booking(
    db: Session,
    *,
    name: str,
    email: str,
    requested_start: datetime,
    duration_minutes: int,
    tenant_id: str,
) -> Booking:
    booking = Booking(
        name=name.strip(),
        email=email.lower().strip(),
        requested_start=requested_start,
        duration_minutes=duration_minutes,
        status="pending",
        tenant_id=tenant_id,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking_by_id(db: Session, booking_id: str) -> Booking | None:
    return db.query(Booking).filter(Booking.id == booking_id).first()


def mark_confirmation_sent(
    db: Session,
    booking: Booking,
    token_hash: str,
    expires_at: datetime,
) -> Booking:
    booking.status = "email_sent"
    booking.confirmation_token_hash = token_hash
    booking.confirmation_expires_at = expires_at
    db.commit()
    db.refresh(booking)
    return booking


def mark_booking_confirmed(
    db: Session,
    booking: Booking,
    calendar_event_id: str | None = None,
) -> Booking:
    booking.status = "confirmed"
    booking.calendar_event_id = calendar_event_id
    booking.confirmation_token_hash = None
    booking.confirmation_expires_at = None
    db.commit()
    db.refresh(booking)
    return booking