import uuid
from datetime import datetime, timedelta, timezone, time

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Booking, BookingSettings, OpeningHour, Vacation
from app.security import hash_password, verify_password
from app.services.availability import (
    get_or_create_default_opening_hours,
    validate_booking_rules,
)
from app.services.bookings import mark_booking_confirmed
from app.services.google_calendar import create_event, update_event

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class CreateTenantRequest(BaseModel):
    name: str
    agent_key: str
    username: str
    password: str


class AdminCreateBookingRequest(BaseModel):
    tenant_id: str
    name: str
    email: str
    requested_start: datetime
    duration_minutes: int
    force: bool = False


class AdminUpdateBookingRequest(BaseModel):
    name: str
    email: str
    requested_start: datetime
    duration_minutes: int
    force: bool = False


class OpeningHourPayload(BaseModel):
    weekday: int = Field(..., ge=0, le=6)
    enabled: bool
    start_time: str | None = None
    end_time: str | None = None


class BookingRulesPayload(BaseModel):
    tenant_id: str
    buffer_minutes: int = Field(..., ge=0, le=240)
    opening_hours: list[OpeningHourPayload]


class VacationPayload(BaseModel):
    tenant_id: str
    title: str = "Urlaub"
    start_datetime: datetime
    end_datetime: datetime


def require_admin(x_admin_secret: str | None = Header(default=None)):
    if not x_admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")


def parse_time_or_none(value: str | None) -> time | None:
    if not value:
        return None

    return time.fromisoformat(value)


def cleanup_expired_pending_bookings(db: Session, tenant_id: str):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)

    expired = (
        db.query(Booking)
        .filter(Booking.tenant_id == tenant_id)
        .filter(Booking.status == "pending")
        .filter(Booking.created_at < cutoff)
        .all()
    )

    for booking in expired:
        db.delete(booking)

    db.commit()


@router.post("/login")
def admin_login(
    payload: AdminLoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.execute(
            text(
                """
                SELECT id, tenant_id, username, password_hash, role
                FROM admin_users
                WHERE username = :username
                """
            ),
            {"username": payload.username.strip().lower()},
        )
        .mappings()
        .fetchone()
    )

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "ok": True,
        "user_id": user["id"],
        "username": user["username"],
        "tenant_id": user["tenant_id"],
        "role": user["role"],
    }


@router.get("/tenants")
def list_tenants(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    tenants = (
        db.execute(
            text(
                """
                SELECT id, name, agent_key
                FROM tenants
                ORDER BY name ASC
                """
            )
        )
        .mappings()
        .all()
    )

    return [
        {
            "id": t["id"],
            "name": t["name"],
            "agent_key": t["agent_key"],
        }
        for t in tenants
    ]


@router.post("/tenants")
def create_tenant(
    payload: CreateTenantRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    tenant_id = str(uuid.uuid4())
    agent_key = payload.agent_key.strip().lower()
    username = payload.username.strip().lower()

    try:
        db.execute(
            text(
                """
                INSERT INTO tenants (id, name, agent_key)
                VALUES (:id, :name, :agent_key)
                """
            ),
            {
                "id": tenant_id,
                "name": payload.name.strip(),
                "agent_key": agent_key,
            },
        )

        db.execute(
            text(
                """
                INSERT INTO admin_users (id, tenant_id, username, password_hash, role)
                VALUES (:id, :tenant_id, :username, :password_hash, :role)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "username": username,
                "password_hash": hash_password(payload.password),
                "role": "tenant_admin",
            },
        )

        db.add(
            BookingSettings(
                tenant_id=tenant_id,
                buffer_minutes=0,
            )
        )

        for weekday in range(7):
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

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Tenant/User konnte nicht erstellt werden: {e}",
        )

    return {
        "ok": True,
        "tenant_id": tenant_id,
        "name": payload.name.strip(),
        "agent_key": agent_key,
        "username": username,
    }


@router.get("/booking-rules")
def get_booking_rules(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    opening_hours = get_or_create_default_opening_hours(db, tenant_id)

    booking_settings = (
        db.query(BookingSettings)
        .filter(BookingSettings.tenant_id == tenant_id)
        .first()
    )

    if not booking_settings:
        booking_settings = BookingSettings(
            tenant_id=tenant_id,
            buffer_minutes=0,
        )
        db.add(booking_settings)
        db.commit()
        db.refresh(booking_settings)

    return {
        "tenant_id": tenant_id,
        "buffer_minutes": booking_settings.buffer_minutes,
        "opening_hours": [
            {
                "id": item.id,
                "weekday": item.weekday,
                "enabled": item.enabled,
                "start_time": item.start_time.strftime("%H:%M") if item.start_time else None,
                "end_time": item.end_time.strftime("%H:%M") if item.end_time else None,
            }
            for item in opening_hours
        ],
    }


@router.put("/booking-rules")
def update_booking_rules(
    payload: BookingRulesPayload,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    if len(payload.opening_hours) != 7:
        raise HTTPException(
            status_code=400,
            detail="Es müssen genau 7 Wochentage gesendet werden.",
        )

    existing_settings = (
        db.query(BookingSettings)
        .filter(BookingSettings.tenant_id == payload.tenant_id)
        .first()
    )

    if not existing_settings:
        existing_settings = BookingSettings(
            tenant_id=payload.tenant_id,
            buffer_minutes=payload.buffer_minutes,
        )
        db.add(existing_settings)
    else:
        existing_settings.buffer_minutes = payload.buffer_minutes

    for item in payload.opening_hours:
        if item.enabled and (not item.start_time or not item.end_time):
            raise HTTPException(
                status_code=400,
                detail=f"Start- und Endzeit fehlen für Wochentag {item.weekday}.",
            )

        start_time = parse_time_or_none(item.start_time)
        end_time = parse_time_or_none(item.end_time)

        if item.enabled and start_time and end_time and start_time >= end_time:
            raise HTTPException(
                status_code=400,
                detail=f"Startzeit muss vor Endzeit liegen. Wochentag: {item.weekday}",
            )

        opening_hour = (
            db.query(OpeningHour)
            .filter(OpeningHour.tenant_id == payload.tenant_id)
            .filter(OpeningHour.weekday == item.weekday)
            .first()
        )

        if not opening_hour:
            opening_hour = OpeningHour(
                tenant_id=payload.tenant_id,
                weekday=item.weekday,
            )
            db.add(opening_hour)

        opening_hour.enabled = item.enabled
        opening_hour.start_time = start_time
        opening_hour.end_time = end_time

    db.commit()

    return {
        "ok": True,
        "message": "Öffnungszeiten und Puffer wurden gespeichert.",
    }


@router.get("/vacations")
def list_vacations(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    vacations = (
        db.query(Vacation)
        .filter(Vacation.tenant_id == tenant_id)
        .order_by(Vacation.start_datetime.asc())
        .all()
    )

    return [
        {
            "id": vacation.id,
            "tenant_id": vacation.tenant_id,
            "title": vacation.title,
            "start_datetime": vacation.start_datetime.isoformat(),
            "end_datetime": vacation.end_datetime.isoformat(),
        }
        for vacation in vacations
    ]


@router.post("/vacations")
def create_vacation(
    payload: VacationPayload,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    if payload.start_datetime >= payload.end_datetime:
        raise HTTPException(
            status_code=400,
            detail="Startdatum muss vor Enddatum liegen.",
        )

    vacation = Vacation(
        tenant_id=payload.tenant_id,
        title=payload.title.strip() or "Urlaub",
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
    )

    db.add(vacation)
    db.commit()
    db.refresh(vacation)

    return {
        "ok": True,
        "vacation": {
            "id": vacation.id,
            "tenant_id": vacation.tenant_id,
            "title": vacation.title,
            "start_datetime": vacation.start_datetime.isoformat(),
            "end_datetime": vacation.end_datetime.isoformat(),
        },
    }


@router.delete("/vacations/{vacation_id}")
def delete_vacation(
    vacation_id: str,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    vacation = (
        db.query(Vacation)
        .filter(Vacation.id == vacation_id)
        .filter(Vacation.tenant_id == tenant_id)
        .first()
    )

    if not vacation:
        raise HTTPException(status_code=404, detail="Urlaub nicht gefunden.")

    db.delete(vacation)
    db.commit()

    return {
        "ok": True,
        "message": "Urlaub wurde gelöscht.",
    }


@router.post("/bookings")
def create_booking_manually(
    payload: AdminCreateBookingRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    validation = validate_booking_rules(
        db=db,
        requested_start=payload.requested_start,
        duration_minutes=payload.duration_minutes,
        tenant_id=payload.tenant_id,
        check_calendar=True,
    )

    if not validation["available"] and not payload.force:
        return {
            "ok": False,
            "requires_confirmation": True,
            "warnings": validation["warnings"],
            "conflict_source": validation["conflict_source"],
            "message": "Der Termin verletzt Regeln. Soll er trotzdem angelegt werden?",
        }

    booking = Booking(
        tenant_id=payload.tenant_id,
        name=payload.name,
        email=payload.email,
        requested_start=payload.requested_start,
        duration_minutes=payload.duration_minutes,
        status="confirmed",
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    event_id, meet_link = create_event(booking)

    booking.calendar_event_id = event_id
    booking.google_meet_link = meet_link

    db.commit()
    db.refresh(booking)

    return {
        "ok": True,
        "booking_id": booking.id,
        "calendar_event_id": booking.calendar_event_id,
        "status": booking.status,
        "warnings": validation["warnings"],
        "was_forced": payload.force and not validation["available"],
    }


@router.patch("/bookings/{booking_id}")
def update_booking_manually(
    booking_id: str,
    payload: AdminUpdateBookingRequest,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .filter(Booking.tenant_id == tenant_id)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    validation = validate_booking_rules(
        db=db,
        requested_start=payload.requested_start,
        duration_minutes=payload.duration_minutes,
        tenant_id=tenant_id,
        check_calendar=True,
        exclude_booking_id=booking_id,
    )

    if not validation["available"] and not payload.force:
        return {
            "ok": False,
            "requires_confirmation": True,
            "warnings": validation["warnings"],
            "conflict_source": validation["conflict_source"],
            "message": "Der geänderte Termin verletzt Regeln. Soll er trotzdem gespeichert werden?",
        }

    booking.name = payload.name
    booking.email = payload.email
    booking.requested_start = payload.requested_start
    booking.duration_minutes = payload.duration_minutes

    if booking.status == "confirmed" and booking.calendar_event_id:
        _event_id, meet_link = update_event(booking)
        booking.google_meet_link = meet_link

    db.commit()
    db.refresh(booking)

    return {
        "ok": True,
        "booking_id": booking.id,
        "status": booking.status,
        "warnings": validation["warnings"],
        "was_forced": payload.force and not validation["available"],
    }


@router.get("/bookings")
def list_bookings(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    cleanup_expired_pending_bookings(db, tenant_id)

    bookings = (
        db.query(Booking)
        .filter(Booking.tenant_id == tenant_id)
        .order_by(Booking.requested_start.desc())
        .all()
    )

    return [
        {
            "id": b.id,
            "tenant_id": b.tenant_id,
            "name": b.name,
            "email": b.email,
            "requested_start": b.requested_start.isoformat() if b.requested_start else None,
            "duration_minutes": b.duration_minutes,
            "status": b.status,
            "calendar_event_id": b.calendar_event_id,
            "google_meet_link": b.google_meet_link,
            "created_at": b.created_at.isoformat() if getattr(b, "created_at", None) else None,
        }
        for b in bookings
    ]


@router.delete("/bookings/{booking_id}")
def delete_booking(
    booking_id: str,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .filter(Booking.tenant_id == tenant_id)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.calendar_event_id:
        try:
            from app.services.google_calendar import delete_event

            delete_event(
                calendar_event_id=booking.calendar_event_id,
                tenant_id=tenant_id,
            )
        except Exception as e:
            print("Google delete failed:", e)

    db.delete(booking)
    db.commit()

    return {
        "ok": True,
        "message": "Booking + Google event deleted",
    }


@router.post("/bookings/{booking_id}/confirm")
def confirm_booking_manually(
    booking_id: str,
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .filter(Booking.tenant_id == tenant_id)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking.status == "confirmed":
        return {
            "ok": True,
            "message": "Booking already confirmed",
            "calendar_event_id": booking.calendar_event_id,
            "meet_link": booking.google_meet_link,
        }

    validation = validate_booking_rules(
        db=db,
        requested_start=booking.requested_start,
        duration_minutes=booking.duration_minutes,
        tenant_id=tenant_id,
        check_calendar=True,
        exclude_booking_id=booking.id,
    )

    if not validation["available"]:
        return {
            "ok": False,
            "requires_confirmation": True,
            "warnings": validation["warnings"],
            "conflict_source": validation["conflict_source"],
            "message": "Dieser Termin verletzt inzwischen Regeln und wurde nicht automatisch bestätigt.",
        }

    event_id, meet_link = create_event(booking)

    booking.google_meet_link = meet_link

    booking = mark_booking_confirmed(
        db=db,
        booking=booking,
        calendar_event_id=event_id,
    )

    return {
        "ok": True,
        "message": "Booking confirmed",
        "booking_id": booking.id,
        "calendar_event_id": event_id,
        "meet_link": meet_link,
    }