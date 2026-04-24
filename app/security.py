import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext

from app.config import settings

BERLIN_TZ = ZoneInfo("Europe/Berlin")

serializer = URLSafeTimedSerializer(
    secret_key=settings.token_secret,
    salt=settings.token_salt,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_confirmation_token(booking_id: str) -> str:
    return serializer.dumps({"booking_id": booking_id})


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_token_expiry() -> datetime:
    return datetime.now(BERLIN_TZ) + timedelta(seconds=settings.token_max_age_seconds)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)