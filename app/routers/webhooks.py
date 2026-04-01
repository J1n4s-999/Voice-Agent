from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    BookingRequest,
    BookingResponse,
    GenericMessageResponse,
    SendConfirmationRequest,
)
from app.services.bookings import create_booking, get_booking_by_id

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/request-booking", response_model=BookingResponse)
def request_booking(payload: BookingRequest, db: Session = Depends(get_db)):
    booking = create_booking(db, payload)
    return BookingResponse(
        ok=True,
        booking_id=booking.id,
        status=booking.status,
        message="Booking wurde als pending gespeichert.",
    )


@router.post("/send-confirmation", response_model=GenericMessageResponse)
def send_confirmation(payload: SendConfirmationRequest, db: Session = Depends(get_db)):
    booking = get_booking_by_id(db, payload.booking_id)

    if not booking:
        return GenericMessageResponse(
            ok=False,
            message="Booking nicht gefunden.",
        )

    return GenericMessageResponse(
        ok=True,
        message=f"Bestätigung kann für Booking {booking.id} vorbereitet werden.",
    )