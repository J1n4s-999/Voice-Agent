import traceback

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from itsdangerous import BadSignature, SignatureExpired
from sqlalchemy.orm import Session

from app.db import get_db
from app.security import hash_token, verify_confirmation_token
from app.services.bookings import get_booking_by_id, mark_booking_confirmed
from app.services.google_calendar import create_event

router = APIRouter(tags=["confirm"])


@router.get("/confirm/{token}", response_class=HTMLResponse)
def confirm_booking(token: str, db: Session = Depends(get_db)):
    try:
        booking_id = verify_confirmation_token(token)
    except SignatureExpired:
        return HTMLResponse(
            content="""
            <h1>Link abgelaufen</h1>
            <p>Der Bestätigungslink ist leider abgelaufen.</p>
            """,
            status_code=400,
        )
    except BadSignature:
        return HTMLResponse(
            content="""
            <h1>Ungültiger Link</h1>
            <p>Der Bestätigungslink ist ungültig.</p>
            """,
            status_code=400,
        )

    booking = get_booking_by_id(db, booking_id)

    if not booking:
        return HTMLResponse(
            content="""
            <h1>Booking nicht gefunden</h1>
            <p>Zu diesem Link konnte kein Termin gefunden werden.</p>
            """,
            status_code=404,
        )

    incoming_token_hash = hash_token(token)

    if booking.confirmation_token_hash != incoming_token_hash:
        return HTMLResponse(
            content="""
            <h1>Ungültiger Link</h1>
            <p>Der Token stimmt nicht mit dem gespeicherten Booking überein.</p>
            """,
            status_code=400,
        )

    if booking.token_used_at is not None:
        return HTMLResponse(
            content="""
            <h1>Bereits bestätigt</h1>
            <p>Dieser Termin wurde bereits bestätigt.</p>
            """,
            status_code=400,
        )

    try:
        event_id, meet_link = create_event(booking)

        booking.calendar_event_id = event_id
        booking.google_meet_link = meet_link
        db.add(booking)
        db.commit()
        db.refresh(booking)

    except Exception as e:
        print("GOOGLE CALENDAR ERROR:", repr(e))
        traceback.print_exc()
        return HTMLResponse(
            content=f"""
            <h1>Google Calendar Fehler</h1>
            <pre>{str(e)}</pre>
            """,
            status_code=500,
        )

    mark_booking_confirmed(db, booking)

    return HTMLResponse(
        content=f"""
        <h1>Termin bestätigt</h1>
        <p>Danke {booking.name}, dein Termin wurde erfolgreich bestätigt.</p>
        <p>E-Mail: {booking.email}</p>
        <p>Status: confirmed</p>
        <p>Kalender-Event-ID: {booking.calendar_event_id}</p>
        <p>Meet-Link: {booking.google_meet_link or 'Kein Meet-Link zurückgegeben'}</p>
        """,
        status_code=200,
    )