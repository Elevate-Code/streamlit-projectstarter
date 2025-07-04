# Role-Based Access Control

This ia a follow up to the [authentication.md](authentication.md) file.


**Relevant Files:**
- `views/auth_admin.py` the Streamlit admin interface, how users are invited and managed
- `auth/auth.py` for core auth functionality
- `auth/rbac.py` for role-based page access controls
- `db/models.py` the database model for storing user roles and permissions
- `db/migrations.py` the database migrations for creating and updating the database schema

## pages.py

The `get_default_page_access_config()` function in `utils/pages.py` provides the initial RBAC configuration that gets loaded when no configuration exists in the database. This default config is critical for bootstrapping the system.

**Key constraints enforced by the system:**
- `views/home.py` must always be public
- `views/user_admin.py` must always require the "admin" role and cannot be public
- Available roles are defined in `AVAILABLE_ROLES = ["admin", "users"]`
- Pages not explicitly listed will use the `default_access` setting

Once deployed and the database is populated, admins can modify these settings through the Auth Admin interface, which saves changes to the database and overrides the default configuration.

## Database Model

In a `models.db` file (or search for equivalent) have something like:

```python
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
    """
    __tablename__ = 'app_settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, comment="Setting name/identifier")
    value = Column(String(1000), nullable=False, comment="Setting value stored as string or JSON")
    description = Column(String(500), nullable=True, comment="Optional description of what this setting does")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Ensure category+key combination is unique
    __table_args__ = (
        Index('idx_app_settings_category_key', 'category', 'key', unique=True),
    )
```