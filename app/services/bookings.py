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
    expires_at: datetime,
) -> Booking:
    booking.status = "email_sent"
    booking.confirm_token_hash = token_hash
    booking.confirm_token_expires_at = expires_at
    db.commit()
    db.refresh(booking)
    return booking