from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import text

from app.config import settings
from app.db import SessionLocal

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BERLIN_TZ = ZoneInfo("Europe/Berlin")


def to_berlin(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=BERLIN_TZ)
    return dt.astimezone(BERLIN_TZ)


def get_google_connection(tenant_id: str):
    db = SessionLocal()

    try:
        connection = (
            db.execute(
                text("""
                    SELECT google_calendar_id, refresh_token
                    FROM calendar_connections
                    WHERE tenant_id = :tenant_id
                      AND provider = 'google'
                    LIMIT 1
                """),
                {"tenant_id": tenant_id},
            )
            .mappings()
            .fetchone()
        )

        if not connection:
            raise Exception("Kein Google Kalender für diesen Kunden verbunden.")

        return {
            "google_calendar_id": connection["google_calendar_id"],
            "refresh_token": connection["refresh_token"],
        }

    finally:
        db.close()

def get_calendar_service(tenant_id: str):
    service, calendar_id = get_oauth_calendar_service(tenant_id)
    return service, calendar_id


def get_oauth_calendar_service(tenant_id: str):
    connection = get_google_connection(tenant_id)

    credentials = Credentials(
        token=None,
        refresh_token=connection["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_oauth_client_id,
        client_secret=settings.google_oauth_client_secret,
        scopes=SCOPES,
    )

    service = build("calendar", "v3", credentials=credentials)

    return service, connection["google_calendar_id"]


def create_event(booking):
    service, calendar_id = get_oauth_calendar_service(booking.tenant_id)

    start = to_berlin(booking.requested_start)
    end = start + timedelta(minutes=booking.duration_minutes)

    event = {
        "summary": f"Termin – {booking.name}",
        "description": f"E-Mail: {booking.email}",
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": "Europe/Berlin",
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": "Europe/Berlin",
        },
    }

    created_event = (
        service.events()
        .insert(
            calendarId=calendar_id,
            body=event,
        )
        .execute()
    )

    event_id = created_event["id"]
    meet_link = created_event.get("hangoutLink")

    return event_id, meet_link


def delete_event(calendar_event_id: str, tenant_id: str):
    service, calendar_id = get_oauth_calendar_service(tenant_id)

    service.events().delete(
        calendarId=calendar_id,
        eventId=calendar_event_id,
    ).execute()

    return True