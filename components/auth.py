"""
Authentication utilities for Streamlit using Auth0 as the identity provider.
Auth0 handles domain and user access control natively through Rules and User Management.
"""

import streamlit as st
from functools import wraps
from typing import Optional, List, Callable
import os

# NOTE: The main app or page script (e.g., pages/authenticated.py) should handle load_dotenv().

def _get_auth_provider_or_raise() -> str:
    provider = os.getenv("STREAMLIT_AUTH_PROVIDER")
    if not provider:
        raise ValueError(
            "STREAMLIT_AUTH_PROVIDER environment variable is not set. "
            "This variable is required to specify the authentication provider (e.g., 'auth0'). "
            "Please ensure it is set in your environment (e.g., in a .env file or your shell) "
            "and matches the provider configuration in .streamlit/secrets.toml."
        )
    return provider

def check_auth(required_roles: Optional[List[str]] = None) -> None:
    """Check authentication and optionally roles, stopping execution if unauthorized.

    Args:
        required_roles: Optional list of roles required to access the page/component
    """
    if not st.experimental_user.is_logged_in:
        auth_provider_name = _get_auth_provider_or_raise()
        with st.sidebar:
            provider_display_name = auth_provider_name.capitalize()
            st.button(
                f"🔐 Login with {provider_display_name}",
                on_click=st.login,
                kwargs={"provider": auth_provider_name},
                use_container_width=True
            )
            st.warning("Please log in to continue")
        st.stop()

    with st.sidebar:
        st.write(f"Logged in as: {st.experimental_user.email}")
        st.button(
            "🚪 Logout",
            on_click=st.logout,
            use_container_width=True
        )

    # Check if user email is verified
    # TODO: Couldn't figure out how to use native Auth0 `if (!event.user.email_verified) {api.access.deny('...')}` as
    # of 2025-05-07 because Streamlit does not propagate errors that appear during the OAuth flow and user just gets
    # redirected back to home page without any indication of what went wrong.
    # See: https://github.com/streamlit/streamlit/issues/10160
    if not st.experimental_user.email_verified:
        st.toast(f"Verify your email ({st.experimental_user.email})", icon="📧")
        st.warning(f"Please verify your email (`{st.experimental_user.email}`) then log out and log back in.\n\nIf you have already verified your email, you may need to log out and log back in.\n\nAdmin can resend verification email or manually verify user via Auth0 Dashboard > User Management > Users")
        # st.json(st.experimental_user)
        st.stop()

    # Auth0 handles access control through Rules, so we don't need additional checks here
    # Future role-based access control can be implemented by checking Auth0 user metadata similar to how we are doing
    # it for `st.experimental_user.email_verified`

def require_auth(func: Optional[Callable] = None, *, roles: Optional[List[str]] = None) -> Callable:
    """Decorator to require authentication and optionally specific roles.
    #TODO: this is largely an example, not actually implemented yet

    To use role-based access in the future, we could do something like:
    ```
    @require_auth(roles=["admin"])
    def admin_only_page():
        st.write("Admin only content")

    # Or directly in a page
    check_auth(required_roles=["admin", "manager"])
    ```

    Args:
        func: The function to wrap
        roles: Optional list of required roles
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            check_auth(roles)
            return f(*args, **kwargs)
        return wrapper

    if func is None:
        return decorator
    return decorator(func)