from uuid import UUID
from typing import Optional

from app.models.credit_package import CreditPackage
from app.repositories.credit_package_repository import CreditPackageRepository


class PackageNotFoundError(Exception):
    pass


class PackageAlreadyExistsError(Exception):
    pass


class InvalidPackageValueError(Exception):
    pass


class CreditPackageService:
    def __init__(self, package_repo: CreditPackageRepository):
        self.package_repo = package_repo

    def create_package(
        self,
        name: str,
        price: float,
        credits: float,
        description: Optional[str] = None
    ) -> CreditPackage:
        if not name or not name.strip():
            raise InvalidPackageValueError("Package name cannot be empty")
        
        if price <= 0:
            raise InvalidPackageValueError(f"Price must be greater than 0. Got: {price}")
        
        if credits <= 0:
            raise InvalidPackageValueError(f"Credits must be greater than 0. Got: {credits}")
        
        name = name.strip()
        existing = self.package_repo.get_package_by_name(name)
        if existing:
            raise PackageAlreadyExistsError(f"Package with name '{name}' already exists")
        
        return self.package_repo.create_package(
            name=name,
            price=price,
            credits=credits,
            description=description
        )

    def update_package(
        self,
        package_id: UUID,
        name: Optional[str] = None,
        price: Optional[float] = None,
        credits: Optional[float] = None,
        description: Optional[str] = None
    ) -> CreditPackage:
        package = self.get_package(package_id)
        
        if name is not None:
            if not name or not name.strip():
                raise InvalidPackageValueError("Package name cannot be empty")
            
            normalized_name = name.strip()
            if normalized_name.lower() != package.name.lower():
                existing = self.package_repo.get_package_by_name(normalized_name)
                if existing and existing.id != package_id:
                    raise PackageAlreadyExistsError(f"Package with name '{normalized_name}' already exists")
            
            final_name = normalized_name
        else:
            final_name = None
        
        if price is not None and price <= 0:
            raise InvalidPackageValueError(f"Price must be greater than 0. Got: {price}")
        
        if credits is not None and credits <= 0:
            raise InvalidPackageValueError(f"Credits must be greater than 0. Got: {credits}")
        
        updated_package = self.package_repo.update_package(
            package_id=package_id,
            name=final_name,
            description=description,
            price=price,
            credits=credits
        )
        
        if not updated_package:
            raise PackageNotFoundError(f"Package {package_id} not found")
        
        return updated_package

    def get_package(self, package_id: UUID) -> CreditPackage:
        package = self.package_repo.get_package_by_id(package_id)
        if not package:
            raise PackageNotFoundError(f"Package {package_id} not found")
        return package

    def get_package_by_name(self, name: str) -> Optional[CreditPackage]:
        return self.package_repo.get_package_by_name(name)

    def get_active_packages(self) -> list[CreditPackage]:
        return self.package_repo.get_active_packages()

    def get_all_packages(self, skip: int = 0, limit: int = 100) -> list[CreditPackage]:
        return self.package_repo.get_all_packages(skip, limit)

    def activate_package(self, package_id: UUID) -> CreditPackage:
        package = self.get_package(package_id)
        
        if package.is_active:
            return package
        
        return self.package_repo.update_package_status(package_id, True)

    def deactivate_package(self, package_id: UUID) -> CreditPackage:
        package = self.get_package(package_id)
        
        if not package.is_active:
            return package
        
        return self.package_repo.update_package_status(package_id, False)

    def delete_package(self, package_id: UUID) -> bool:
        package = self.get_package(package_id)
        return self.package_repo.delete_package(package_id)