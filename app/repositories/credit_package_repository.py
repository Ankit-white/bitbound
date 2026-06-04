from uuid import UUID

from sqlalchemy.orm import Session

from app.models.credit_package import CreditPackage


class CreditPackageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_package(
        self,
        name: str,
        price: float,
        credits: float,
        description: str | None = None
    ) -> CreditPackage:
        package = CreditPackage(
            name=name,
            description=description,
            price=price,
            credits=credits,
            is_active=True
        )
        self.db.add(package)
        self.db.commit()
        self.db.refresh(package)
        return package

    def get_package_by_id(self, package_id: UUID) -> CreditPackage | None:
        return self.db.query(CreditPackage).filter(CreditPackage.id == package_id).first()

    def get_package_by_name(self, name: str) -> CreditPackage | None:
        return self.db.query(CreditPackage).filter(CreditPackage.name == name).first()

    def get_active_packages(self) -> list[CreditPackage]:
        return (
            self.db.query(CreditPackage)
            .filter(CreditPackage.is_active == True)
            .order_by(CreditPackage.price.asc())
            .all()
        )

    def get_all_packages(self) -> list[CreditPackage]:
        return (
            self.db.query(CreditPackage)
            .order_by(CreditPackage.created_at.desc())
            .all()
        )

    def update_package_status(self, package_id: UUID, is_active: bool) -> CreditPackage | None:
        package = self.get_package_by_id(package_id)
        if not package:
            return None
        package.is_active = is_active
        self.db.commit()
        self.db.refresh(package)
        return package

    def delete_package(self, package_id: UUID) -> bool:
        package = self.get_package_by_id(package_id)
        if not package:
            return False
        self.db.delete(package)
        self.db.commit()
        return True