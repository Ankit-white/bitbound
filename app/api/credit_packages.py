from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.repositories.credit_package_repository import CreditPackageRepository
from app.schemas.credit_package import (
    CreditPackageCreateRequest,
    CreditPackageListResponse,
    CreditPackageResponse,
)
from app.services.credit_package_service import (
    CreditPackageService,
    InvalidPackageValueError,
    PackageAlreadyExistsError,
    PackageNotFoundError,
)

router = APIRouter(prefix="/credit-packages", tags=["Credit Packages"])


@router.post(
    "/",
    response_model=CreditPackageResponse,
    status_code=status.HTTP_201_CREATED
)
def create_package(
    request: CreditPackageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    package_repo = CreditPackageRepository(db)
    package_service = CreditPackageService(package_repo)
    
    try:
        package = package_service.create_package(
            name=request.name,
            price=request.price,
            credits=request.credits,
            description=request.description,
        )
        return package
    except PackageAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidPackageValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=CreditPackageListResponse)
def get_active_packages(
    db: Session = Depends(get_db),
):
    package_repo = CreditPackageRepository(db)
    package_service = CreditPackageService(package_repo)
    
    packages = package_service.get_active_packages()
    
    return CreditPackageListResponse(packages=packages, total=len(packages))


@router.get("/all", response_model=CreditPackageListResponse)
def get_all_packages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    package_repo = CreditPackageRepository(db)
    package_service = CreditPackageService(package_repo)
    
    packages = package_service.get_all_packages()
    
    return CreditPackageListResponse(packages=packages, total=len(packages))


@router.get("/{package_id}", response_model=CreditPackageResponse)
def get_package(
    package_id: UUID,
    db: Session = Depends(get_db),
):
    package_repo = CreditPackageRepository(db)
    package_service = CreditPackageService(package_repo)
    
    try:
        package = package_service.get_package(package_id)
        return package
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{package_id}/activate", response_model=CreditPackageResponse)
def activate_package(
    package_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    package_repo = CreditPackageRepository(db)
    package_service = CreditPackageService(package_repo)
    
    try:
        package = package_service.activate_package(package_id)
        return package
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{package_id}/deactivate", response_model=CreditPackageResponse)
def deactivate_package(
    package_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    package_repo = CreditPackageRepository(db)
    package_service = CreditPackageService(package_repo)
    
    try:
        package = package_service.deactivate_package(package_id)
        return package
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    package_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    package_repo = CreditPackageRepository(db)
    package_service = CreditPackageService(package_repo)
    
    try:
        package_service.delete_package(package_id)
    except PackageNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))