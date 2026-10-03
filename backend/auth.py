import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

security = HTTPBearer()


def hash_password(password: str):
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()


def verify_password(password: str, hashed: str):
    return bcrypt.checkpw(
        password.encode(),
        hashed.encode()
    )


def create_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=ALGORITHM
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET,
            algorithms=[ALGORITHM]
        )

        return payload["user_id"]

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )