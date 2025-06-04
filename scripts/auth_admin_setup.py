"""
Create the first admin user for the application.
Run once after initial authentication setup to bootstrap the first admin account.
"""

import os
import sys
import secrets
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Required environment variables
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_M2M_CLIENT_ID = os.getenv("AUTH0_M2M_CLIENT_ID")
AUTH0_M2M_CLIENT_SECRET = os.getenv("AUTH0_M2M_CLIENT_SECRET")
AUTH0_DATABASE_CONNECTION_NAME = os.getenv("AUTH0_DATABASE_CONNECTION_NAME", "Username-Password-Authentication")
STREAMLIT_AUTH_CLIENT_ID = os.getenv("STREAMLIT_AUTH_CLIENT_ID")

# Validate environment
missing = [var for var in ["AUTH0_DOMAIN", "AUTH0_M2M_CLIENT_ID", "AUTH0_M2M_CLIENT_SECRET", "STREAMLIT_AUTH_CLIENT_ID"]
           if not os.getenv(var)]
if missing:
    print(f"❌ Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)


def get_m2m_token():
    """Fetch M2M access token from Auth0."""
    response = requests.post(
        f'https://{AUTH0_DOMAIN}/oauth/token',
        json={
            "grant_type": "client_credentials",
            "client_id": AUTH0_M2M_CLIENT_ID,
            "client_secret": AUTH0_M2M_CLIENT_SECRET,
            "audience": f'https://{AUTH0_DOMAIN}/api/v2/'
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_existing_admins(token):
    """Get list of existing admin emails."""
    response = requests.get(
        f'https://{AUTH0_DOMAIN}/api/v2/users',
        headers={"Authorization": f"Bearer {token}"},
        params={"per_page": 100, "fields": "email,app_metadata", "include_fields": "true"}
    )
    response.raise_for_status()
    data = response.json()
    users = data if isinstance(data, list) else data.get('users', [])

    return [u['email'] for u in users if 'admin' in u.get('app_metadata', {}).get('roles', [])]


def send_password_email(email):
    """Send password setup email."""
    response = requests.post(
        f'https://{AUTH0_DOMAIN}/dbconnections/change_password',
        json={
            "client_id": STREAMLIT_AUTH_CLIENT_ID,
            "email": email,
            "connection": AUTH0_DATABASE_CONNECTION_NAME
        }
    )
    if response.ok:
        print(f"📧 Password setup email sent to {email}")
    else:
        print(f"⚠️  Could not send password email (status: {response.status_code})")


def create_or_update_admin(token, email):
    """Create admin user or update existing user with admin role."""
    # Try to create new user
    response = requests.post(
        f'https://{AUTH0_DOMAIN}/api/v2/users',
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "email": email,
            "connection": AUTH0_DATABASE_CONNECTION_NAME,
            "password": secrets.token_urlsafe(48),
            "email_verified": False,
            "verify_email": False,
            "app_metadata": {"invited": True, "roles": ["admin"]}
        }
    )

    if response.status_code == 201:
        print(f"✅ Admin user created: {email}")
        send_password_email(email)
        return True

    if response.status_code == 409:  # User exists
        print(f"User exists, updating with admin role...")

        # Get user ID
        response = requests.get(
            f'https://{AUTH0_DOMAIN}/api/v2/users-by-email',
            headers={"Authorization": f"Bearer {token}"},
            params={"email": email}
        )
        response.raise_for_status()
        users = response.json()

        if not users:
            print(f"❌ User {email} not found")
            return False

        # Update with admin role
        user_id = users[0]['user_id']
        response = requests.patch(
            f'https://{AUTH0_DOMAIN}/api/v2/users/{user_id}',
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"app_metadata": {"roles": ["admin"], "invited": True}}
        )
        response.raise_for_status()

        print(f"✅ User {email} updated with admin role")
        if not users[0].get('email_verified'):
            send_password_email(email)
        return True

    # Other error - print details
    print(f"\n❌ Error {response.status_code}: {response.reason}")
    error_body = response.text
    if error_body:
        print(f"Details: {error_body}")

    return False


def main():
    """Main script execution."""
    print("🚀 Auth0 Admin User Setup\n")

    # Get M2M token
    print("Connecting to Auth0...")
    try:
        token = get_m2m_token()
        print("✅ Connected\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)

    # Check existing admins
    existing_admins = get_existing_admins(token)
    if existing_admins:
        print("Existing admin users:")
        for admin in existing_admins:
            print(f"  • {admin}")
        if input("\nCreate another admin? (y/N): ").lower() != 'y':
            sys.exit(0)

    # Get email
    email = input("\nAdmin email address: ").strip()
    if not email or '@' not in email:
        print("❌ Invalid email")
        sys.exit(1)

    # Create admin
    if create_or_update_admin(token, email):
        print("\n✅ Success! Check your email for the password setup link.")
        print("   You can then access the User Admin page to manage other users.")
    else:
        print("\n❌ Failed to create admin user")
        sys.exit(1)


if __name__ == "__main__":
    main()