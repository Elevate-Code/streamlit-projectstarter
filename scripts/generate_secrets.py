#!/usr/bin/env python3

import os
import json
import toml
from pathlib import Path
from typing import Dict, Any, Optional

SUPPORTED_PROVIDERS = ["auth0", "google", "microsoft"]

def validate_required_env_vars() -> None:
    """Validate that all required environment variables are set."""
    required_vars = [
        "STREAMLIT_AUTH_PROVIDER",
        "STREAMLIT_AUTH_CLIENT_ID",
        "STREAMLIT_AUTH_CLIENT_SECRET",
        "STREAMLIT_AUTH_SERVER_METADATA_URL",
        "STREAMLIT_AUTH_COOKIE_SECRET"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def parse_client_kwargs(env_var: str) -> Optional[Dict[str, Any]]:
    """Parse client_kwargs from environment variable JSON string."""
    if not env_var:
        return None
    try:
        return json.loads(env_var)
    except json.JSONDecodeError:
        print(f"⚠️ Warning: Invalid JSON in client_kwargs: {env_var}")
        return None

def get_provider_config(provider: str) -> Dict[str, Any]:
    """Generate provider-specific configuration from environment variables."""
    config = {
        "client_id": os.getenv("STREAMLIT_AUTH_CLIENT_ID"),
        "client_secret": os.getenv("STREAMLIT_AUTH_CLIENT_SECRET"),
        "server_metadata_url": os.getenv("STREAMLIT_AUTH_SERVER_METADATA_URL")
    }

    if client_kwargs := parse_client_kwargs(os.getenv("STREAMLIT_AUTH_CLIENT_KWARGS")):
        config["client_kwargs"] = client_kwargs

    return config

def generate_secrets() -> Dict[str, Any]:
    """Generate secrets dictionary from environment variables."""
    validate_required_env_vars()

    provider = os.getenv("STREAMLIT_AUTH_PROVIDER", "").lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported auth provider: {provider}. Must be one of: {', '.join(SUPPORTED_PROVIDERS)}")

    return {
        "auth": {
            "redirect_uri": os.getenv("STREAMLIT_AUTH_REDIRECT_URI", "http://localhost:8501/oauth2callback"),
            "cookie_secret": os.getenv("STREAMLIT_AUTH_COOKIE_SECRET"),
            provider: get_provider_config(provider)
        }
    }

def write_secrets_file(secrets: Dict[str, Any]) -> None:
    """Write secrets to .streamlit/secrets.toml file."""
    streamlit_dir = Path(".streamlit")
    streamlit_dir.mkdir(exist_ok=True)

    secrets_file = streamlit_dir / "secrets.toml"
    with open(secrets_file, "w") as f:
        toml.dump(secrets, f)

    print(f"✅ Generated {secrets_file} successfully")
    print(f"Using auth provider: {os.getenv('STREAMLIT_AUTH_PROVIDER')}")
    print(f"Using redirect_uri: {secrets['auth']['redirect_uri']}")

if __name__ == "__main__":
    try:
        secrets = generate_secrets()
        write_secrets_file(secrets)
    except Exception as e:
        print(f"❌ Error generating secrets file: {str(e)}")
        exit(1)