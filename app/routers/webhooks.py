from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.schemas import (
    BookingRequest,
    BookingResponse,
    GenericMessageResponse,
    SendConfirmationRequest,
    SendConfirmationResponse,
)
from app.security import (
    generate_confirmation_token,
    get_token_expiry,
    hash_token,
)
from app.services.bookings import (
    create_booking,
    get_booking_by_id,
    mark_confirmation_sent,
)

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


@router.post("/send-confirmation", response_model=SendConfirmationResponse)
def send_confirmation(payload: SendConfirmationRequest, db: Session = Depends(get_db)):
    booking = get_booking_by_id(db, payload.booking_id)

    if not booking:
        return SendConfirmationResponse(
            ok=False,
            booking_id="",
            status="not_found",
            confirm_link="",
            expires_at=get_token_expiry(),
        )

    token = generate_confirmation_token(booking.id)
    token_hash = hash_token(token)
    expires_at = get_token_expiry()

    booking = mark_confirmation_sent(
        db=db,
        booking=booking,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    confirm_link = f"{settings.public_base_url}/confirm/{token}"

    return SendConfirmationResponse(
        ok=True,
        booking_id=booking.id,
        status=booking.status,
        confirm_link=confirm_link,
        expires_at=expires_at,
    )