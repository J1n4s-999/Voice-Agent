import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db

router = APIRouter(prefix="/admin/google", tags=["google"])


SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]

def require_admin(x_admin_secret: str | None = Header(default=None)):
    if not x_admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")


def create_flow(state: str | None = None) -> Flow:
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_oauth_redirect_uri],
            }
        },
        scopes=SCOPES,
        state=state,
    )
    flow.redirect_uri = settings.google_oauth_redirect_uri
    return flow


@router.get("/connect")
def google_connect(
    tenant_id: str = Query(...),
    _admin=Depends(require_admin),
):
    state = tenant_id

    flow = create_flow(state=state)

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    return {"authorization_url": authorization_url}


@router.get("/callback")
def google_callback(
    state: str = Query(...),
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    tenant_id = state

    flow = create_flow(state=state)

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google OAuth fehlgeschlagen: {e}")

    credentials = flow.credentials

    userinfo_service = build(
        "oauth2",
        "v2",
        credentials=credentials,
    )
    userinfo = userinfo_service.userinfo().get().execute()
    connected_email = userinfo.get("email")

    calendar_service = build(
        "calendar",
        "v3",
        credentials=credentials,
    )

    calendars = calendar_service.calendarList().list().execute()
    items = calendars.get("items", [])

    primary_calendar_id = None

    for item in items:
        if item.get("primary"):
            primary_calendar_id = item.get("id")
            break

    if not primary_calendar_id and items:
        primary_calendar_id = items[0].get("id")

    if not primary_calendar_id:
        raise HTTPException(status_code=400, detail="Kein Google Kalender gefunden.")

    db.execute(
        text("""
            DELETE FROM calendar_connections
            WHERE tenant_id = :tenant_id
              AND provider = 'google'
        """),
        {"tenant_id": tenant_id},
    )

    db.execute(
        text("""
            INSERT INTO calendar_connections (
                id,
                tenant_id,
                provider,
                google_calendar_id,
                connected_email,
                access_token,
                refresh_token,
                token_expiry,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :tenant_id,
                'google',
                :google_calendar_id,
                :connected_email,
                :access_token,
                :refresh_token,
                :token_expiry,
                :created_at,
                :updated_at
            )
        """),
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "google_calendar_id": primary_calendar_id,
            "connected_email": connected_email,
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": credentials.expiry,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
    )

    db.commit()

    return RedirectResponse(
        url=f"https://voice-agent-production-ed66.up.railway.app/google-connected"
    )


@router.get("/status")
def google_status(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    connection = (
        db.execute(
            text("""
                SELECT tenant_id, google_calendar_id, connected_email, updated_at
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
        return {"connected": False}

    return {
        "connected": True,
        "tenant_id": connection["tenant_id"],
        "google_calendar_id": connection["google_calendar_id"],
        "connected_email": connection["connected_email"],
        "updated_at": connection["updated_at"],
    }

@router.delete("/disconnect")
def google_disconnect(
    tenant_id: str = Query(...),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    db.execute(
        text("""
            DELETE FROM calendar_connections
            WHERE tenant_id = :tenant_id
              AND provider = 'google'
        """),
        {"tenant_id": tenant_id},
    )

    db.commit()

    return {"ok": True}