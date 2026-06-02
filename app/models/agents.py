from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Agent(BaseModel):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    wallet_address: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    balance: Mapped[float] = mapped_column(Numeric(18, 8), default=0.0, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="agents")

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.name}, user_id={self.user_id})>"

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "wallet_address": self.wallet_address,
            "user_id": str(self.user_id),
            "balance": float(self.balance),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }