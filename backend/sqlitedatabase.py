from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, DeclarativeMeta
from databases import Database

DATABASE_URL = "sqlite:///./test.db"  # Async SQLite URL
# For other databases like PostgreSQL, use the appropriate database URL

# SQLAlchemy setup for model definition. This won't change.
Base: DeclarativeMeta = declarative_base()

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Databases library setup
database = Database(DATABASE_URL)

# SessionLocal for compatibility with synchronous operations if needed
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
