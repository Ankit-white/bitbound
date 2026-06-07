from typing import Optional

from sqlalchemy import Boolean, Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Capability(BaseModel):
    __tablename__ = "capabilities"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    credit_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("idx_capabilities_name", "name"),
        Index("idx_capabilities_category", "category"),
        Index("idx_capabilities_active", "is_active"),
    )
