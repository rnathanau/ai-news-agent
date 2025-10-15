"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - supports both PostgreSQL and SQLite for development
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./news_agent.db"  # Default to SQLite for easy local dev
)

# SQLite-specific: Add check_same_thread=False for FastAPI compatibility
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db() -> Generator:
    """Dependency for getting database sessions in FastAPI endpoints.
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables.
    
    Should be called on application startup.
    """
    # Import all models to ensure they're registered with Base
    from backend import models  # noqa: F401
    
    Base.metadata.create_all(bind=engine)

