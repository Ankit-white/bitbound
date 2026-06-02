from uuid import UUID

from app.auth.hashing import PasswordHasher
from app.auth.jwt import JWTManager
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserLoginRequest, UserSignupRequest


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def signup(self, request: UserSignupRequest) -> dict:
        if self.user_repo.email_exists(request.email):
            raise UserAlreadyExistsError(f"User with email {request.email} already exists")

        password_hash = PasswordHasher.hash_password(request.password)

        user = self.user_repo.create_user(
            name=request.name,
            email=request.email,
            password_hash=password_hash,
            role="developer"
        )

        access_token = JWTManager.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role
        )

        return {
            "user": user,
            "access_token": access_token
        }

    def login(self, request: UserLoginRequest) -> dict:
        user = self.user_repo.get_user_by_email(request.email)

        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        if not PasswordHasher.verify_password(request.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        if not user.is_active:
            raise InactiveUserError("Account is deactivated")

        access_token = JWTManager.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role
        )

        return {
            "user": user,
            "access_token": access_token
        }

    def get_current_user(self, user_id: UUID) -> User:
        user = self.user_repo.get_user_by_id(user_id)

        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")

        if not user.is_active:
            raise InactiveUserError("Account is deactivated")

        return user

    def deactivate_user(self, user_id: UUID) -> User:
        user = self.get_current_user(user_id)
        return self.user_repo.deactivate_user(user.id)