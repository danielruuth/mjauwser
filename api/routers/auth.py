import time
import jwt
from fastapi import APIRouter, HTTPException, Depends

from config import settings
from schemas import LoginRequest, LoginResponse
from dependencies.auth import require_admin

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    if body.username != settings.admin_username or body.password != settings.admin_password:
        raise HTTPException(401, "Invalid credentials")

    now = time.time()
    expires_at = now + settings.jwt_expire_minutes * 60
    payload = {
        "sub": "admin",
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return LoginResponse(token=token, expires_at=expires_at)


@router.get("/verify", dependencies=[Depends(require_admin)])
async def verify():
    return {"valid": True}
