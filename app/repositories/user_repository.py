from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str = "developer"
    ) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def get_user_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def email_exists(self, email: str) -> bool:
        return self.db.query(User).filter(User.email == email).first() is not None

    def update_user(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        
        return user

    def deactivate_user(self, user_id: UUID) -> User | None:
        user = self.get_user_by_id(user_id)
        
        if user:
            user.is_active = False
            self.db.commit()
            self.db.refresh(user)
        
        return user