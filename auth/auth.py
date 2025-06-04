"""
Authentication utilities for Streamlit using Auth0 as the identity provider.
Auth0 handles domain and user access control natively through Rules and User Management.
"""

import streamlit as st
from functools import wraps, lru_cache
from typing import Optional, List, Callable, Dict
import os
from dataclasses import dataclass, field

# @lru_cache(maxsize=1)
def _get_auth_provider_name() -> str:
    provider = os.getenv("STREAMLIT_AUTH_PROVIDER")
    if not provider:
        # Fallback for safety, though Streamlit usually requires it for login to be configured
        st.error("STREAMLIT_AUTH_PROVIDER environment variable is not set.")
        return "auth0" # Default to auth0 if not set, but this is a config error
    return provider

# @lru_cache(maxsize=1)
def _get_roles_claim_namespace() -> str:
    """Constructs the namespace for roles claim in the ID token."""
    app_url = os.getenv("STREAMLIT_AUTH_REDIRECT_URI", "").replace("/oauth2callback", "")
    if not app_url:
        # Fallback to localhost for development if not set or empty
        app_url = "http://localhost:8501"
    return f"{app_url}/claims/roles"

@dataclass
class User:
    email: str
    email_verified: bool
    _raw_user_obj: dict = field(repr=False)
    _roles: Optional[List[str]] = field(default=None, init=False, repr=False)

    @property
    def roles(self) -> List[str]:
        if self._roles is None:
            roles_claim = _get_roles_claim_namespace()
            self._roles = self._raw_user_obj.get(roles_claim, [])
        return self._roles

    @classmethod
    def from_st_user(cls, st_user_obj) -> Optional['User']:
        if not st_user_obj or not hasattr(st_user_obj, 'email'):
            return None
        return cls(
            email=st_user_obj.email,
            email_verified=getattr(st_user_obj, 'email_verified', False),
            _raw_user_obj=st_user_obj.to_dict() if hasattr(st_user_obj, 'to_dict') else {}
        )

# @lru_cache(maxsize=1) # Cache the user object for the duration of a script run
def get_current_user() -> Optional[User]:
    """
    Retrieves the current authenticated user.
    Tries st.user first, then falls back to st.experimental_user.
    Returns a User object or None if not authenticated.
    """
    st_user = None
    if hasattr(st, 'user') and hasattr(st.user, 'is_logged_in'):
        if st.user.is_logged_in:
            st_user = st.user
    elif hasattr(st, 'experimental_user') and hasattr(st.experimental_user, 'is_logged_in'):
        st.error("Using deprecated st.experimental_user API. Will be removed after 2025-11-06.")
        st.stop()

    if st_user:
        return User.from_st_user(st_user)
    return None

def render_auth_sidebar() -> None:
    """Render authentication UI in the sidebar.

    This should be called on every page load, typically from app.py,
    to ensure the login/logout UI is always available.
    """
    with st.sidebar:
        current_user = get_current_user()

        if current_user:
            st.write(f"👤 {current_user.email}")
            st.button(
                "🚪 Logout",
                on_click=st.logout,
                use_container_width=True
            )
            # Optional: Display email verification status or prompt
            # if not current_user.email_verified:
            #     st.warning("Please verify your email.", icon="📧")
        else:
            auth_provider_name = _get_auth_provider_name()
            provider_display_name = auth_provider_name.capitalize()
            st.info("🔐 Please log in to access all features")
            st.button(
                f"Login with {provider_display_name}",
                on_click=st.login,
                kwargs={"provider": auth_provider_name},
                use_container_width=True,
                type="primary"
            )


# The functions `check_auth` and `require_auth` are now considered deprecated.
# Page protection should be handled by `components.rbac.require_page_access`.
# `is_authenticated` is replaced by checking if `get_current_user()` returns a User object.
# `_get_auth_provider_or_raise` is replaced by internal `_get_auth_provider_name`.

# Example of how email verification check, previously in check_auth, can be done in a page
# if user := get_current_user():
#     if not user.email_verified:
#         st.toast(f"Verify your email ({user.email})", icon="📧")
#         st.warning(f"Please verify your email (`{user.email}`) to access all features.\n\n"
#                    "An administrator can resend the verification email or manually verify "
#                    "your account via the Auth0 Dashboard (User Management > Users).")
#         st.stop()