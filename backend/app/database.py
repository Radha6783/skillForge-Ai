import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, DeclarativeBase

load_dotenv()

# Database URL from environment variables
# Example PostgreSQL: postgresql://postgres:postgres@localhost:5432/skillforge_db
# Default fallback to local sqlite database for development if DATABASE_URL is not set or unavailable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skillforge_db.sqlite")

# Handle SQLAlchemy dialect fix for PostgreSQL (psycopg2)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Configure engine options based on driver
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create SessionLocal class for DB session creation
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative ORM models
class Base(DeclarativeBase):
    pass

# Dependency for FastAPI routers to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
