import os
from datetime import datetime, timedelta, timezone
from typing import Final
from uuid import UUID

from jose import JWTError, jwt


class JWTManager:
    _secret_key: Final[str] = os.getenv("JWT_SECRET_KEY", "")
    _algorithm: Final[str] = os.getenv("JWT_ALGORITHM", "HS256")
    _expire_minutes: Final[int] = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    @classmethod
    def _validate_config(cls) -> None:
        if not cls._secret_key:
            raise ValueError("JWT_SECRET_KEY is not configured. Set it in .env file")

    @classmethod
    def create_access_token(cls, user_id: UUID, email: str, role: str) -> str:
        cls._validate_config()
        
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=cls._expire_minutes)
        
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "iat": now,
            "exp": expire,
        }
        
        return jwt.encode(payload, cls._secret_key, algorithm=cls._algorithm)

    @classmethod
    def verify_token(cls, token: str) -> dict | None:
        cls._validate_config()
        
        try:
            payload = jwt.decode(token, cls._secret_key, algorithms=[cls._algorithm])
            return payload
        except JWTError:
            return None

    @classmethod
    def get_current_user_payload(cls, token: str) -> dict | None:
        payload = cls.verify_token(token)
        
        if not payload:
            return None
        
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role"),
        }