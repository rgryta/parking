import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
APP_PASSWORD = os.getenv("APP_PASSWORD", "parking123")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 8


def create_token(username: str, is_admin: bool = False) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "admin": is_admin, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def check_password(password: str) -> bool:
    return password == APP_PASSWORD


def check_admin_password(password: str) -> bool:
    return password == ADMIN_PASSWORD


def get_current_user(request: Request) -> Optional[dict]:
    token = request.cookies.get("session")
    if not token:
        return None
    return decode_token(token)


class AuthRedirect(Exception):
    def __init__(self, url: str):
        self.url = url


def require_auth(request: Request) -> dict:
    user = get_current_user(request)
    if not user:
        raise AuthRedirect("/login")
    return user


def require_admin(request: Request) -> dict:
    user = get_current_user(request)
    if not user or not user.get("admin"):
        raise AuthRedirect("/login?next=admin")
    return user
