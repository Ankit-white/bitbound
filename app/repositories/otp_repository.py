from uuid import UUID
from typing import Optional

from sqlalchemy.orm import Session

from app.models.otp import OTP


class OTPRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_otp(
        self,
        user_id: UUID,
        otp_code: str,
        otp_type: str,
        expires_at
    ) -> OTP:
        otp = OTP(
            user_id=user_id,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at,
            is_used=False,
            attempts=0
        )

        self.db.add(otp)
        self.db.commit()
        self.db.refresh(otp)

        return otp

    def get_by_id(self, otp_id: UUID) -> Optional[OTP]:
        return (
            self.db.query(OTP)
            .filter(OTP.id == otp_id)
            .first()
        )

    def get_valid_otp(
        self,
        user_id: UUID,
        otp_code: str,
        otp_type: str
    ) -> Optional[OTP]:
        return (
            self.db.query(OTP)
            .filter(
                OTP.user_id == user_id,
                OTP.otp_code == otp_code,
                OTP.otp_type == otp_type,
                OTP.is_used == False
            )
            .first()
        )

    def get_latest_otp(
        self,
        user_id: UUID,
        otp_type: str
    ) -> Optional[OTP]:
        return (
            self.db.query(OTP)
            .filter(
                OTP.user_id == user_id,
                OTP.otp_type == otp_type
            )
            .order_by(OTP.created_at.desc())
            .first()
        )

    def update_otp(self, otp: OTP) -> OTP:
        self.db.commit()
        self.db.refresh(otp)
        return otp

    def delete_otp(self, otp_id: UUID) -> bool:
        otp = self.get_by_id(otp_id)

        if not otp:
            return False

        self.db.delete(otp)
        self.db.commit()

        return True
