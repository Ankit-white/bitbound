from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.repositories.api_key_repository import APIKeyRepository
from app.services.api_key_service import (
    APIKeyService,
    APIKeyNotFoundError
)
from app.models.user import User


router = APIRouter(
    prefix="/api-keys",
    tags=["API Keys"]
)


class CreateAPIKeyRequest(BaseModel):
    name: str
    agent_id: Optional[UUID] = None
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: UUID
    name: str
    prefix: str
    agent_id: Optional[UUID]
    is_active: bool
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    api_key: str
    key: APIKeyResponse


class APIKeyListResponse(BaseModel):
    items: List[APIKeyResponse]
    total: int


def get_api_key_service(db: Session = Depends(get_db)) -> APIKeyService:
    api_key_repo = APIKeyRepository(db)
    return APIKeyService(api_key_repo)


@router.post("/", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    request: CreateAPIKeyRequest,
    current_user: User = Depends(get_current_user),
    service: APIKeyService = Depends(get_api_key_service)
):
    """
    Create a new API key.
    
    Returns the plain text API key only once. Store it securely.
    """
    try:
        api_key, plain_key = service.create_api_key(
            user_id=current_user.id,
            name=request.name,
            agent_id=request.agent_id,
            expires_in_days=request.expires_in_days
        )
        
        return APIKeyCreateResponse(
            api_key=plain_key,
            key=APIKeyResponse.model_validate(api_key)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=APIKeyListResponse)
def get_api_keys(
    include_inactive: bool = Query(False, description="Include inactive keys"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: APIKeyService = Depends(get_api_key_service)
):
    """
    List all API keys for the current user.
    """
    keys = service.get_user_keys(
        user_id=current_user.id,
        include_inactive=include_inactive,
        skip=skip,
        limit=limit
    )
    
    return APIKeyListResponse(
        items=[APIKeyResponse.model_validate(key) for key in keys],
        total=len(keys)
    )


@router.get("/{key_id}", response_model=APIKeyResponse)
def get_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    service: APIKeyService = Depends(get_api_key_service)
):
    """
    Get a single API key by ID.
    """
    try:
        api_key = service.get_key_by_id(key_id, current_user.id)
        return APIKeyResponse.model_validate(api_key)
    except APIKeyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{key_id}/rotate", response_model=APIKeyCreateResponse)
def rotate_api_key(
    key_id: UUID,
    expires_in_days: Optional[int] = Query(None, description="New expiry in days for the rotated key"),
    current_user: User = Depends(get_current_user),
    service: APIKeyService = Depends(get_api_key_service)
):
    """
    Rotate an API key.
    
    Deactivates the old key and creates a new one.
    Returns the new plain text API key only once.
    """
    try:
        new_api_key, new_plain_key = service.rotate_key(
            key_id=key_id,
            user_id=current_user.id,
            expires_in_days=expires_in_days
        )
        
        return APIKeyCreateResponse(
            api_key=new_plain_key,
            key=APIKeyResponse.model_validate(new_api_key)
        )
    except APIKeyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{key_id}/deactivate", response_model=APIKeyResponse)
def deactivate_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    service: APIKeyService = Depends(get_api_key_service)
):
    """
    Deactivate an API key.
    
    Deactivated keys cannot be used for authentication.
    """
    try:
        api_key = service.deactivate_key(key_id, current_user.id)
        return APIKeyResponse.model_validate(api_key)
    except APIKeyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    service: APIKeyService = Depends(get_api_key_service)
):
    """
    Permanently delete an API key.
    """
    try:
        service.delete_key(key_id, current_user.id)
    except APIKeyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )