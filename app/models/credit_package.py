from typing import Optional

from sqlalchemy import Boolean, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CreditPackage(BaseModel):
    __tablename__ = "credit_packages"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    price: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    credits: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    __table_args__ = (
        Index("idx_credit_packages_active", "is_active"),
        Index("idx_credit_packages_price", "price"),
    )

    def __repr__(self) -> str:
        return f"<CreditPackage(id={self.id}, name={self.name}, price={self.price}, credits={self.credits}, is_active={self.is_active})>"