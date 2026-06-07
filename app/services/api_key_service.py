from uuid import UUID
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import secrets
import hashlib

from app.repositories.api_key_repository import APIKeyRepository
from app.models.api_key import APIKey


class APIKeyNotFoundError(Exception):
    """Raised when API key does not exist."""
    pass


class InvalidAPIKeyError(Exception):
    """Raised when API key is invalid or deactivated."""
    pass


class APIKeyExpiredError(Exception):
    """Raised when API key has expired."""
    pass


class APIKeyService:
    def __init__(self, api_key_repository: APIKeyRepository):
        self.api_key_repository = api_key_repository

    def _generate_api_key(self) -> tuple[str, str, str]:
        """Generate API key, hash, and prefix."""
        random_part = secrets.token_hex(32)
        plain_key = f"bb_live_{random_part}"
        
        prefix = plain_key[:10]
        
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        
        return plain_key, key_hash, prefix

    def create_api_key(
        self,
        user_id: UUID,
        name: str,
        agent_id: Optional[UUID] = None,
        expires_in_days: Optional[int] = None
    ) -> tuple[APIKey, str]:
        """
        Create a new API key.
        
        Args:
            user_id: User ID
            name: Key name for identification
            agent_id: Optional agent ID to scope key to specific agent
            expires_in_days: Optional expiry in days
        
        Returns:
            Tuple of (APIKey object, plain_text_key)
        """
        if not name or not name.strip():
            raise ValueError("Key name cannot be empty")
        
        plain_key, key_hash, prefix = self._generate_api_key()
        
        expires_at = None
        if expires_in_days is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        api_key = self.api_key_repository.create_api_key(
            user_id=user_id,
            key_hash=key_hash,
            prefix=prefix,
            name=name.strip(),
            agent_id=agent_id,
            expires_at=expires_at
        )
        
        return api_key, plain_key

    def validate_api_key(self, plain_key: str) -> APIKey:
        """
        Validate an API key.
        
        Args:
            plain_key: Plain text API key
        
        Returns:
            Validated APIKey object
        
        Raises:
            InvalidAPIKeyError: If key format is invalid or key not found
            APIKeyExpiredError: If key has expired
        """
        plain_key = plain_key.strip()
        
        if not plain_key.startswith('bb_live_'):
            raise InvalidAPIKeyError("Invalid API key format")
        
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        
        api_key = self.api_key_repository.get_valid_key_by_hash(key_hash)
        
        if not api_key:
            raise InvalidAPIKeyError("Invalid or deactivated API key")
        
        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            raise APIKeyExpiredError(f"API key expired on {api_key.expires_at}")
        
        self.api_key_repository.update_last_used(api_key.id)
        
        return api_key

    def get_key_by_id(self, key_id: UUID, user_id: UUID) -> APIKey:
        """Get API key by ID with ownership check."""
        api_key = self.api_key_repository.get_by_id(key_id)
        
        if not api_key:
            raise APIKeyNotFoundError(f"API key {key_id} not found")
        
        if api_key.user_id != user_id:
            raise APIKeyNotFoundError(f"API key {key_id} not found")
        
        return api_key

    def deactivate_key(self, key_id: UUID, user_id: UUID) -> APIKey:
        """Deactivate an API key."""
        api_key = self.get_key_by_id(key_id, user_id)
        
        if not api_key.is_active:
            return api_key
        
        deactivated_key = self.api_key_repository.deactivate_key(key_id)
        
        if not deactivated_key:
            raise APIKeyNotFoundError(f"API key {key_id} not found")
        
        return deactivated_key

    def get_user_keys(
        self,
        user_id: UUID,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[APIKey]:
        """Get all API keys for a user."""
        if include_inactive:
            return self.api_key_repository.get_by_user(user_id, skip, limit)
        else:
            return self.api_key_repository.get_active_keys_by_user(user_id, skip, limit)

    def get_agent_keys(
        self,
        agent_id: UUID,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[APIKey]:
        """Get all API keys for an agent."""
        if include_inactive:
            return self.api_key_repository.get_by_agent(agent_id, skip, limit)
        else:
            return self.api_key_repository.get_active_keys_by_agent(agent_id, skip, limit)

    def delete_key(self, key_id: UUID, user_id: UUID) -> bool:
        """Permanently delete an API key."""
        self.get_key_by_id(key_id, user_id)
        
        deleted = self.api_key_repository.delete_key(key_id)
        
        if not deleted:
            raise APIKeyNotFoundError(f"API key {key_id} not found")
        
        return True

    def rotate_key(
        self,
        key_id: UUID,
        user_id: UUID,
        expires_in_days: Optional[int] = None
    ) -> tuple[APIKey, str]:
        """
        Rotate an existing API key.
        
        Creates a new key and deactivates the old one.
        """
        old_key = self.get_key_by_id(key_id, user_id)
        
        self.deactivate_key(key_id, user_id)
        
        new_api_key, new_plain_key = self.create_api_key(
            user_id=user_id,
            name=f"{old_key.name} (Rotated)",
            agent_id=old_key.agent_id,
            expires_in_days=expires_in_days
        )
        
        return new_api_key, new_plain_key

    def count_active_keys(self, user_id: UUID) -> int:
        """Count active API keys for a user."""
        return self.api_key_repository.count_active_keys(user_id)

    def cleanup_expired_keys(self) -> int:
        """Deactivate all expired keys. Returns count of deactivated keys."""
        expired_keys = self.api_key_repository.get_expired_keys()
        
        count = 0
        for key in expired_keys:
            self.api_key_repository.deactivate_key(key.id)
            count += 1
        
        return count
    