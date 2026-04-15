from fastapi import FastAPI

from app.config import settings
from app.db import Base, engine
from app.routers import confirm, webhooks
import app.models 
from sqlalchemy import text
from app.db import engine

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(webhooks.router)
app.include_router(confirm.router)


@app.get("/health")
def health():
    return {"ok": True, "app": settings.app_name}

@app.get("/db-count")
def db_count():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM bookings"))
        count = result.scalar()
    return {"bookings": count}