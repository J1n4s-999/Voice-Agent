from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import Booking
from app.services.google_calendar import get_calendar_service


BERLIN_TZ = ZoneInfo("Europe/Berlin")


def _to_berlin(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=BERLIN_TZ)
    return dt.astimezone(BERLIN_TZ)


def _format_spoken_time(dt: datetime) -> str:
    dt = _to_berlin(dt)
    return dt.strftime("%H:%M")


def _format_iso(dt: datetime) -> str:
    return _to_berlin(dt).isoformat()


def has_db_conflict(
    db: Session,
    start: datetime,
    end: datetime,
) -> bool:
    """
    Prüft auf Überschneidungen in der eigenen DB.
    Berücksichtigt pending + email_sent + confirmed.
    """
    conflicting_statuses = ["pending", "email_sent", "confirmed"]

    conflict = (
        db.query(Booking)
        .filter(Booking.status.in_(conflicting_statuses))
        .filter(
            and_(
                Booking.requested_start < end,
                Booking.requested_start + timedelta(minutes=0) >= Booking.requested_start,  # Dummy für Lesbarkeit
            )
        )
        .all()
    )

    # Da SQLAlchemy keine timedelta auf Spalten so bequem handhabt,
    # prüfen wir die Überschneidung hier in Python sauber nach.
    for booking in conflict:
        booking_start = _to_berlin(booking.requested_start)
        booking_end = booking_start + timedelta(minutes=booking.duration_minutes)

        if booking_start < end and booking_end > start:
            return True

    return False


def has_google_calendar_conflict(
    start: datetime,
    end: datetime,
    tenant_id: str,
) -> bool:
    service, calendar_id = get_calendar_service(tenant_id)

    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])

    for event in events:
        if event.get("status") == "cancelled":
            continue
        return True

    return False


def is_slot_available(
    db: Session,
    requested_start: datetime,
    duration_minutes: int,
    tenant_id: str,
) -> tuple[bool, str | None]:
    start = _to_berlin(requested_start)
    end = start + timedelta(minutes=duration_minutes)

    if has_db_conflict(db, start, end):
        return False, "db"

    if has_google_calendar_conflict(start, end, tenant_id):
        return False, "google"

    return True, None


def find_alternative_slots(
    db: Session,
    requested_start: datetime,
    duration_minutes: int,
    tenant_id: str,
    count: int = 3,
    slot_interval_minutes: int = 30,
    search_limit: int = 12,
) -> list[datetime]:
    alternatives: list[datetime] = []
    current = _to_berlin(requested_start)

    for _ in range(search_limit):
        available, _reason = is_slot_available(
            db=db,
            requested_start=current,
            duration_minutes=duration_minutes,
            tenant_id=tenant_id,
        )
        if available:
            alternatives.append(current)

        if len(alternatives) >= count:
            break

        current += timedelta(minutes=slot_interval_minutes)

    return alternatives


def build_spoken_text(
    requested_start: datetime,
    available: bool,
    alternatives: list[datetime],
) -> str:
    requested_label = _format_spoken_time(requested_start)

    if available:
        return f"Ja, der Termin um {requested_label} ist frei."

    if not alternatives:
        return (
            f"Der Termin um {requested_label} ist leider nicht frei. "
            f"Ich habe aktuell keine passenden Alternativen gefunden."
        )

    formatted = [_format_spoken_time(dt) for dt in alternatives]

    if len(formatted) == 1:
        alt_text = formatted[0]
    elif len(formatted) == 2:
        alt_text = f"{formatted[0]} oder {formatted[1]}"
    else:
        alt_text = f"{formatted[0]}, {formatted[1]} oder {formatted[2]}"

    return (
        f"Der Termin um {requested_label} ist leider nicht frei. "
        f"Ich hätte noch {alt_text} frei."
    )


def check_availability_payload(
    db: Session,
    requested_start: datetime,
    duration_minutes: int,
    tenant_id: str,
    alternative_count: int = 3,
    slot_interval_minutes: int = 30,
) -> dict:
    available, reason = is_slot_available(
        db=db,
        requested_start=requested_start,
        duration_minutes=duration_minutes,
        tenant_id=tenant_id,
    )

    alternatives: list[datetime] = []

    if not available:
        alternatives = find_alternative_slots(
            db=db,
            requested_start=_to_berlin(requested_start) + timedelta(minutes=slot_interval_minutes),
            duration_minutes=duration_minutes,
            tenant_id=tenant_id,
            count=alternative_count,
            slot_interval_minutes=slot_interval_minutes,
        )

    return {
        "available": available,
        "requested_start": _format_iso(requested_start),
        "duration_minutes": duration_minutes,
        "conflict_source": reason,
        "alternatives": [_format_iso(dt) for dt in alternatives],
        "spoken_text": build_spoken_text(
            requested_start=requested_start,
            available=available,
            alternatives=alternatives,
        ),
    }