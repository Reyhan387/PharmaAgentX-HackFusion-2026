from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# ===============================
# Database URL
# ===============================

DATABASE_URL = "sqlite:///./pharmaagentx.db"

# ===============================
# Engine
# ===============================

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite
)

# ===============================
# Session Factory
# ===============================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ===============================
# Base Class
# ===============================

Base = declarative_base()

# ===============================
# FastAPI Dependency
# ===============================

def get_db():
    """
    Dependency for getting DB session.
    Used in API routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()