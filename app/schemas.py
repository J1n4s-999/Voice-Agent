from datetime import datetime
from pydantic import BaseModel, EmailStr


class BookingRequest(BaseModel):
    name: str
    email: EmailStr
    day: int
    month: int
    hour: int
    minute: int
    duration_minutes: int
    year: int | None = None


class BookingAttemptResponse(BaseModel):
    ok: bool
    booking_id: str | None = None
    status: str
    message: str
    conflict_source: str | None = None
    alternatives: list[str] = []
    spoken_text: str | None = None


class SendConfirmationRequest(BaseModel):
    booking_id: str


class SendConfirmationResponse(BaseModel):
    ok: bool
    booking_id: str
    status: str
    confirm_link: str
    expires_at: datetime