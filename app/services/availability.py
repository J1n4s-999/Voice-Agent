from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import Booking, BookingSettings, OpeningHour, Vacation
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


def _parse_time(value: str | time | None) -> time | None:
    if value is None:
        return None

    if isinstance(value, time):
        return value

    return time.fromisoformat(value)


def get_buffer_minutes(db: Session, tenant_id: str) -> int:
    settings = (
        db.query(BookingSettings)
        .filter(BookingSettings.tenant_id == tenant_id)
        .first()
    )

    if not settings:
        return 0

    return max(settings.buffer_minutes or 0, 0)


def get_opening_hours(db: Session, tenant_id: str) -> list[OpeningHour]:
    return (
        db.query(OpeningHour)
        .filter(OpeningHour.tenant_id == tenant_id)
        .order_by(OpeningHour.weekday.asc())
        .all()
    )


def get_or_create_default_opening_hours(db: Session, tenant_id: str) -> list[OpeningHour]:
    existing = get_opening_hours(db, tenant_id)

    if len(existing) == 7:
        return existing

    existing_by_weekday = {item.weekday: item for item in existing}

    for weekday in range(7):
        if weekday not in existing_by_weekday:
            db.add(
                OpeningHour(
                    tenant_id=tenant_id,
                    weekday=weekday,
                    enabled=weekday < 5,
                    start_time=time(9, 0),
                    end_time=time(17, 0),
                )
            )

    db.commit()

    return get_opening_hours(db, tenant_id)


def is_within_opening_hours(
    db: Session,
    start: datetime,
    end: datetime,
    tenant_id: str,
) -> tuple[bool, str | None]:
    start = _to_berlin(start)
    end = _to_berlin(end)

    if start.date() != end.date():
        return False, "Der Termin darf nicht über Mitternacht hinausgehen."

    weekday = start.weekday()

    opening_hour = (
        db.query(OpeningHour)
        .filter(OpeningHour.tenant_id == tenant_id)
        .filter(OpeningHour.weekday == weekday)
        .first()
    )

    if not opening_hour:
        return False, "Für diesen Wochentag sind keine Öffnungszeiten hinterlegt."

    if not opening_hour.enabled:
        return False, "An diesem Wochentag ist geschlossen."

    open_time = _parse_time(opening_hour.start_time)
    close_time = _parse_time(opening_hour.end_time)

    if not open_time or not close_time:
        return False, "Die Öffnungszeiten für diesen Tag sind unvollständig."

    if start.time() < open_time or end.time() > close_time:
        return False, "Der Termin liegt außerhalb der Öffnungszeiten."

    return True, None


def is_during_vacation(
    db: Session,
    start: datetime,
    end: datetime,
    tenant_id: str,
) -> tuple[bool, str | None]:
    start = _to_berlin(start)
    end = _to_berlin(end)

    vacations = (
        db.query(Vacation)
        .filter(Vacation.tenant_id == tenant_id)
        .filter(Vacation.start_datetime < end)
        .filter(Vacation.end_datetime > start)
        .all()
    )

    if not vacations:
        return False, None

    titles = ", ".join(v.title for v in vacations)

    return True, f"Der Termin liegt in einem gesperrten Zeitraum: {titles}."


def has_db_conflict(
    db: Session,
    start: datetime,
    end: datetime,
    tenant_id: str,
    buffer_minutes: int = 0,
    exclude_booking_id: str | None = None,
) -> bool:
    start = _to_berlin(start)
    end = _to_berlin(end)

    buffered_start = start - timedelta(minutes=buffer_minutes)
    buffered_end = end + timedelta(minutes=buffer_minutes)

    conflicting_statuses = ["pending", "email_sent", "confirmed"]

    query = (
        db.query(Booking)
        .filter(Booking.tenant_id == tenant_id)
        .filter(Booking.status.in_(conflicting_statuses))
    )

    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)

    bookings = query.all()

    for booking in bookings:
        booking_start = _to_berlin(booking.requested_start)
        booking_end = booking_start + timedelta(minutes=booking.duration_minutes)

        if booking_start < buffered_end and booking_end > buffered_start:
            return True

    return False


def has_google_calendar_conflict(
    start: datetime,
    end: datetime,
    tenant_id: str,
    buffer_minutes: int = 0,
) -> bool:
    start = _to_berlin(start)
    end = _to_berlin(end)

    buffered_start = start - timedelta(minutes=buffer_minutes)
    buffered_end = end + timedelta(minutes=buffer_minutes)

    service, calendar_id = get_calendar_service(tenant_id)

    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=buffered_start.isoformat(),
            timeMax=buffered_end.isoformat(),
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


def validate_booking_rules(
    db: Session,
    requested_start: datetime,
    duration_minutes: int,
    tenant_id: str,
    check_calendar: bool = True,
    exclude_booking_id: str | None = None,
) -> dict:
    start = _to_berlin(requested_start)
    end = start + timedelta(minutes=duration_minutes)

    buffer_minutes = get_buffer_minutes(db, tenant_id)

    warnings: list[str] = []
    conflict_source: str | None = None

    in_opening_hours, opening_reason = is_within_opening_hours(
        db=db,
        start=start,
        end=end,
        tenant_id=tenant_id,
    )

    if not in_opening_hours:
        warnings.append(opening_reason or "Der Termin liegt außerhalb der Öffnungszeiten.")
        conflict_source = conflict_source or "opening_hours"

    vacation_conflict, vacation_reason = is_during_vacation(
        db=db,
        start=start,
        end=end,
        tenant_id=tenant_id,
    )

    if vacation_conflict:
        warnings.append(vacation_reason or "Der Termin liegt in einem gesperrten Zeitraum.")
        conflict_source = conflict_source or "vacation"

    if has_db_conflict(
        db=db,
        start=start,
        end=end,
        tenant_id=tenant_id,
        buffer_minutes=buffer_minutes,
        exclude_booking_id=exclude_booking_id,
    ):
        if buffer_minutes > 0:
            warnings.append(
                f"Der Termin überschneidet sich mit einem bestehenden Termin oder verletzt den Puffer von {buffer_minutes} Minuten."
            )
        else:
            warnings.append("Der Termin überschneidet sich mit einem bestehenden Termin.")

        conflict_source = conflict_source or "db"

    if check_calendar and has_google_calendar_conflict(
        start=start,
        end=end,
        tenant_id=tenant_id,
        buffer_minutes=buffer_minutes,
    ):
        if buffer_minutes > 0:
            warnings.append(
                f"Der Termin überschneidet sich mit Google Calendar oder verletzt den Puffer von {buffer_minutes} Minuten."
            )
        else:
            warnings.append("Der Termin überschneidet sich mit Google Calendar.")

        conflict_source = conflict_source or "google"

    return {
        "available": len(warnings) == 0,
        "warnings": warnings,
        "conflict_source": conflict_source,
        "buffer_minutes": buffer_minutes,
    }


def is_slot_available(
    db: Session,
    requested_start: datetime,
    duration_minutes: int,
    tenant_id: str,
) -> tuple[bool, str | None]:
    result = validate_booking_rules(
        db=db,
        requested_start=requested_start,
        duration_minutes=duration_minutes,
        tenant_id=tenant_id,
        check_calendar=True,
    )

    return result["available"], result["conflict_source"]


def find_alternative_slots(
    db: Session,
    requested_start: datetime,
    duration_minutes: int,
    tenant_id: str,
    count: int = 3,
    slot_interval_minutes: int = 30,
    search_limit: int = 24,
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
    reason: str | None = None,
) -> str:
    requested_label = _format_spoken_time(requested_start)

    if available:
        return f"Ja, der Termin um {requested_label} ist frei."

    if not alternatives:
        if reason == "opening_hours":
            return (
                f"Der Termin um {requested_label} liegt leider außerhalb unserer Öffnungszeiten. "
                f"Ich habe aktuell keine passenden Alternativen gefunden."
            )

        if reason == "vacation":
            return (
                f"Der Termin um {requested_label} liegt leider in einem gesperrten Zeitraum. "
                f"Ich habe aktuell keine passenden Alternativen gefunden."
            )

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
        f"Der Termin um {requested_label} ist leider nicht verfügbar. "
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
    result = validate_booking_rules(
        db=db,
        requested_start=requested_start,
        duration_minutes=duration_minutes,
        tenant_id=tenant_id,
        check_calendar=True,
    )

    available = result["available"]
    reason = result["conflict_source"]

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
        "warnings": result["warnings"],
        "buffer_minutes": result["buffer_minutes"],
        "alternatives": [_format_iso(dt) for dt in alternatives],
        "spoken_text": build_spoken_text(
            requested_start=requested_start,
            available=available,
            alternatives=alternatives,
            reason=reason,
        ),
    }