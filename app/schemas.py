from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from pydantic import BaseModel, EmailStr


class BookingRequest(BaseModel):
    name: str
    email: EmailStr
    date: str
    time: str
    duration_minutes: int


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