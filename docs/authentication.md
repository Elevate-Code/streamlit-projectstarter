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
> - The custom start command is not being used in production

## Setup Overview

1. Decide on an authentication provider and register an application with them.
2. Set up a whitelisting mechanism for users or organizations.
3. Set your local environment variables.
4. Generate or regenerate `secrets.toml` using `python scripts/generate_secrets.py`.
5. Test the registration and login locally.
6. Deploy to Railway.
7. Set your Railway environment variables.
8. Update the Custom Start Command in your Railway service settings.
9. Redeploy.
10. Test the registration and login in production.

TODO: The last four steps seem somewhat messy; perhaps there's a more streamlined process?

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
2. Proceed with the **Auth0** (recommended) or **Google OAuth** setup below to get the remaining variables
3. At the end, you will need to generate a `secrets.toml` file using `python scripts/generate_secrets.py`

## Auth0 Setup (Recommended)

**TERMINOLOGY:** Think of an Auth0 `Team` as the billing & admin envelope that can hold many `Tenants` - though the Free plan allows just **one**. Each Tenant is an isolated environment (dev, staging, prod) with its own config, logs, and `Users` (end-users). Inside a Tenant you create `Applications` (front-end or API clients) and configure `Connections` (user:pass database, social login, passwordless) that authenticate users. Collaborators are invited either at the **Team** level (see every tenant) or the **Tenant** level (just that tenant); the Free plan allows **three admins** in total. `Organizations` let you model B2B customers (clients?) and are available - up to **five** on Free.

### Auth0 Account Setup

First, have the client create an Auth0 account and invite you to manage it.
```md
Please create an Auth0 account and invite me as a collaborator through the Auth0 Dashboard:
1. Sign up for Auth0 (https://auth0.com/) - the Free plan will be sufficient for our needs
2. Invite my 🔴`YOUR_ECOM_EMAIL_HERE` email as a collaborator through the Auth0 Dashboard:
   - Switch to the auto-created Team (via the top nav dropdown menu)
   - You can also try this link: https://accounts.auth0.com/teams
   - Go to the "Members"/"Team Members" page using the sidebar menu
   - Click Invite A Member, enter my email address with the highest privileges (eg. "Team Owner")
```

Then, once your email is invited, it is very important to note the ID and/or URL of that team account in the client's project, as it will be displayed as a non-descript "team-abc1234" upon login. Consider noting it in the .env file as a comment or under a `STREAMLIT_AUTH_TEAM_ID` variable.

NOTE: Once you're inside one Team, there is no in-page "switch-team" button. You must sign out and re-enter through [accounts.auth0.com](https://accounts.auth0.com) to select a different Team.

Once invited to the Team, you will need to grant yourself Admin permissions for the tenant by following these steps:
- Navigate to the Team > Members page (eg. https://accounts.auth0.com/teams/CLIENT_TEAM_ID/members).
- Click the ellipses ("...") next to your user and select "Manage Tenant Access".
- Click "Add Tenant Access", select the tenant, and then select "Admin".

### Auth0 Application Setup

1. Create a new application, selecting "Regular Web Application" as the application type.
2. Under **Settings** set the following:
   - Name: Project name in title case (eg. "[Client Name] Reporting Dashboard").
   - Description: A brief sentence to help users identify the application during login.
   - Copy the Client ID and Client Secret, and set `STREAMLIT_AUTH_PROVIDER=auth0` in your `.env` file
   - Allowed Callback URLs: `http://localhost:8501/oauth2callback, https://YOUR-RAILWAY-APP-URL.railway.app/oauth2callback`
   - Allowed Logout URLs: `http://localhost:8501, https://YOUR-RAILWAY-APP-URL.railway.app`
   - Allowed Web Origins: `http://localhost:8501, https://YOUR-RAILWAY-APP-URL.railway.app`
3. Scroll to the bottom of Settings, and under Advanced Settings > Grant Types, ensure "Authorization Code" is selected.
4. While in Advanced Settings, go to the Endpoints tab and copy the "OpenID Configuration" URL (eg. `https://YOUR-AUTH0-DOMAIN.us.auth0.com/.well-known/openid-configuration`). You will need this for the **STREAMLIT_AUTH_SERVER_METADATA_URL** environment variable.
5. Click **Save Changes**
6. Back at the top of the page, under Credentials > Application Authentication, select "Client Secret (Basic)" as the authentication method and click Save.
7. ⚠️ Proceed to the [Users/Domains Whitelisting with Auth0 Actions](#usersdomains-whitelisting-with-auth0-actions) section for details on how to whitelist specific users or organizations.

TODO: Add instructions here on how to (optionally) disable strict Auth0 password requirements (eg. 8 characters, uppercase, lowercase, number, special character) on Auth0, ... via Auth0 Tenant Dashboard, select Settings, then Advanced?

### Users/Domains Whitelisting with Auth0 Actions

**⚠️⚠️⚠️ WARNING ⚠️⚠️⚠️** By default, Auth0 allows **ALL USERS** to register and access the application. This is highly undesirable for private/internal applications. You will want to whitelist specific users/domains or use an invite-only approach by disabling public registration.

**🔒 SECURITY NOTES:** We will use a `pre-user-registration` Action to check username-password signups and block unauthorized signups as early as possible and implement `post-login` enforcement for login-time checks. This latter step is crucial if administrators manually add users or if social logins (which bypass the registration check) might be used later. Finally, since a user can sign up with an allowed domain using a username-password without verifying domain ownership, it's critical to require email verification either before a token is issued or during the in-app authentication check.

Go to Actions > Triggers > `pre-user-registration` > Add Action (+) > From scratch.

**💡 FYI:** You can use the play button ("▶️") in the editor to test if the Action works correctly with various emails before deploying it.

```js
// Name: "Pre-Registration Email Whitelist"
exports.onExecutePreUserRegistration = async (event, api) => {
  // Define allow lists
  const allowedEmails  = [
   // allow specific emails
   'joe@client.com',
   'mike@client.com',
   'vip.user@example.com',
  ];
  const allowedDomains = ['client.com', 'partner.org']; // allow entire domains

  const email = event.user.email || "";
  const domain = email.split('@').pop().toLowerCase();  // get domain part of email

  // Check if domain or full email is in the whitelist
  const domainAllowed = allowedDomains.map(d => d.toLowerCase()).includes(domain);
  const emailAllowed  = allowedEmails.map(e => e.toLowerCase()).includes(email.toLowerCase());

  if (!domainAllowed && !emailAllowed) {
    // Deny the signup – user will not be created
    api.access.deny("signup_denied", "Signup not allowed: unauthorized email - contact the admin");
  }
};
```

Back on the Triggers page, on the flow customization page, you should see a section (often on the right side) listing your "Custom" Actions. Find the Action you created, drag it into the visual flow editor in the main part of the page, and click "Apply" to save the changes to the flow.

Go back to the Triggers page and repeat for the `post-login` flow. The Post-Login Action, is very similar to the Pre-Registration Action, but adds custom claims to the token (for example, roles).

The process is *nearly* the same:
1. Actions > Triggers > `post-login` > Add Action (+) > From scratch.
2. Name the Action (eg. "Post-Login Email Whitelist")
3. Copy and paste code below and modify the allowlist to exactly match the Pre-Registration Email Whitelist.
4. 👉 BUT, also modify the `namespace` variable to match your Railway app URL (eg. `https://YOUR-RAILWAY-APP-URL.railway.app/claims`).
5. Deploy > Drag the Action into the visual flow editor > Apply

**💡 FYI:** To enforce RBAC in the Streamlit app, the app needs to know the user's roles after login. The best practice is to embed the role information into the user's ID token (or access token) as custom claims during the authentication flow. The `api.idToken.setCustomClaim(``${namespace}/roles``, roles);`  bit of code will take whatever roles you stored in the user's app_metadata and inject them into the ID token as, for example, `"https://yourapp.com/claims/roles": ["admin"]`.

```js
// Name: "Post-Login Email Whitelist"
exports.onExecutePostLogin = async (event, api) => {
  // Define allow lists for email/domain whitelisting
  const allowedEmails  = [
   // allow specific emails
   'joe@client.com',
   'mike@client.com',
   'vip.user@example.com',
  ];
  const allowedDomains = ['client.com', 'partner.org']; // allow entire domains

  const email = event.user.email || "";
  const domain = email.split('@').pop().toLowerCase();
  const domainAllowed = allowedDomains.map(d => d.toLowerCase()).includes(domain);
  const emailAllowed  = allowedEmails.map(e => e.toLowerCase()).includes(email.toLowerCase());

  // Set claim namespace; add custom app_metadata (such as `roles`) to ID token as custom claim.
  // Don't store sensitive data in app_metadata and keep it lean
  const namespace = "https://YOUR-RAILWAY-APP-URL.railway.app/claims";
  const roles = event.user.app_metadata?.roles || []; // get app_metadata roles (if any)
  api.idToken.setCustomClaim(`${namespace}/roles`, roles);

// TODO: Couldn't figure out how to use this as of 2025-05-07 because Streamlit does not propagate errors
// that appear during the OAuth flow and user just gets redirected back to home page without any indication
// of what went wrong. Just handling unverified users inside the app via `st.experimental_user.email_verified` for now.
// See: https://github.com/streamlit/streamlit/issues/10160
//   if (!event.user.email_verified) {
//     api.access.deny('Please verify your email before logging in.');
//   }

  // Deny access if email is not in allow lists
  if (!domainAllowed && !emailAllowed) {
    api.access.deny("unauthorized", "Access denied: email is not allowed");
  }
};
```

####  Test the Configuration Locally Then Minimaliy in Production

If when registering as a new user you get a "Something went wrong, please try again later" error, make sure you have the .env file set up correctly and nothing is missing.

Don't forget to restart the terminal session and/or Streamlit server after making changes to the .env file.

Check the Auth0 Dashboard > Logs > All Logs to ensure the user was created and the email whitelist actions were triggered.

If needed, delete the user and try Signing up again.

See the [Railway Deployment](#railway-deployment) section for details on how to deploy the changes to production and do a small scale test there.

#### Client Instructions

Inform the client how to self-manage their allowlist by sending them the following instructions:

```md
**Add (or remove) users/domains via the allowlist on Auth0:**
1. Log in to the [Auth0 Dashboard](https://manage.auth0.com/dashboard) and navigate to the Actions > Library page.
2. Edit and deploy (save) BOTH custom Actions: **Pre-Registration Email Whitelist** and **Post-Login Email Whitelist**.

**User registration options:**
1. Self-Signup: Users navigate to the app, click "Login," and then click "Sign up" to register on the login page with their whitelisted email address. By default, Auth0 automatically sends a verification email with a confirmation link.
2. Social Login: Users can also sign up using a social provider (eg. Google, etc.) if their account email is whitelisted.
3. Admin-Added: You can also manually add users (for Username-Password-Authentication) to the Auth0 database by navigating to the Users section in the Auth0 Dashboard and clicking the "Add User" button. You can also verify their email address for them via Details > Email > Edit section.

Note that in User Management, you can also:
- Send a verification email to a user and/or manually verify their email address
- Change a user's email or password
- See user details, metadata, and detailed audit logs

**Setting user roles:**
New users default to the lowest `public` role, which has no permissions. You can change this by editing the user's roles in Users > [user] > Details (not to be confused with the Roles tab).
1. Open a user's profile in the Auth0 Dashboard.
2. In the Details tab, scroll down to the "**App** Metadata" section - 🚫 NOT the "User Metadata" section, which is user-editable.
3. In the "App Metadata" section, define the user's roles like so: `{"roles": ["admin"]}` or `{"roles": ["admin", "editor"]}`
   - The `roles` values will vary based on your application's needs, for example: `admin`, `editor`, `viewer`, `office`, `accounting`, etc.
   - You can assign multiple roles to a single user, they will be granted all of the access associated with each role.
4. Click "Save" to apply the changes.
```

#### Invite-Only Option

TODO: Need to further test and document this option, but it's likely just a matter of toggling off the "Allow users to sign up" option in the Auth0 Application settings and just going with the Admin-added approach in the client instructions above.

Auth0 offers an [Invite Only](https://auth0.com/docs/email/send-email-invitations-for-application-signup) feature where public sign-ups are disabled. Instead, administrators manually invite users by email via the dashboard. Invited users receive a sign-up link, inherently whitelisting who can join.

#### Role-Based Access Control

Auth0's free plan does not officially include the Role Management feature via the dashboard or API (RBAC is a paid feature). However, you can still implement role-based access control by leveraging user profile metadata or custom claims:

Using Metadata for Roles: The reliable approach on free tier is to store roles in the user's metadata. Auth0 provides two metadata fields on each user profile: user_metadata and app_metadata. For roles or permissions, use app_metadata, since it cannot be edited by the end user and is intended for access information. For example, you can edit a user's profile in the Auth0 Dashboard to add an app_metadata key like:

```json
"app_metadata": { "roles": ["admin", "editor"] }
```

This effectively “assigns” roles to the user. You can manage these metadata-based roles through the Auth0 dashboard (User Management > Users > select user > App Metadata section) or via the Auth0 Management API. Using metadata is a free-tier-friendly way to define roles in a maintainable fashion (you or the client can update roles without changing application code).

**Accessing Role Data in the Streamlit App**

Upon a successful login `st.user` will contain the user's OIDC ID token identity information. This means your custom roles claim should be present in `st.user`. For example:

```python
if st.user.is_logged_in:
   # Use a dict because the key contains characters that can't be used as a simple attribute
    roles = st.user.to_dict().get("https://YOUR-RAILWAY-APP-URL.railway.app/claims/roles", [])
    st.write("Roles:", roles)
```

You can then use roles to control access to different parts of your app. For example:

```python
# Show/Hide UI Components
if "admin" in roles:
    st.sidebar.write("🔒 **Admin Panel**")
    # ... admin-specific widgets ...
else:
    st.write("Welcome, regular user.")
    # ... non-admin content ...


# Or Restricting the Entire Page
import streamlit as st
roles = st.session_state.get("roles", [])  # assume you saved roles in session_state
if "admin" not in roles:
    st.error("You are not authorized to view this page.")
    st.stop()
# ... rest of admin page code for authorized users ...
```

### Auth0 Environment Variables & Generating the Secrets File

You should already have the Client ID and Client Secret from earlier steps. If not, go to Applications > [Your Application] > Settings > Basic Information and copy the Client ID and Client Secret.

Then, run the following command to generate the secrets file:
```bash
python scripts/generate_secrets.py
```

### Railway Deployment

When deploying to Railway:

1. Ensure everything is working locally with the development environment variables.
2. Set the environment variables in your Railway project settings using the production values; these may be largely the same as the local development values.
3. ⚠️ However, be sure to update and use the production redirect URI:
```
STREAMLIT_AUTH_REDIRECT_URI=https://YOUR-RAILWAY-APP-URL.up.railway.app/oauth2callback
```
4. Deploy the changes.
5. Commit changes to the repository. These changes might include the following:
   - Adding the `auth.py`, `generate_secrets.py` files.
   - Updating the `README.md` with the new authentication instructions.
   - Adding an `authenticated.py` test page/view to safely test the authentication flow in production.
   - Ensuring the dev `secrets.toml` file is NOT being committed to the repository.
6. The application uses a custom start command that generates the Streamlit secrets file from environment variables before starting. You will need to update the custom start command in the service Settings > Deploy > Custom Start Command (this might create some downtime):
   ```bash
   python scripts/generate_secrets.py && streamlit run app.py
   ```
7. Redeploy the changes.
8. Test the authentication flow in production; if it works, add and commit authentication to all pages/views.

## Auth0 Extras and Details

### Auth0 Advanced Configurations

Auth0 provides extensive support for customizing registration, login, and access controls through [Actions](https://auth0.com/docs/customize/actions) and [Forms](https://auth0.com/docs/customize/forms), allowing you to extend your identity flows with additional steps and business logic. For example, you can add an Action to your registration trigger to verify a user's email address, an Action to your login trigger to require 2FA, or a Form to require users to provide additional information or accept terms of service.

### Auth0 Actions

For Actions, here are some of the **Triggers** you can use:
- `pre-user-registration`: Runs before a user is created, allowing you to validate registration data (deny registration if not in allowlist), enrich user profiles, or reject signups based on custom criteria. (⚠️ Does not run for social logins.)
- `post-user-registration`: Runs asynchronously after user creation, enabling tasks like sending welcome emails, setting up user resources, or triggering external system integrations. (⚠️ Does not run for social logins.)
- `post-login`: Executes after successful login but before the auth completes (token issuance), allowing you to validate access policies (deny access if not in allowlist), add custom claims, enforce MFA, or integrate with external systems. (☑️ Works with social logins.)

Find templates in Library > Create Action > Choose a template, or use a convrsational AI like ChatGPT/Claude to generate custom Actions. Here are some common examples:
- [simple-user-allowlist-POST_LOGIN](https://github.com/auth0/opensource-marketplace/blob/main/templates/simple-user-allowlist-POST_LOGIN/code.js) | [simple-domain-allowlist-PRE_USER_REGISTRATION](https://github.com/auth0/opensource-marketplace/blob/main/templates/simple-domain-allowlist-PRE_USER_REGISTRATION/code.js)
- [creates-lead-salesforce-POST_USER_REGISTRATION](https://github.com/auth0/opensource-marketplace/blob/main/templates/creates-lead-salesforce-POST_USER_REGISTRATION/code.js)
- [email-verified-POST_LOGIN](https://github.com/auth0/opensource-marketplace/blob/main/templates/email-verified-POST_LOGIN/code.js)

### Auth0 External Allowlist File or API

Maintain the list of allowed emails/domains on a secure (behind a secret token) external resource that the client can update (for example, a JSON file on a secure cloud storage, or a simple web API that your client can edit or call to add/remove entries). **⚠️ Caveat:** Reaching out to an external service on **every** authentication can introduce failure points and latency. Ideally, the external service would be very reliable and fast or even an in-memory edge service. Keep the timeout short and handle failures gracefully. In your Auth0 Action, you can **fetch this list at runtime**. Auth0 Actions run on Node.js and support HTTP requests – for example, using the `axios` library (which you can `require` in an Action) to call an external URL. You might store the URL of the allowlist as an Action secret (so it's configurable without code changes), then do something like:

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
   console.error("Error fetching allowlist:", err);
   api.access.deny("error", "Could not verify allowlist due to an internal error");
}
```

## Google OAuth Setup (If Not Using Auth0)

NOTE: Google OAuth is generally not recommended because, although free, it can be very limiting. Furthermore, you can easily add support for Google (and other) social logins using Auth0. This section is kept primarily for reference.

### Google Cloud Console Setup

Create OAuth 2.0 credentials in [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. [Create a project](https://console.cloud.google.com/projectcreate) or select an existing one.
2. [Configure OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent) (External is acceptable for testing).
3. [Create OAuth Client ID](https://console.cloud.google.com/apis/credentials) (Web Application type).
4. Add authorized redirect URIs:
   - Local: `http://localhost:8501/oauth2callback`
   - Production: `https://YOUR-RAILWAY-APP-URL.railway.app/oauth2callback`
   - Add the same domains (without the `/oauth2callback` path) as authorized JavaScript origins.
5. Customize the branding information that users see on the consent screen.
6. Refer to the [Whitelisting Users/Orgs](#whitelisting-usersorgs) section for details on whitelisting specific users or organizations.

For Google Cloud, a single URL is used for OIDC clients. Set `https://accounts.google.com/.well-known/openid-configuration` as the **STREAMLIT_AUTH_SERVER_METADATA_URL**.

### Google OAuth Whitelisting Users/Orgs

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
```env
# Auth Access Control (comma separated lists)
STREAMLIT_AUTH_ALLOWED_DOMAINS=company.com,agency.org
STREAMLIT_AUTH_ALLOWED_EMAILS=user@company.com,admin@agency.org
```

For applications with many users or those requiring role-based access control, consider managing access control via a database or switching to Auth0.

### Google OAuth Security Considerations

- Regularly rotate cookie secrets and OAuth credentials.
- Monitor the Google Cloud Console for any suspicious authentication activity.
- Periodically review access control lists to ensure they reflect current authorization requirements.