from typing import Final

from passlib.context import CryptContext


class PasswordHasher:
    _context: Final = CryptContext(
        schemes=["bcrypt"],
        bcrypt__rounds=12,
        bcrypt__ident="2b",
        deprecated="auto"
    )

    @classmethod
    def hash_password(cls, plain_password: str) -> str:
        if not plain_password:
            raise ValueError("Password cannot be empty")
        
        return cls._context.hash(plain_password)

    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        if not plain_password or not hashed_password:
            return False
        
        return cls._context.verify(plain_password, hashed_password)