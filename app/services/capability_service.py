from uuid import UUID

from app.models.capability import Capability
from app.repositories.capability_repository import CapabilityRepository


class CapabilityNotFoundError(Exception):
    pass


class CapabilityAlreadyExistsError(Exception):
    pass


class CapabilityService:
    def __init__(self, capability_repository: CapabilityRepository):
        self.capability_repository = capability_repository

    def create_capability(
        self,
        name: str,
        description: str | None = None,
        category: str | None = None,
        credit_cost: float = 0.0,
        is_active: bool = True
    ) -> Capability:
        if self.capability_repository.get_by_name(name):
            raise CapabilityAlreadyExistsError(f"Capability {name} already exists")

        capability = Capability(
            name=name,
            description=description,
            category=category,
            credit_cost=credit_cost,
            is_active=is_active
        )
        return self.capability_repository.create(capability)

    def get_capability(self, capability_id: UUID) -> Capability:
        capability = self.capability_repository.get_by_id(capability_id)
        if not capability:
            raise CapabilityNotFoundError(f"Capability {capability_id} not found")
        return capability

    def list_active_capabilities(self) -> list[Capability]:
        return self.capability_repository.list_active()
