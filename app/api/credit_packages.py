from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.auth.dependencies import get_current_user, require_admin
from app.models.user import User
from app.repositories.credit_package_repository import CreditPackageRepository
from app.services.credit_package_service import (
    CreditPackageService,
    InvalidPackageValueError,
    PackageAlreadyExistsError,
    PackageNotFoundError,
)


router = APIRouter(prefix="/credit-packages", tags=["Credit Packages"])


class CreditPackageCreateRequest(BaseModel):
    name: str
    price: float
    credits: float
    description: Optional[str] = None


class CreditPackageUpdateRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    credits: Optional[float] = None
    description: Optional[str] = None


class CreditPackageResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    price: float
    credits: float
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class CreditPackageListResponse(BaseModel):
    packages: list[CreditPackageResponse]
    total: int


def get_credit_package_service(db: Session = Depends(get_db)) -> CreditPackageService:
    package_repo = CreditPackageRepository(db)
    return CreditPackageService(package_repo)


@router.post(
    "/",
    response_model=CreditPackageResponse,
    status_code=status.HTTP_201_CREATED
)
def create_package(
    request: CreditPackageCreateRequest,
    admin: User = Depends(require_admin),
    service: CreditPackageService = Depends(get_credit_package_service)
):
    try:
        package = service.create_package(
            name=request.name,
            price=request.price,
            credits=request.credits,
            description=request.description,
        )
        return CreditPackageResponse.model_validate(package)
    except PackageAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidPackageValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=CreditPackageListResponse)
def get_active_packages(
    service: CreditPackageService = Depends(get_credit_package_service)
):
    packages = service.get_active_packages()
    return CreditPackageListResponse(
        packages=[CreditPackageResponse.model_validate(p) for p in packages],
        total=len(packages)
    )


@router.get("/all", response_model=CreditPackageListResponse)
def get_all_packages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    admin: User = Depends(require_admin),
    service: CreditPackageService = Depends(get_credit_package_service)
):
    packages = service.get_all_packages(skip, limit)
    return CreditPackageListResponse(
        packages=[CreditPackageResponse.model_validate(p) for p in packages],
        total=len(packages)
    )


@router.get("/{package_id}", response_model=CreditPackageResponse)
def get_package(
    package_id: UUID,
    service: CreditPackageService = Depends(get_credit_package_service)
):
    try:
        package = service.get_package(package_id)
        return CreditPackageResponse.model_validate(package)
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{package_id}", response_model=CreditPackageResponse)
def update_package(
    package_id: UUID,
    request: CreditPackageUpdateRequest,
    admin: User = Depends(require_admin),
    service: CreditPackageService = Depends(get_credit_package_service)
):
    try:
        package = service.update_package(
            package_id=package_id,
            name=request.name,
            price=request.price,
            credits=request.credits,
            description=request.description
        )
        return CreditPackageResponse.model_validate(package)
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PackageAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidPackageValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{package_id}/activate", response_model=CreditPackageResponse)
def activate_package(
    package_id: UUID,
    admin: User = Depends(require_admin),
    service: CreditPackageService = Depends(get_credit_package_service)
):
    try:
        package = service.activate_package(package_id)
        return CreditPackageResponse.model_validate(package)
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{package_id}/deactivate", response_model=CreditPackageResponse)
def deactivate_package(
    package_id: UUID,
    admin: User = Depends(require_admin),
    service: CreditPackageService = Depends(get_credit_package_service)
):
    try:
        package = service.deactivate_package(package_id)
        return CreditPackageResponse.model_validate(package)
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_package_soft_delete(
    package_id: UUID,
    admin: User = Depends(require_admin),
    service: CreditPackageService = Depends(get_credit_package_service)
):
    try:
        service.deactivate_package(package_id)
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))