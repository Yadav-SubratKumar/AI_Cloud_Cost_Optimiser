import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET") or "change-this-secret"
ALGORITHM = "HS256"

security = HTTPBearer()


def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: int, role: str, remember_me: bool = False):
    # A normal session lasts 1 day; Remember Me extends the session to 30 days.
    expires_in = timedelta(days=30 if remember_me else 1)
    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "role": role,
        "remember_me": remember_me,
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        return jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[ALGORITHM],
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_current_user(payload=Depends(get_token_payload)):
    try:
        return int(payload["user_id"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_role(payload=Depends(get_token_payload)):
    role = payload.get("role")
    if not role:
        raise HTTPException(status_code=401, detail="Token has no role")
    return role
