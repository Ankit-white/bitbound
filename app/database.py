import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

load_dotenv()

def _validate_required_config() -> None:
    required_vars = [
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_NAME",
        "DATABASE_USER",
        "DATABASE_PASSWORD",
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

_validate_required_config()

def _build_connection_string() -> str:
    host = os.getenv("DATABASE_HOST")
    port = os.getenv("DATABASE_PORT")
    name = os.getenv("DATABASE_NAME")
    user = os.getenv("DATABASE_USER")
    password = os.getenv("DATABASE_PASSWORD")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"

def _get_pool_size() -> int:
    environment = os.getenv("ENVIRONMENT", "production").lower()
    if environment == "development":
        return int(os.getenv("DATABASE_POOL_SIZE", "5"))
    return int(os.getenv("DATABASE_POOL_SIZE", "20"))

def _get_max_overflow() -> int:
    return int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

def _get_pool_recycle() -> int:
    return int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

def _is_echo_enabled() -> bool:
    return os.getenv("DATABASE_ECHO", "false").lower() == "true"

engine = create_engine(
    _build_connection_string(),
    poolclass=QueuePool,
    pool_size=_get_pool_size(),
    max_overflow=_get_max_overflow(),
    pool_pre_ping=True,
    pool_recycle=_get_pool_recycle(),
    echo=_is_echo_enabled(),
    connect_args={
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
    isolation_level="READ COMMITTED",
    future=True,
)

@event.listens_for(engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    pass

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    pass

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    expire_on_commit=True,
)

class CustomBase:
    __allow_unmapped__ = False

Base = declarative_base(cls=CustomBase)

def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def check_database_health() -> dict:
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()
        
        pool = engine.pool
        
        return {
            "status": "healthy",
            "pool_size": pool.size(),
            "pool_overflow": pool.overflow(),
            "pool_checked_in": pool.checkedin(),
            "pool_checked_out": pool.checkedout(),
            "engine_connected": True,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "pool_size": 0,
            "pool_overflow": 0,
            "pool_checked_in": 0,
            "pool_checked_out": 0,
        }

def dispose_engine() -> None:
    engine.dispose()

__all__ = [
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "check_database_health",
    "dispose_engine",
]