from fastapi import APIRouter

router = APIRouter(tags=["confirm"])


@router.get("/confirm/{token}")
def confirm_booking(token: str):
    return {"ok": True, "token": token}