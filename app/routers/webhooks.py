from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

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
import logging
logger = logging.getLogger(__name__)

def get_tenant_id_by_agent_key(db: Session, agent_key: str) -> str:
    tenant = db.execute(
        text("SELECT id FROM tenants WHERE agent_key = :agent_key"),
        {"agent_key": agent_key},
    ).fetchone()

    if not tenant:
        raise HTTPException(status_code=400, detail="Invalid agent_key")

    return tenant[0]

BERLIN_TZ = ZoneInfo("Europe/Berlin")

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def build_requested_start(payload: BookingRequest) -> datetime:
    now = datetime.now(BERLIN_TZ)

    try:
        candidate = datetime(
            year=now.year,
            month=payload.month,
            day=payload.day,
            hour=payload.hour,
            minute=payload.minute,
            tzinfo=BERLIN_TZ,
        )

        if candidate < now:
            candidate = datetime(
                year=now.year + 1,
                month=payload.month,
                day=payload.day,
                hour=payload.hour,
                minute=payload.minute,
                tzinfo=BERLIN_TZ,
            )

        return candidate

    except ValueError as e:
        raise ValueError(f"Ungültiges Datum/Uhrzeit: {e}") from e


@router.post("/request-booking", response_model=BookingAttemptResponse)
def request_booking(payload: BookingRequest, db: Session = Depends(get_db)):
    logger.info("Booking request received with agent_key=%s", payload.agent_key)

    tenant_id = get_tenant_id_by_agent_key(db, payload.agent_key)

    logger.info(
        "Resolved agent_key=%s to tenant_id=%s",
        payload.agent_key,
        tenant_id,
    )

    try:
        requested_start = build_requested_start(payload)
    except ValueError:
        logger.warning(
            "Invalid date/time for agent_key=%s: day=%s month=%s hour=%s minute=%s",
            payload.agent_key,
            payload.day,
            payload.month,
            payload.hour,
            payload.minute,
        )

        return BookingAttemptResponse(
            ok=False,
            booking_id=None,
            status="rejected",
            message="Datum oder Uhrzeit konnten nicht korrekt verarbeitet werden.",
            conflict_source=None,
            alternatives=[],
            spoken_text="Ich konnte das Datum oder die Uhrzeit leider nicht korrekt verstehen. Bitte nenne beides noch einmal.",
        )

    logger.info(
        "Parsed requested_start=%s for tenant_id=%s",
        requested_start.isoformat(),
        tenant_id,
    )

    availability = check_availability_payload(
        db=db,
        requested_start=requested_start,
        duration_minutes=payload.duration_minutes,
        alternative_count=3,
        slot_interval_minutes=30,
    )

    logger.info(
        "Availability result for tenant_id=%s requested_start=%s available=%s",
        tenant_id,
        requested_start.isoformat(),
        availability.get("available"),
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
        tenant_id=tenant_id,
    )

    logger.info(
        "Created booking id=%s tenant_id=%s status=%s",
        booking.id,
        tenant_id,
        booking.status,
    )

    return BookingAttemptResponse(
        ok=True,
        booking_id=booking.id,
        status=booking.status,
        message="Booking wurde als pending gespeichert.",
        conflict_source=None,
        alternatives=[],
        spoken_text="Ja, der Termin ist frei. Ich habe ihn vorgemerkt.",
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