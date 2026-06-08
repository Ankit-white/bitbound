from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from uuid import UUID, uuid4

from jose import jwt
from jose.exceptions import JWTError


class JWTServiceError(Exception):
    """Raised when JWT operations fail."""
    pass


class JWTService:
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(self, user_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "jti": str(uuid4()),
            "iat": now,
            "exp": expire
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: UUID) -> str:
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_token_expire_days)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "jti": str(uuid4()),
            "iat": now,
            "exp": expire
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except JWTError as e:
            raise JWTServiceError(f"Invalid token: {str(e)}")

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        payload = self.verify_token(token)
        
        if payload.get("type") != "access":
            raise JWTServiceError("Invalid access token")
        
        return payload

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        payload = self.verify_token(token)
        
        if payload.get("type") != "refresh":
            raise JWTServiceError("Invalid refresh token")
        
        return payload

    def get_user_id(self, token: str) -> UUID:
        payload = self.verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise JWTServiceError("Token does not contain user_id")
        return UUID(user_id)

    def get_token_type(self, token: str) -> str:
        payload = self.verify_token(token)
        token_type = payload.get("type")
        if not token_type:
            raise JWTServiceError("Token does not contain type")
        return token_type
