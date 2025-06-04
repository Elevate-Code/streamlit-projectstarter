# Database models and schema definitions
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DB_URL = os.getenv('DATABASE_URL')

# Only create engine and Session if database URL is provided
# This is purely to allow for local dev until we have a database in place
if DB_URL:
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
else:
    # engine = None
    Session = None

Base = declarative_base()

#NOTE: The User and AppSettings tables are primarily here for Auth/RBAC. If you don't need them, you can remove them.

class User(Base):
    """Stores user information and preferences synchronized from Auth0."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False, unique=True, index=True, comment="User's email address from Auth0")
    auth0_user_id = Column(String(255), nullable=False, unique=True, index=True, comment="Auth0 user ID (e.g., auth0|123456)")
    roles = Column(JSONB, nullable=False, default=list, server_default='[]', comment="List of user roles")
    user_preferences = Column(JSONB, nullable=True, comment="User-specific preferences and settings")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in (self.roles or [])

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        user_roles = self.roles or []
        return any(role in user_roles for role in roles)

class AppSettings(Base):
    """
    Generic settings table for storing application-wide configuration values.
    Each setting is stored as a key-value pair with metadata.
    """
    __tablename__ = 'app_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, comment="Setting name/identifier")
    value = Column(String(1000), nullable=False, comment="Setting value stored as string or JSON")
    description = Column(String(500), nullable=True, comment="Optional description of what this setting does")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ensure key is unique
    __table_args__ = (
        Index('idx_app_settings_key', 'key', unique=True),
    )

# NOTE: Database tables are not automatically created.
# To create tables, set up a proper PostgreSQL database on Railway and run migrations:
#    python -c "from db.models import Base, engine; Base.metadata.create_all(engine)"
# Removed automatic creation: Base.metadata.create_all(engine)
