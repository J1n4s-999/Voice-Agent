import hashlib
from datetime import datetime, timedelta, timezone

from itsdangerous import URLSafeTimedSerializer

from app.config import settings


def get_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=settings.token_secret,
        salt=settings.token_salt,
    )


def generate_confirmation_token(booking_id: str) -> str:
    serializer = get_serializer()
    return serializer.dumps({"booking_id": booking_id})


def verify_confirmation_token(token: str) -> str:
    serializer = get_serializer()
    data = serializer.loads(
        token,
        max_age=settings.token_max_age_seconds,
    )
    return data["booking_id"]


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.token_max_age_seconds)