from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Configure connection arguments based on database engine
connect_args = {}
engine_kwargs = {
    "pool_pre_ping": settings.DB_POOL_PRE_PING
}

if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    engine_kwargs["connect_args"] = connect_args
else:
    # PostgreSQL / MySQL connection pool configuration
    engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT

engine = create_engine(
    settings.DATABASE_URL,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator:
    """Dependency that yields a database session and safely rolls back and closes it."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

