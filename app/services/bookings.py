from sqlalchemy.orm import Session

from app.models import Booking
from app.schemas import BookingRequest


def create_booking(db: Session, payload: BookingRequest) -> Booking:
    booking = Booking(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        requested_start=payload.requested_start,
        duration_minutes=payload.duration_minutes,
        status="pending",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking_by_id(db: Session, booking_id: str) -> Booking | None:
    return db.query(Booking).filter(Booking.id == booking_id).first()