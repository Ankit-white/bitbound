from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    UserLoginRequest,
    UserResponse,
    UserSignupRequest,
    TokenResponse,
)
from app.services.auth_service import (
    AuthService,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    InactiveUserError,
    UserNotFoundError,
)
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Creates a new user account and returns JWT access token"
)
def signup(
    request: UserSignupRequest,
    db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    try:
        result = auth_service.signup(request)
        return TokenResponse(
            access_token=result["access_token"],
            token_type="bearer"
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user",
    description="Verifies credentials and returns JWT access token"
)
def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db)
):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    try:
        result = auth_service.login(request)
        return TokenResponse(
            access_token=result["access_token"],
            token_type="bearer"
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except InactiveUserError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns authenticated user's profile information"
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return UserResponse.model_validate(current_user)