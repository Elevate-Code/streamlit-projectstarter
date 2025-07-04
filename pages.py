"""
Page definitions for the application.

This module contains the single source of truth for all pages in the application.
Both app.py and the RBAC system import from here.
"""

# Define all pages in the application
ALL_PAGES = [
    {"file": "views/home.py", "title": "Home", "icon": "🏠", "default": True},
    {"file": "views/state_scenarios.py", "title": "State Scenarios", "icon": "🔁"},
    {"file": "views/user_admin.py", "title": "User Admin", "icon": "🔐"},
]


def get_default_page_access_config():
    """
    Returns the minimal default page access configuration.

    This provides a fallback configuration with minimal access:
    - Home page is public
    - User Admin is admin-only
    - All other pages use the default access level
    """
    return {
        "version": "1.0",
        "default_access": "authenticated",  # Options: "public", "authenticated", "deny"
        # IMPORTANT: make sure the roles match the ones defined in rbac.py > AVAILABLE_ROLES
        "pages": {
            "views/home.py": {"access": "public"},  # Landing page is public
            "views/state_scenarios.py": {"access": "authenticated"},
            # "views/other_page.py": {"roles": ["admin", "users"]},
            "views/user_admin.py": {"roles": ["admin"]},  # Admin only
        }
    }