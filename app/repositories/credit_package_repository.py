from uuid import UUID
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.credit_package import CreditPackage


class CreditPackageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_package(
        self,
        name: str,
        price: float,
        credits: float,
        description: Optional[str] = None
    ) -> CreditPackage:
        package = CreditPackage(
            name=name,
            description=description,
            price=price,
            credits=credits,
            is_active=True
        )
        self.db.add(package)
        try:
            self.db.commit()
            self.db.refresh(package)
            return package
        except Exception:
            self.db.rollback()
            raise

    def get_package_by_id(self, package_id: UUID) -> Optional[CreditPackage]:
        return self.db.query(CreditPackage).filter(CreditPackage.id == package_id).first()

    def get_package_by_name(self, name: str) -> Optional[CreditPackage]:
        return self.db.query(CreditPackage).filter(CreditPackage.name == name).first()

    def get_active_packages(self) -> List[CreditPackage]:
        return (
            self.db.query(CreditPackage)
            .filter(CreditPackage.is_active.is_(True))
            .order_by(CreditPackage.price.asc())
            .all()
        )

    def get_all_packages(self, skip: int = 0, limit: int = 100) -> List[CreditPackage]:
        return (
            self.db.query(CreditPackage)
            .order_by(CreditPackage.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_package(
        self,
        package_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[float] = None,
        credits: Optional[float] = None
    ) -> Optional[CreditPackage]:
        package = self.get_package_by_id(package_id)
        if not package:
            return None
        
        if name is not None:
            package.name = name
        if description is not None:
            package.description = description
        if price is not None:
            package.price = price
        if credits is not None:
            package.credits = credits
        
        try:
            self.db.commit()
            self.db.refresh(package)
            return package
        except Exception:
            self.db.rollback()
            raise

    def update_package_status(self, package_id: UUID, is_active: bool) -> Optional[CreditPackage]:
        package = self.get_package_by_id(package_id)
        if not package:
            return None
        
        package.is_active = is_active
        try:
            self.db.commit()
            self.db.refresh(package)
            return package
        except Exception:
            self.db.rollback()
            raise

    def delete_package(self, package_id: UUID) -> bool:
        package = self.get_package_by_id(package_id)
        if not package:
            return False
        
        self.db.delete(package)
        try:
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def get_packages_by_price_range(
        self,
        min_price: float,
        max_price: float,
        skip: int = 0,
        limit: int = 100
    ) -> List[CreditPackage]:
        return (
            self.db.query(CreditPackage)
            .filter(
                and_(
                    CreditPackage.price >= min_price,
                    CreditPackage.price <= max_price,
                    CreditPackage.is_active.is_(True)
                )
            )
            .order_by(CreditPackage.price.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )