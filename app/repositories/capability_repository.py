from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.capability import Capability


class CapabilityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, capability: Capability) -> Capability:
        self.db.add(capability)
        self.db.commit()
        self.db.refresh(capability)
        return capability

    def get_by_id(self, capability_id: UUID) -> Optional[Capability]:
        return self.db.query(Capability).filter(Capability.id == capability_id).first()

    def get_by_name(self, name: str) -> Optional[Capability]:
        return self.db.query(Capability).filter(Capability.name == name).first()

    def list_active(self) -> list[Capability]:
        return (
            self.db.query(Capability)
            .filter(Capability.is_active.is_(True))
            .order_by(Capability.name.asc())
            .all()
        )

    def update(self, capability: Capability) -> Capability:
        self.db.commit()
        self.db.refresh(capability)
        return capability
