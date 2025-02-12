# Authentication Setup

This application uses Streamlit's native Google OAuth authentication for secure access control. This document provides detailed setup instructions for both local development and production environments.

⚠️ Streamlit `st.login()` uses the `secrets.toml` file for authentication, but Railway does not support secrets files. So we use a custom start command to generate the secrets file from environment variables.

## Google OAuth Setup

1. Create OAuth 2.0 credentials in [Google Cloud Console](https://console.cloud.google.com/apis/credentials):
   - [Create a project](https://console.cloud.google.com/projectcreate) or select an existing one
   - [Configure OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent) (External is fine for testing)
   - [Create OAuth Client ID](https://console.cloud.google.com/apis/credentials) (Web Application type)
   - Add authorized redirect URIs:
     - Local: `http://localhost:8501/oauth2callback`
     - Prod: `https://your-railway-app-url.railway.app/oauth2callback`
     - Add the same domains without the `/oauth2callback` path as authorized JavaScript origins.
    - customize the branding information that your users see on the user-consent screen.

## Local Development Secrets Configuration

1. In your `.env` file include the following:
   ```env
   # Streamlit Native Auth
   STREAMLIT_AUTH_REDIRECT_URI=http://localhost:8501/oauth2callback
   STREAMLIT_AUTH_COOKIE_SECRET=
   STREAMLIT_AUTH_CLIENT_ID=your-google-client-id
   STREAMLIT_AUTH_CLIENT_SECRET=your-google-client-secret
   STREAMLIT_AUTH_SERVER_METADATA_URL=https://accounts.google.com/.well-known/openid-configuration

   # Auth Access Control (comma separated lists)
   STREAMLIT_AUTH_ALLOWED_DOMAINS=company.com,agency.org
   STREAMLIT_AUTH_ALLOWED_EMAILS=user@company.com,admin@agency.org
   ```

2. Generate a secure `STREAMLIT_AUTH_COOKIE_SECRET` using:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. Generate/regenerate `secrets.toml` using `python scripts/generate_secrets.py`

4. Access Control Options:
   - **Domain-based Access**: Add organization domains as a comma-separated list to `STREAMLIT_AUTH_ALLOWED_DOMAINS`
   - **User-based Access**: Add specific email addresses as a comma-separated list to `STREAMLIT_AUTH_ALLOWED_EMAILS`
   - The application will grant access if either the user's email is in the allowed list OR their domain is allowed
   - For applications with many users or where you need role-based access control, move access control handling to a database

## Railway Deployment

When deploying to Railway:

1. Set the environment variables in your Railway project settings with the production values, these may be largely the same as the local development values. ⚠️ Make sure to use the correct redirect URI:
   ```
   STREAMLIT_AUTH_REDIRECT_URI=https://your-railway-app-url.railway.app/oauth2callback
   STREAMLIT_AUTH_COOKIE_SECRET=your-secure-cookie-secret
   STREAMLIT_AUTH_CLIENT_ID=your-google-client-id
   STREAMLIT_AUTH_CLIENT_SECRET=your-google-client-secret
   STREAMLIT_AUTH_ALLOWED_DOMAINS=your-allowed-domains
   STREAMLIT_AUTH_ALLOWED_EMAILS=your-allowed-emails
   ```

2. The application uses a custom start command that generates the Streamlit secrets file from environment variables before starting. You can set this under the service Settings > Deploy > Custom Start Command:
   ```bash
   python scripts/generate_secrets.py && streamlit run app.py
   ```

## Security Considerations

- Regularly rotate the cookie secret and OAuth credentials
- Monitor the Google Cloud Console for any suspicious authentication attempts
- Review the access control lists periodically to ensure they reflect current authorization requirements