import json
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BERLIN_TZ = ZoneInfo("Europe/Berlin")


def to_berlin(dt: datetime) -> datetime:
    """
    Sorgt dafür, dass ein datetime sicher in Europe/Berlin vorliegt.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=BERLIN_TZ)
    return dt.astimezone(BERLIN_TZ)


def get_calendar_service():
    if settings.google_service_account_json:
        info = json.loads(settings.google_service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=SCOPES,
        )
    else:
        credentials = service_account.Credentials.from_service_account_file(
            settings.google_credentials_path,
            scopes=SCOPES,
        )

    return build("calendar", "v3", credentials=credentials)


def create_event(booking):
    service = get_calendar_service()

    start = to_berlin(booking.requested_start)
    end = start + timedelta(minutes=booking.duration_minutes)

    event = {
        "summary": f"CDM Beratung – {booking.name}",
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
            calendarId=settings.google_calendar_id,
            body=event,
        )
        .execute()
    )

    event_id = created_event["id"]
    meet_link = created_event.get("hangoutLink")

    return event_id, meet_link