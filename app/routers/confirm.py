from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from itsdangerous import BadSignature, SignatureExpired
from sqlalchemy.orm import Session

from app.db import get_db
from app.security import serializer, hash_token
from app.services.bookings import get_booking_by_id, mark_booking_confirmed
from app.services.google_calendar import create_event

router = APIRouter(tags=["confirm"])

BERLIN_TZ = ZoneInfo("Europe/Berlin")


def html_page(title: str, message: str) -> HTMLResponse:
    return HTMLResponse(
        f"""
        <html>
          <head>
            <meta charset="utf-8">
            <title>{title}</title>
          </head>
          <body style="font-family: Arial, Helvetica, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; color: #111827;">
            <h1>{title}</h1>
            <p>{message}</p>
          </body>
        </html>
        """
    )


@router.get("/confirm/{token}", response_class=HTMLResponse)
def confirm_booking(token: str, db: Session = Depends(get_db)):
    try:
        data = serializer.loads(token)
    except SignatureExpired:
        return html_page(
            "Link abgelaufen",
            "Dieser Bestätigungslink ist leider abgelaufen.",
        )
    except BadSignature:
        return html_page(
            "Ungültiger Link",
            "Dieser Bestätigungslink ist ungültig.",
        )

    booking_id = data.get("booking_id")
    if not booking_id:
        return html_page(
            "Ungültiger Link",
            "Im Bestätigungslink fehlt die Buchungs-ID.",
        )

    booking = get_booking_by_id(db, booking_id)
    if not booking:
        return html_page(
            "Booking nicht gefunden",
            "Zu diesem Link konnte keine Buchung gefunden werden.",
        )

    token_hash = hash_token(token)

    if not booking.confirmation_token_hash:
        return html_page(
            "Ungültiger Link",
            "Für diese Buchung wurde kein gültiger Bestätigungslink gespeichert.",
        )

    if booking.confirmation_token_hash != token_hash:
        return html_page(
            "Ungültiger Link",
            "Der Token stimmt nicht mit dem gespeicherten Booking überein.",
        )

    if booking.confirmation_expires_at:
        now = datetime.now(BERLIN_TZ)
        expires_at = booking.confirmation_expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=BERLIN_TZ)
        else:
            expires_at = expires_at.astimezone(BERLIN_TZ)

        if now > expires_at:
            return html_page(
                "Link abgelaufen",
                "Dieser Bestätigungslink ist leider abgelaufen.",
            )

    if booking.status == "confirmed":
        return html_page(
            "Bereits bestätigt",
            "Dieser Termin wurde bereits bestätigt.",
        )

    try:
        event_id, meet_link = create_event(booking)
    except Exception as e:
        print("GOOGLE CALENDAR ERROR:", repr(e))
        return html_page(
            "Google Calendar Fehler",
            f"Der Termin konnte nicht im Kalender erstellt werden: {e}",
        )

    booking = mark_booking_confirmed(
        db=db,
        booking=booking,
        calendar_event_id=event_id,
    )

    meet_html = ""
    if meet_link:
        meet_html = f'<p><strong>Meet-Link:</strong> <a href="{meet_link}">{meet_link}</a></p>'

    return HTMLResponse(
        f"""
        <html>
          <head>
            <meta charset="utf-8">
            <title>Termin bestätigt</title>
          </head>
          <body style="font-family: Arial, Helvetica, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; color: #111827;">
            <h1>Termin bestätigt</h1>
            <p>Danke {booking.name}, dein Termin wurde erfolgreich bestätigt.</p>
            <p><strong>E-Mail:</strong> {booking.email}</p>
            <p><strong>Status:</strong> {booking.status}</p>
            <p><strong>Kalender-Event-ID:</strong> {event_id}</p>
            {meet_html}
          </body>
        </html>
        """
    )