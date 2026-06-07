from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.otp_repository import OTPRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.services.jwt_service import JWTService
from app.core.config import settings


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials

    try:
        from app.auth.jwt import JWTManager
        payload = JWTManager.get_current_user_payload(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not payload or not payload.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = UUID(payload.get("user_id"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    return current_user


def get_auth_service(
    db: Session = Depends(get_db)
) -> AuthService:
    user_repo = UserRepository(db)
    otp_repo = OTPRepository(db)
    refresh_repo = RefreshTokenRepository(db)

    

    jwt_service = JWTService(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
    access_token_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    return AuthService(
        user_repository=user_repo,
        otp_repository=otp_repo,
        refresh_token_repository=refresh_repo,
        jwt_service=jwt_service
    )


def get_email_service() -> EmailService:
    smtp_port = settings.SMTP_PORT
    use_ssl = smtp_port == 465
    use_tls = smtp_port != 465

    return EmailService(
        mail_username=settings.SMTP_USERNAME,
        mail_password=settings.SMTP_PASSWORD,
        mail_from=settings.SMTP_FROM_EMAIL,
        mail_server=settings.SMTP_HOST,
        mail_port=smtp_port,
        use_ssl=use_ssl,
        use_tls=use_tls
    )
def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user
