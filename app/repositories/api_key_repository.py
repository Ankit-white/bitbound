from uuid import UUID
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.api_key import APIKey


class APIKeyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_api_key(
        self,
        user_id: UUID,
        key_hash: str,
        prefix: str,
        name: str,
        agent_id: Optional[UUID] = None,
        expires_at: Optional[datetime] = None
    ) -> APIKey:
        api_key = APIKey(
            user_id=user_id,
            agent_id=agent_id,
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            expires_at=expires_at,
            is_active=True
        )
        self.db.add(api_key)
        try:
            self.db.commit()
            self.db.refresh(api_key)
            return api_key
        except Exception:
            self.db.rollback()
            raise

    def get_by_id(self, key_id: UUID) -> Optional[APIKey]:
        return self.db.query(APIKey).filter(APIKey.id == key_id).first()

    def get_by_key_hash(self, key_hash: str) -> Optional[APIKey]:
        return self.db.query(APIKey).filter(APIKey.key_hash == key_hash).first()

    def get_by_user(
            
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[APIKey]:
        return (
            self.db.query(APIKey)
            .filter(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_agent(
        self,
        agent_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[APIKey]:
        return (
            self.db.query(APIKey)
            .filter(APIKey.agent_id == agent_id)
            .order_by(APIKey.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_keys_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[APIKey]:
        return (
            self.db.query(APIKey)
            .filter(
                and_(
                    APIKey.user_id == user_id,
                    APIKey.is_active.is_(True)
                )
            )
            .order_by(APIKey.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_keys_by_agent(
        self,
        agent_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[APIKey]:
        return (
            self.db.query(APIKey)
            .filter(
                and_(
                    APIKey.agent_id == agent_id,
                    APIKey.is_active.is_(True)
                )
            )
            .order_by(APIKey.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_valid_key_by_hash(self, key_hash: str) -> Optional[APIKey]:
        now = datetime.now(timezone.utc)
        return (
            self.db.query(APIKey)
            .filter(
                and_(
                    APIKey.key_hash == key_hash,
                    APIKey.is_active.is_(True),
                    or_(
                        APIKey.expires_at.is_(None),
                        APIKey.expires_at > now
                    )
                )
            )
            .first()
        )

    def update_last_used(self, key_id: UUID) -> Optional[APIKey]:
        api_key = self.get_by_id(key_id)
        if api_key:
            api_key.last_used_at = datetime.now(timezone.utc)
            try:
                self.db.commit()
                self.db.refresh(api_key)
            except Exception:
                self.db.rollback()
                raise
        return api_key

    def deactivate_key(self, key_id: UUID) -> Optional[APIKey]:
        api_key = self.get_by_id(key_id)
        if api_key:
            api_key.is_active = False
            try:
                self.db.commit()
                self.db.refresh(api_key)
            except Exception:
                self.db.rollback()
                raise
        return api_key

    def delete_key(self, key_id: UUID) -> bool:
        api_key = self.get_by_id(key_id)
        if api_key:
            self.db.delete(api_key)
            try:
                self.db.commit()
                return True
            except Exception:
                self.db.rollback()
                raise
        return False

    def get_expired_keys(self) -> List[APIKey]:
        now = datetime.now(timezone.utc)
        return (
            self.db.query(APIKey)
            .filter(
                and_(
                    APIKey.is_active.is_(True),
                    APIKey.expires_at.isnot(None),
                    APIKey.expires_at <= now
                )
            )
            .all()
        )

    def count_active_keys(self, user_id: UUID) -> int:
        return (
            self.db.query(APIKey)
            .filter(
                and_(
                    APIKey.user_id == user_id,
                    APIKey.is_active.is_(True)
                )
            )
            .count()
        )