# Authentication Setup

This application uses Streamlit's native user authentication for secure access control. This document provides detailed setup instructions for both local development and production environments.

> Streamlit supports user authentication with OpenID Connect (OIDC), which is an authentication protocol built on top of OAuth 2.0. `st.login()` redirects the user to your identity provider. After they log in, Streamlit stores an identity cookie and then redirects them to the homepage of your app in a new session. [Streamlit authentication docs](https://docs.streamlit.io/develop/concepts/connections/authentication)

⚠️ **NOTE:** Streamlit `st.login()` uses the `secrets.toml` file for authentication, but Railway does not support secrets files. So we use a custom start command to generate the secrets file from environment variables.

## Prerequisites

- `streamlit>=1.42.0`
- `authlib>=1.3.2`

> ⚠️ **IMPORTANT:** If you see `AttributeError: st.experimental_user has no attribute "is_logged_in"`, this typically means either:
> - You're using an older version of Streamlit (must be >=1.42.0)
> - Environment variables are not set correctly
> - The `secrets.toml` file hasn't been generated using `python scripts/generate_secrets.py`

## Setup Overview

1. Decide on an authentication provider and register an application with them
2. Setup a whitelisting mechanism for users or organizations
3. Set your local environment variables
4. Generate/regenerate `secrets.toml` using `python scripts/generate_secrets.py`
5. Test the registration and login locally
6. Deploy to Railway, then hurry up and...
7. Set your Railway environment variables
8. Update the Custom Start Command in your Railway service settings
9. Redeploy

TODO: those last 4 steps seem kind of sketchy, maybe there's a better way?

## General Local Variables

In your local `.env` file add the following section:

```env
# Streamlit Auth
STREAMLIT_AUTH_PROVIDER=
STREAMLIT_AUTH_REDIRECT_URI=http://localhost:8501/oauth2callback
STREAMLIT_AUTH_COOKIE_SECRET=
STREAMLIT_AUTH_CLIENT_ID=
STREAMLIT_AUTH_CLIENT_SECRET=
STREAMLIT_AUTH_SERVER_METADATA_URL=
```

1. Generate a secure `STREAMLIT_AUTH_COOKIE_SECRET` using: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Proceed with the **Auth0** or **Google OAuth** setup below to get the remaining variables
3. At the end, you will need to generate a `secrets.toml` file using `python scripts/generate_secrets.py`

## Auth0 Setup (Recommended)

First, have the client create an Auth0 account and invite you to manage it.
```md
Please create an Auth0 account and invite me as a collaborator through the Auth0 Dashboard:
1. Sign up for Auth0 (https://auth0.com/) - the Free plan will be sufficient for our needs
2. Invite my 🔴YOUR_ECOM_EMAIL_HERE email as a collaborator through the Auth0 Dashboard:
   - Switch to the auto-created Team (via the top nav dropdown menu)
   - You can also try this link: https://accounts.auth0.com/teams
   - Go to the "Members"/"Team Members" page using the sidebar menu
   - Click **Invite A Member**, enter my email address with the highest privileges (eg. "Team Owner")
```

Then...
1. Create a new application and select "Regular Web Application" as the application type
2. Under **Settings** set the following:
   - Name: project name in title case (eg. "[Client Name] Dashboard")
   - Description: Helps the user identify the application when logging in
   - Allowed Callback URLs: `http://localhost:8501/oauth2callback, https://YOUR-RAILWAY-APP-URL.railway.app/oauth2callback`
   - Allowed Logout URLs: `http://localhost:8501, https://YOUR-RAILWAY-APP-URL.railway.app`
   - Allowed Web Origins: `http://localhost:8501, https://YOUR-RAILWAY-APP-URL.railway.app`
3. Scroll to the bottom of Settings and under Advanced Settings > Grant Types, ensure that "Authorization Code" is selected
4. Click **Save Changes**
5. While you are in Advanced Setting, go to the Endpoints tab and grab the "OpenID Configuration" URL (eg. `https://YOUR-AUTH0-DOMAIN.us.auth0.com/.well-known/openid-configuration`) as you will need it for the **STREAMLIT_AUTH_SERVER_METADATA_URL** environment variable.
6. Under Credentials > Application Authentication, select "Client Secret (Basic)" as the authentication method and click save
7. See the [Whitelisting Users/Orgs](#whitelisting-usersorgs) section for details on how to whitelist specific users or organizations.

## Google OAuth Setup (Skip if using Auth0)

Create OAuth 2.0 credentials in [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. [Create a project](https://console.cloud.google.com/projectcreate) or select an existing one
2. [Configure OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent) (External is fine for testing)
3. [Create OAuth Client ID](https://console.cloud.google.com/apis/credentials) (Web Application type)
4. Add authorized redirect URIs:
   - Local: `http://localhost:8501/oauth2callback`
   - Production: `https://YOUR-RAILWAY-APP-URL.railway.app/oauth2callback`
   - Add the same domains without the `/oauth2callback` path as authorized JavaScript origins.
5. Customize the branding information that your users see on the user-consent screen.
6. See the [Whitelisting Users/Orgs](#whitelisting-usersorgs) section for details on how to whitelist specific users or organizations.

For Google Cloud, a single URL is shared for OIDC clients so use `https://accounts.google.com/.well-known/openid-configuration` as the **STREAMLIT_AUTH_SERVER_METADATA_URL**.

## Whitelisting Users/Orgs

⚠️ By default, the application will grant access to **all users** who have authenticated with Auth0 or Google. This is likely undesirable for private/internal applications, and you will want to whitelist specific users or organizations.

### Auth0

For more details and advanced configurations, see the [Auth0 Advanced Configurations](#auth0-advanced-configurations) section.

Use a `pre-user-registration` Action for the database sign-up check to block unauthorized signups as early as possible​, AND a `post-login` additional login-time enforcement (important if admins might manually users or social logins might be used later). This two-step approach covers all cases without letting unauthorized accounts persist.

**Whitelist Logic: Allowing Certain Domains and Emails**

**NOTE:** This is a simplified example with a hardcoded allow lists, where you may need to update the Action code every time a user is added or removed. For options that enable the client to manage the allowlist, see the [Client-Managed Allowlist](#client-managed-allowlist) section.

This code supports two types of entries: entire domains (e.g. @client.com) and specific email addresses. The logic will be: allow the login/sign-up if the email's domain is on the list OR the exact email is on the list; otherwise deny.

```js
exports.onExecutePreUserRegistration = async (event, api) => {
  // Define allowed domains and specific addresses
  const allowedDomains = ['client.com', 'partner.org'];      // domains allowed
  const allowedEmails  = ['vip.user@example.com', 'joe@client.com'];  // specific emails allowed

  const email = event.user.email || "";
  const domain = email.split('@').pop().toLowerCase();  // get domain part of email

  // Check if domain or full email is in the whitelist
  const domainAllowed = allowedDomains.map(d => d.toLowerCase()).includes(domain);
  const emailAllowed  = allowedEmails.map(e => e.toLowerCase()).includes(email.toLowerCase());

  if (!domainAllowed && !emailAllowed) {
    // Deny the signup – user will not be created
    api.access.deny("signup_denied", "Signup not allowed: unauthorized email domain");
    // You could also use api.validation.error(...) here – either will stop the flow.
  }
};

```

For the Post-Login Action (if used), the code is very similar - you get event.user.email after login and perform the same checks. This will abort the login for any user whose email isn’t in the allowlist, returning an access_denied error.

```js
exports.onExecutePostLogin = async (event, api) => {
  const email = event.user.email || "";
  const domain = email.split('@').pop().toLowerCase();
  const domainAllowed = ['client.com','partner.org'].includes(domain);
  const emailAllowed  = ['vip.user@example.com','joe@client.com'].includes(email.toLowerCase());

  if (!domainAllowed && !emailAllowed) {
    api.access.deny("unauthorized", "Access denied: email is not allowed");
  }
};

```

IMPORTANT: In both cases, consider also requiring that the user’s email is verified if you want to be extra sure (since with email/password, a user could sign up with an allowed domain but never verify ownership). For example, you might check event.user.email_verified in a Post-Login Action and deny access if it’s false​. Auth0’s default email/password flow can be configured to require verification before login, so you might simply enable “Force email verification” in the Auth0 dashboard rather than coding it (it’s a built-in toggle/rule)​ gist.github.com

### Google OAuth (Skip if using Auth0)

You can implement access control in your application code.

Here's an example approach for Google OAuth:

```python
def get_env_list(env_var: str) -> list:
    """Convert comma-separated environment variable to list."""
    return os.getenv(env_var, "").split(",") if os.getenv(env_var) else []

def is_allowed_user(email: str) -> bool:
    """Check if user is allowed based on email domain or specific whitelist."""
    if not email:
        return False

    allowed_domains = get_env_list("STREAMLIT_AUTH_ALLOWED_DOMAINS")
    allowed_users = get_env_list("STREAMLIT_AUTH_ALLOWED_EMAILS")

    # Check whitelist first
    if email.lower() in (user.lower() for user in allowed_users):
        return True

    # Then check domain
    domain = email.split('@')[-1].lower()
    return domain in (d.lower() for d in allowed_domains)
```

Then, add the following to your `.env` file:
```
# Auth Access Control (comma separated lists)
STREAMLIT_AUTH_ALLOWED_DOMAINS=company.com,agency.org
STREAMLIT_AUTH_ALLOWED_EMAILS=user@company.com,admin@agency.org
```

For applications with many users or where you need role-based access control, move access control handling to a database

## Railway Deployment

When deploying to Railway:

1\. Set the environment variables in your Railway project settings with the production values, these may be largely the same as the local development values. ⚠️ Make sure to update and use the correct redirect URI:
```
STREAMLIT_AUTH_REDIRECT_URI=https://your-railway-app-url.railway.app/oauth2callback
```

2\. The application uses a custom start command that generates the Streamlit secrets file from environment variables before starting. You will need to update the custom start command in the service Settings > Deploy > Custom Start Command:
   ```bash
   python scripts/generate_secrets.py && streamlit run app.py
   ```

## Security Considerations

- Regularly rotate the cookie secret and OAuth credentials
- Monitor the Google Cloud Console for any suspicious authentication attempts
- Review the access control lists periodically to ensure they reflect current authorization requirements


## Extras and Details

### Auth0 Advanced Configurations


Auth0 provides extensive support for customizing registration, login, and access controls through [Actions](https://auth0.com/docs/customize/actions) and [Forms](https://auth0.com/docs/customize/forms) to extend your identity flows with additional steps and business logic. For example, you can add an Action to your registration trigger to verify the user's email address, add an Action to your login trigger to require 2FA, a Form to require users to provide additional information or accept terms of service, etc.

### Actions

For Actions, here are some of the **Triggers** you can use:
- `pre-user-registration`: Runs before a user is created, allowing you to validate registration data (deny registration if not in allowlist), enrich user profiles, or reject signups based on custom criteria. (⚠️ Does not run for social logins.)
- `post-user-registration`: Runs asynchronously after user creation, enabling tasks like sending welcome emails, setting up user resources, or triggering external system integrations. (⚠️ Does not run for social logins.)
- `post-login`: Executes after successful login but before the auth completes (token issuance), allowing you to validate access policies (deny access if not in allowlist), add custom claims, enforce MFA, or integrate with external systems. (☑️ Works with social logins.)

Find templates in Library > Create Action > Choose a template, or use ChatGPT/Claude to generate custom Actions. Here are some common ones:
- [simple-user-allowlist-POST_LOGIN](https://github.com/auth0/opensource-marketplace/blob/main/templates/simple-user-allowlist-POST_LOGIN/code.js) | [simple-domain-allowlist-PRE_USER_REGISTRATION](https://github.com/auth0/opensource-marketplace/blob/main/templates/simple-domain-allowlist-PRE_USER_REGISTRATION/code.js)
- [creates-lead-salesforce-POST_USER_REGISTRATION](https://github.com/auth0/opensource-marketplace/blob/main/templates/creates-lead-salesforce-POST_USER_REGISTRATION/code.js)
- [email-verified-POST_LOGIN](https://github.com/auth0/opensource-marketplace/blob/main/templates/email-verified-POST_LOGIN/code.js)

### Client-Managed Allowlist

TODO: This section is still under development, continue from here: https://chatgpt.com/share/68029b34-cc50-8003-aa97-4b8186952765

Hard-coding the allowed domains/emails means you, the developer, must update the Action code for changes. Ideally, we want the client to manage the allowlist. There are a few ways to achieve this:

- **External Allowlist File or API:** Maintain the list of allowed emails/domains on a secure (behind a secret token) external resource that the client can update (for example, a JSON file on a secure cloud storage, or a simple web API that your client can edit or call to add/remove entries). In your Auth0 Action, you can **fetch this list at runtime**. Auth0 Actions run on Node.js and support HTTP requests – for example, using the `axios` library (which you can `require` in an Action) to call an external URL. You might store the URL of the allowlist as an Action secret (so it's configurable without code changes), then do something like:

**⚠️ Caveat:** Reaching out to an external service on **every** authentication can introduce failure points and latency. Ideally, the external service would be very reliable and fast or even an in-memory edge service. Keep the timeout short and handle failures gracefully.

```js
const axios = require('axios');
// ... inside onExecutePreUserRegistration or onExecutePostLogin:
const ALLOWLIST_URL = event.secrets.ALLOWLIST_URL;  // e.g. stored secret with URL
try {
   const { data } = await axios.get(ALLOWLIST_URL, { timeout: 2000 });
   // Assume data comes back as { domains: [...], emails: [...] }
   const allowedDomains = data.domains || [];
   const allowedEmails = data.emails || [];
   // then perform the same checks as before...
   if (!allowedDomains.includes(domain) && !allowedEmails.includes(email)) {
   api.access.deny("unauthorized", "Email not allowed");
   }
} catch (err) {
   // If the fetch fails, optionally deny by default or log the error
   api.access.deny("error", "Could not verify allowlist");
}
```

- **Auth0 Stored Configuration:** Another approach is to store the allowlist in Auth0 itself in a way the client can manage. For instance, you could use Auth0 **Action secrets or environment variables** to hold the list (e.g., a comma-separated string of domains). The client would need access to the Auth0 dashboard or an API to update those. One could build a simple admin UI that calls the Auth0 Management API to update a "configuration" object or the Action itself. However, Auth0 doesn’t provide a built-in UI for non-technical users to edit such config safely. Using the Auth0 Management API or Deploy CLI, a developer could automate updates to the allowlist, but that still involves technical work. If your client is comfortable updating a file in, say, an S3 bucket or Google Sheet, the external fetch approach might actually be more client-friendly.

- **Invite-Only alternative:** Auth0 has an [Invite Only](https://auth0.com/docs/email/send-email-invitations-for-application-signup) feature where you disable public sign-ups and instead manually invite users by email via the dashboard. Invited emails get a sign-up link. This inherently whitelists who can join.


**Manually Adding Users**

💸 **NOTE:** Role Management is not available on the Free tier of Auth0.

You can manually add users (for Username-Password-Authentication) to the Auth0 database by going to the Users section in the Auth0 Dashboard and clicking the "Add User" button. You can also import users from a CSV file. In User management you can also:
- Send a verification email to a user
- Change a user's email or password
- See user details, metadata, and audit logs
