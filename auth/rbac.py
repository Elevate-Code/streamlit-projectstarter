"""
Role-Based Access Control (RBAC) for Streamlit pages.

This module provides functionality to control page access based on user roles.
Page access configuration is stored in the database and can be managed through
the Auth Admin interface.
"""

import streamlit as st
from typing import List, Dict, Optional
import json
import os
from db.models import Session as SessionFactory, AppSettings
from auth.auth import get_current_user  # Updated import
from pages import get_default_page_access_config
from datetime import datetime

AVAILABLE_ROLES = ["admin", "users"]


def get_user_roles() -> List[str]:
    """Return the current user's roles, or an empty list if not logged in or no roles."""
    current_user = get_current_user()
    if not current_user:
        return []
    return current_user.roles  # Access roles via the User object's property


# @st.cache_data(ttl=60, show_spinner=False)
def _fetch_page_access_config() -> Dict:
    """Internal helper that actually queries the DB (cached)."""
    # Moved SessionFactory inside to only run on cache miss
    with SessionFactory() as session:
        setting = session.query(AppSettings).filter(
            AppSettings.key == 'page_access'
        ).first()

        if setting:
            try:
                return json.loads(setting.value)
            except json.JSONDecodeError:
                st.error("Error decoding page access config from DB. Falling back to defaults.")
                # Fall through to default if JSON is corrupted
        return get_default_page_access_config()


def load_page_access_config() -> Dict:
    """Return the cached page-access configuration dict."""
    return _fetch_page_access_config()


def save_page_access_config(config: Dict) -> bool:
    """Save page access configuration to database.

    Args:
        config: Page access configuration dict.

    Returns:
        True if saved successfully, False otherwise.
    """
    try:
        with SessionFactory() as session:
            setting = session.query(AppSettings).filter(
                AppSettings.key == 'page_access'
            ).first()

            config_json = json.dumps(config, indent=2)

            if setting:
                setting.value = config_json
            else:
                setting = AppSettings(
                    key='page_access',
                    value=config_json,
                    description='Page access control configuration'
                )
                session.add(setting)

            session.commit()
            # Invalidate the cached copy so next call fetches fresh data
            # TODO: re-enable once we have fully debugged auth and caching is added back in
            # _fetch_page_access_config.clear()
            return True
    except Exception as e:
        st.error(f"Error saving page access config: {str(e)}")
        return False


def can_access_page(page_path: str, current_user: Optional[object], config: Optional[Dict] = None) -> bool:
    """Check if user can access a specific page.

    Args:
        page_path: Path to the page file (e.g., "views/reports.py").
        current_user: The current User object (from get_current_user()) or None.
        config: Optional page access config. If not provided, will be loaded from database.

    Returns:
        True if user can access the page, False otherwise.
    """
    if config is None:
        config = load_page_access_config()

    page_config = config["pages"].get(page_path, {})

    # Check if page is explicitly public
    if page_config.get("access") == "public":
        return True

    # User must be logged in for any non-public page
    if not current_user:
        return False

    # Check if page requires only authentication (no specific roles)
    if page_config.get("access") == "authenticated":
        return True  # Already checked current_user is not None

    # If no roles specified in page config, use default access
    if "roles" not in page_config:
        default = config.get("default_access", "authenticated")
        # For pages without explicit role requirements we honour the default_access value.
        # Because we have already confirmed the user is authenticated, any value other than
        # "deny" results in access.
        return default != "deny"

    # For pages with specific role requirements
    required_roles = page_config.get("roles", [])
    user_roles = current_user.roles if hasattr(current_user, 'roles') else []

    # If user has no roles but is authenticated, they can't access role-protected pages
    # unless the page has an empty roles list (meaning any authenticated user with *any* role, though this is unusual)
    if not required_roles:  # Page explicitly allows any authenticated user (empty roles list)
        return True

    if not user_roles and required_roles:  # User has no roles, but page requires specific roles
        return False

    # Check if user has any of the required roles
    return any(role in required_roles for role in user_roles)


def filter_pages_by_access(all_pages: List[Dict], current_user: Optional[object]) -> List[Dict]:
    """Filter pages based on user's access permissions.

    Args:
        all_pages: List of all page definitions.
        current_user: The current User object or None.

    Returns:
        List of pages the user can access.
    """
    config = load_page_access_config()
    accessible_pages = []

    for page_info in all_pages:
        if can_access_page(page_info["file"], current_user, config):
            accessible_pages.append(page_info)

    return accessible_pages


def create_navigation_pages(all_pages: List[Dict]) -> List:
    """Create Streamlit Page objects for pages the current user can access.

    Args:
        all_pages: List of all page definitions.

    Returns:
        List of st.Page objects for accessible pages.
    """
    current_user = get_current_user()
    accessible_pages = filter_pages_by_access(all_pages, current_user)

    pages = []
    for page_info in accessible_pages:
        page = st.Page(
            page_info["file"],
            title=page_info["title"],
            icon=page_info["icon"],
            default=page_info.get("default", False)
        )
        pages.append(page)

    return pages


def require_page_access(page_path: str) -> None:
    """Check if current user can access the page and if their email is verified, stop execution if not.

    This should be called at the top of each protected page.

    Args:
        page_path: Path to the current page file.
    """
    current_user = get_current_user()

    if not can_access_page(page_path, current_user):
        user_roles_display = ", ".join(current_user.roles) if current_user and current_user.roles else "None"
        auth_status = "Authenticated" if current_user else "Not Authenticated"
        st.error("🚫 You don't have permission to access this page.")
        st.info(f"Authentication: {auth_status}. Your roles: {user_roles_display}.")
        st.stop()

    # Check email verification for non-public pages after permission check
    # We only do this if the user *could* access the page, but might be blocked by email verification
    page_config = load_page_access_config()["pages"].get(page_path, {})
    is_public_page = page_config.get("access") == "public"

    if current_user and not current_user.email_verified and not is_public_page:
        st.toast(f"Verify your email ({current_user.email}) to access all features.", icon="📧")
        st.warning(
            f"Please verify your email (`{current_user.email}`) to continue.\n\n"
            f"An administrator can resend the verification email or manually verify "
            f"your account via the Auth0 Dashboard (User Management > Users).")
        # Optionally, show st.user details if needed for debugging
        # if hasattr(st, 'user') and st.user:
        #     st.json(st.user.to_dict())
        st.stop()