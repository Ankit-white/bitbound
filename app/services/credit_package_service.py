from uuid import UUID

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
        description: str | None = None
    ) -> CreditPackage:
        if price <= 0:
            raise InvalidPackageValueError(f"Price must be greater than 0. Got: {price}")
        
        if credits <= 0:
            raise InvalidPackageValueError(f"Credits must be greater than 0. Got: {credits}")
        
        existing = self.package_repo.get_package_by_name(name)
        if existing:
            raise PackageAlreadyExistsError(f"Package with name '{name}' already exists")
        
        return self.package_repo.create_package(
            name=name,
            price=price,
            credits=credits,
            description=description
        )

    def get_package(self, package_id: UUID) -> CreditPackage:
        package = self.package_repo.get_package_by_id(package_id)
        if not package:
            raise PackageNotFoundError(f"Package {package_id} not found")
        return package

    def get_package_by_name(self, name: str) -> CreditPackage | None:
        return self.package_repo.get_package_by_name(name)

    def get_active_packages(self) -> list[CreditPackage]:
        return self.package_repo.get_active_packages()

    def get_all_packages(self) -> list[CreditPackage]:
        return self.package_repo.get_all_packages()

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