import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Booking
from app.security import hash_password, verify_password
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


class AdminUpdateBookingRequest(BaseModel):
    name: str
    email: str
    requested_start: datetime
    duration_minutes: int


def require_admin(x_admin_secret: str | None = Header(default=None)):
    if not x_admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")


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
            text("""
                SELECT id, tenant_id, username, password_hash, role
                FROM admin_users
                WHERE username = :username
            """),
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
            text("""
                SELECT id, name, agent_key
                FROM tenants
                ORDER BY name ASC
            """)
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
            text("""
                INSERT INTO tenants (id, name, agent_key)
                VALUES (:id, :name, :agent_key)
            """),
            {
                "id": tenant_id,
                "name": payload.name.strip(),
                "agent_key": agent_key,
            },
        )

        db.execute(
            text("""
                INSERT INTO admin_users (id, tenant_id, username, password_hash, role)
                VALUES (:id, :tenant_id, :username, :password_hash, :role)
            """),
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "username": username,
                "password_hash": hash_password(payload.password),
                "role": "tenant_admin",
            },
        )

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Tenant/User konnte nicht erstellt werden: {e}")

    return {
        "ok": True,
        "tenant_id": tenant_id,
        "name": payload.name.strip(),
        "agent_key": agent_key,
        "username": username,
    }

@router.post("/bookings")
def create_booking_manually(
    payload: AdminCreateBookingRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
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
    }

@router.patch("/bookings/{booking_id}")
def update_booking_manually(
    booking_id: str,
    payload: AdminUpdateBookingRequest,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.name = payload.name
    booking.email = payload.email
    booking.requested_start = payload.requested_start
    booking.duration_minutes = payload.duration_minutes

    if booking.status == "confirmed" and booking.calendar_event_id:
        event_id, meet_link = update_event(booking)
        booking.google_meet_link = meet_link

    db.commit()
    db.refresh(booking)

    return {
        "ok": True,
        "booking_id": booking.id,
        "status": booking.status,
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
                tenant_id=tenant_id
            )
        except Exception as e:
            print("Google delete failed:", e)

    db.delete(booking)
    db.commit()

    return {
        "ok": True,
        "message": "Booking + Google event deleted"
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