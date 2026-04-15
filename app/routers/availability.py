from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.availability import check_availability_payload

router = APIRouter(prefix="/availability", tags=["availability"])


class AvailabilityRequest(BaseModel):
    requested_start: datetime
    duration_minutes: int = Field(..., gt=0)
    alternative_count: int = 3
    slot_interval_minutes: int = 30


@router.post("/check")
def check_availability(
    payload: AvailabilityRequest,
    db: Session = Depends(get_db),
):
    return check_availability_payload(
        db=db,
        requested_start=payload.requested_start,
        duration_minutes=payload.duration_minutes,
        alternative_count=payload.alternative_count,
        slot_interval_minutes=payload.slot_interval_minutes,
    )