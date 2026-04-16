from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Booking


def create_booking(
    db: Session,
    *,
    name: str,
    email: str,
    requested_start: datetime,
    duration_minutes: int,
) -> Booking:
    booking = Booking(
        name=name.strip(),
        email=email.lower().strip(),
        requested_start=requested_start,
        duration_minutes=duration_minutes,
        status="pending",
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
    expires_at,
) -> Booking:
    booking.confirmation_token_hash = token_hash
    booking.confirmation_expires_at = expires_at
    booking.confirmation_sent_at = datetime.now(timezone.utc)
    booking.status = "email_sent"

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def mark_booking_confirmed(db: Session, booking: Booking) -> Booking:
    now = datetime.now(timezone.utc)
    booking.status = "confirmed"
    booking.confirmed_at = now
    booking.token_used_at = now

    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking