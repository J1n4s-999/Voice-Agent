from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BookingRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    requested_start: datetime
    duration_minutes: int = Field(..., ge=15, le=180)


class BookingResponse(BaseModel):
    ok: bool
    booking_id: str
    status: str
    message: str


class SendConfirmationRequest(BaseModel):
    booking_id: str


class GenericMessageResponse(BaseModel):
    ok: bool
    message: str


class SendConfirmationResponse(BaseModel):
    ok: bool
    booking_id: str
    status: str
    confirm_link: str
    expires_at: datetime


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    requested_start: datetime
    duration_minutes: int
    status: str
    confirmation_expires_at: datetime | None = None
    confirmation_sent_at: datetime | None = None
    confirmed_at: datetime | None = None
    token_used_at: datetime | None = None
    calendar_event_id: str | None = None
    google_meet_link: str | None = None
    created_at: datetime
    updated_at: datetime

class BookingAttemptResponse(BaseModel):
    ok: bool
    booking_id: str | None = None
    status: str
    message: str
    conflict_source: str | None = None
    alternatives: list[str] = []
    spoken_text: str | None = None