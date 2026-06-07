from uuid import UUID

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserNotFoundError(Exception):
    pass


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def get_user(self, user_id: UUID) -> User:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        return user

    def get_user_by_email(self, email: str) -> User:
        user = self.user_repository.get_user_by_email(email)
        if not user:
            raise UserNotFoundError(f"User {email} not found")
        return user

    def deactivate_user(self, user_id: UUID) -> User:
        user = self.user_repository.deactivate_user(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")
        return user
