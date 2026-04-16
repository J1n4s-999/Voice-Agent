from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings
from app.db import get_db
from app.schemas import (
    BookingAttemptResponse,
    BookingRequest,
    SendConfirmationRequest,
    SendConfirmationResponse,
)
from app.security import (
    generate_confirmation_token,
    get_token_expiry,
    hash_token,
)
from app.services.availability import check_availability_payload
from app.services.bookings import (
    create_booking,
    get_booking_by_id,
    mark_confirmation_sent,
)
from app.services.email import send_confirmation_email

BERLIN_TZ = ZoneInfo("Europe/Berlin")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/request-booking", response_model=BookingAttemptResponse)
def request_booking(payload: BookingRequest, db: Session = Depends(get_db)):
    try:
        requested_start = datetime.strptime(
            f"{payload.date} {payload.time}",
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=BERLIN_TZ)
    except ValueError:
        return BookingAttemptResponse(
            ok=False,
            booking_id=None,
            status="rejected",
            message="Datum oder Uhrzeit konnten nicht korrekt verarbeitet werden.",
            conflict_source=None,
            alternatives=[],
            spoken_text="Ich konnte das Datum oder die Uhrzeit leider nicht korrekt verstehen. Bitte nenne beides noch einmal."
        )

    availability = check_availability_payload(
        db=db,
        requested_start=requested_start,
        duration_minutes=payload.duration_minutes,
        alternative_count=3,
        slot_interval_minutes=30,
    )

    if not availability["available"]:
        return BookingAttemptResponse(
            ok=False,
            booking_id=None,
            status="rejected",
            message="Der gewünschte Termin ist nicht verfügbar.",
            conflict_source=availability.get("conflict_source"),
            alternatives=availability.get("alternatives", []),
            spoken_text=availability.get("spoken_text"),
        )

    booking = create_booking(
        db=db,
        name=payload.name,
        email=payload.email,
        requested_start=requested_start,
        duration_minutes=payload.duration_minutes,
    )

    return BookingAttemptResponse(
        ok=True,
        booking_id=booking.id,
        status=booking.status,
        message="Booking wurde als pending gespeichert.",
        conflict_source=None,
        alternatives=[],
        spoken_text="Ja, der Termin ist frei. Ich habe ihn vorgemerkt."
    )


@router.post("/send-confirmation", response_model=SendConfirmationResponse)
def send_confirmation(payload: SendConfirmationRequest, db: Session = Depends(get_db)):
    booking = get_booking_by_id(db, payload.booking_id)

    if not booking:
        raise HTTPException(status_code=404, detail="Booking nicht gefunden.")

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

    try:
        send_confirmation_email(
            to_email=booking.email,
            name=booking.name,
            requested_start=booking.requested_start,
            duration_minutes=booking.duration_minutes,
            confirm_link=confirm_link,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"E-Mail-Versand fehlgeschlagen: {e}")

    return SendConfirmationResponse(
        ok=True,
        booking_id=booking.id,
        status=booking.status,
        confirm_link=confirm_link,
        expires_at=expires_at,
    )