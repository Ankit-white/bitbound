from uuid import UUID
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_refresh_token(
        self,
        user_id: UUID,
        token: str,
        expires_at: datetime,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
            is_revoked=False
        )
        self.db.add(refresh_token)
        try:
            self.db.commit()
            self.db.refresh(refresh_token)
            return refresh_token
        except Exception:
            self.db.rollback()
            raise

    def get_by_id(self, token_id: UUID) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.id == token_id).first()

    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.token == token).first()

    def get_by_user(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[RefreshToken]:
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.user_id == user_id)
            .order_by(RefreshToken.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_user_tokens(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[RefreshToken]:
        return self.get_by_user(user_id, skip, limit)

    def get_active_user_tokens(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[RefreshToken]:
        return (
            self.db.query(RefreshToken)
            .filter(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked.is_(False),
                    RefreshToken.expires_at > datetime.now(timezone.utc)
                )
            )
            .order_by(RefreshToken.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def revoke_token(self, token_id: UUID) -> Optional[RefreshToken]:
        refresh_token = self.get_by_id(token_id)
        if refresh_token:
            refresh_token.is_revoked = True
            try:
                self.db.commit()
                self.db.refresh(refresh_token)
                return refresh_token
            except Exception:
                self.db.rollback()
                raise
        return refresh_token

    def revoke_by_token(self, token: str) -> Optional[RefreshToken]:
        refresh_token = self.get_by_token(token)
        if refresh_token:
            refresh_token.is_revoked = True
            try:
                self.db.commit()
                self.db.refresh(refresh_token)
                return refresh_token
            except Exception:
                self.db.rollback()
                raise
        return refresh_token

    def revoke_all_user_tokens(self, user_id: UUID) -> int:
        tokens = self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False)
            )
        ).all()
        
        count = 0
        for token in tokens:
            token.is_revoked = True
            count += 1
        
        try:
            self.db.commit()
            return count
        except Exception:
            self.db.rollback()
            raise

    def update_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        try:
            self.db.add(refresh_token)
            self.db.commit()
            self.db.refresh(refresh_token)
            return refresh_token
        except Exception:
            self.db.rollback()
            raise

    def delete_token(self, token_id: UUID) -> bool:
        refresh_token = self.get_by_id(token_id)
        if refresh_token:
            self.db.delete(refresh_token)
            try:
                self.db.commit()
                return True
            except Exception:
                self.db.rollback()
                raise
        return False

    def delete_expired_tokens(self) -> int:
        now = datetime.now(timezone.utc)
        tokens = self.db.query(RefreshToken).filter(
            RefreshToken.expires_at <= now
        ).all()
        
        count = 0
        for token in tokens:
            self.db.delete(token)
            count += 1
        
        try:
            self.db.commit()
            return count
        except Exception:
            self.db.rollback()
            raise

    def get_valid_token_by_value(self, token: str) -> Optional[RefreshToken]:
        now = datetime.now(timezone.utc)
        return (
            self.db.query(RefreshToken)
            .filter(
                and_(
                    RefreshToken.token == token,
                    RefreshToken.is_revoked.is_(False),
                    RefreshToken.expires_at > now
                )
            )
            .first()
        )