#!/usr/bin/env python3

import os
import toml
from pathlib import Path
from typing import Dict, Any

def generate_secrets() -> Dict[str, Any]:
    """Generate secrets dictionary from environment variables."""
    # Default values for local development
    default_redirect_uri = "http://localhost:8501/oauth2callback"

    return {
        "auth": {
            "redirect_uri": os.getenv("STREAMLIT_AUTH_REDIRECT_URI", default_redirect_uri),
            "cookie_secret": os.getenv("STREAMLIT_AUTH_COOKIE_SECRET"),
            "client_id": os.getenv("STREAMLIT_AUTH_CLIENT_ID"),
            "client_secret": os.getenv("STREAMLIT_AUTH_CLIENT_SECRET"),
            "server_metadata_url": os.getenv(
                "STREAMLIT_AUTH_SERVER_METADATA_URL",
                "https://accounts.google.com/.well-known/openid-configuration"
            )
        }
    }

def write_secrets_file(secrets: Dict[str, Any]) -> None:
    """Write secrets to .streamlit/secrets.toml file."""
    streamlit_dir = Path(".streamlit")
    streamlit_dir.mkdir(exist_ok=True)

    secrets_file = streamlit_dir / "secrets.toml"
    with open(secrets_file, "w") as f:
        toml.dump(secrets, f)

    print(f"Using redirect_uri: {secrets['auth']['redirect_uri']}")
    print(f"✅ Generated {secrets_file} successfully")

if __name__ == "__main__":
    try:
        secrets = generate_secrets()
        write_secrets_file(secrets)
    except Exception as e:
        print(f"❌ Error generating secrets file: {str(e)}")
        exit(1)