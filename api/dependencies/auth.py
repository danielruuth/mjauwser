import jwt
from fastapi import Header, HTTPException, Request
from config import settings


def require_admin(authorization: str = Header(None, alias="Authorization")):
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401, "Invalid Authorization header format")
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    if payload.get("sub") != "admin":
        raise HTTPException(401, "Invalid token subject")


def require_admin_ws(request: Request):
    token = request.query_params.get("token")
    if not token:
        return
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(401, "Invalid or expired token")
    if payload.get("sub") != "admin":
        raise HTTPException(401, "Invalid token subject")
