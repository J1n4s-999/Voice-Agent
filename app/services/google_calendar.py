from datetime import timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.config import settings


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_calendar_service():
    credentials = service_account.Credentials.from_service_account_file(
        settings.google_credentials_path,
        scopes=SCOPES,
    )
    return build("calendar", "v3", credentials=credentials)


def create_event(booking):
    service = get_calendar_service()

    start = booking.requested_start
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
        "conferenceData": {
            "createRequest": {
                "requestId": f"{booking.id}",
                "conferenceSolutionKey": {
                    "type": "hangoutsMeet"
                },
            }
        },
    }

    created_event = (
        service.events()
        .insert(
            calendarId=settings.google_calendar_id,
            body=event,
            conferenceDataVersion=1,
        )
        .execute()
    )

    event_id = created_event["id"]
    meet_link = created_event.get("hangoutLink")

    return event_id, meet_link