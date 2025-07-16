# Authentication Setup

This application uses Streamlit's native user authentication for secure access control. This document provides detailed setup instructions for both local development and production environments.

> Streamlit supports user authentication with OpenID Connect (OIDC), which is an authentication protocol built on top of OAuth 2.0. `st.login()` redirects the user to your identity provider. After they log in, Streamlit stores an identity cookie and then redirects them to the homepage of your app in a new session. [Streamlit authentication docs](https://docs.streamlit.io/develop/concepts/connections/authentication)

## Prerequisites

- `streamlit>=1.42.0`
- `authlib>=1.3.2`

## Setup Overview

1. Register an application with Auth0
3. Set your local environment variables.
4. Generate or regenerate `secrets.toml` using `python scripts/generate_secrets.py`.
5. Test the registration and login locally.
6. Set your Railway environment variables.
7. Deploy to Railway.
8. Update the Custom Start Command in your Railway service settings & redeploy.
9. Test the registration, login, and access control in production.

## Troubleshooting

If you see `AttributeError: st.user has no attribute "is_logged_in"`, this typically means either:
> - You're using an older version of Streamlit (must be >=1.42.0)
> - Environment variables are not set correctly
> - The `secrets.toml` file hasn't been generated using `python scripts/generate_secrets.py`
> - The custom start command is not being used in production

If you encounter any Auth0 specific issues, strongly recommend taking a look at [Monitoring > Logs](https://manage.auth0.com/#/logs) as a first stop.

## Local Environment Variables

In your local `.env` file add the following section:

```env
# Streamlit Auth
STREAMLIT_AUTH_PROVIDER=auth0
STREAMLIT_AUTH_REDIRECT_URI=http://localhost:8501/oauth2callback
STREAMLIT_AUTH_COOKIE_SECRET=
STREAMLIT_AUTH_CLIENT_ID=
STREAMLIT_AUTH_CLIENT_SECRET=
STREAMLIT_AUTH_SERVER_METADATA_URL=
```

1. Generate the `STREAMLIT_AUTH_COOKIE_SECRET` env variable: `python -c "import secrets; print(secrets.token_hex(32))"`
2. Proceed with the **Auth0** (recommended) or **Google OAuth** (minimally supported in this guide)
3. At the end, you will need to generate a `secrets.toml` file using `python scripts/generate_secrets.py`

## Auth0 Setup (Recommended)

In addition to the Streamlit auth variables, you will need to set the following environment variables:
```env
AUTH0_TEAM_LOGIN_URL=https://accounts.auth0.com/teams/<team-id-here>
AUTH0_DOMAIN=
AUTH0_M2M_CLIENT_ID=
AUTH0_M2M_CLIENT_SECRET=
AUTH0_DATABASE_CONNECTION_NAME=
```

**TERMINOLOGY:** Think of an Auth0 `Team` as the billing & admin envelope that can hold many `Tenants` - though the Free plan allows just one tenant. Each Tenant is an isolated environment (dev, staging, prod) with its own config, logs, and `Users` (end-users). Inside a Tenant you create `Applications` (front-end or API clients) and configure `Connections` (user:pass database, social login, passwordless) that authenticate users. Collaborators are invited either at the **Team** level (see every tenant) or the **Tenant** level (just that tenant); the Free plan allows **three admins** in total. `Organizations` let you model B2B customers (clients?) and are available - up to **five** on Free.

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

For handling user invitation emails, please create a Mailgun account (free for 100 emails/month) and share the credentials with me.

This is crucial for our invite-only system. While email delivery is generally reliable, corporate firewalls or spam filters can sometimes block invitations. To address this, the application includes an admin interface with fallback options to manually verify users or generate secure, one-time password reset links if direct email delivery fails.

1. Go to https://mailgun.com and click Start for Free
2. Verify the account (email + phone).
3. Add a Sending > Domain sub-domain (eg. `mg.yourdomain.com`, mine looks like: `mg.ecomanalytics.co`) and paste the 2 TXT + 2 MX records into your DNS (records can take 5-30 minutes to validate)
4. Share the Mailgun credentials with me - I'll need you to also forward me the 2FA code
5. I'll finish all remaining technical settings.
6. After I'm done, please remember to reset the password for the Mailgun account.
```

⚠️ **IMPORTANT:** Once your email is invited to the Auth0 Team, make sure to note the URL of that team account in the client's project, as it will be displayed as a non-descript "team-abc1234" upon login. Save it as `AUTH0_TEAM_LOGIN_URL` in the .env file. You can view the team you are currently in by clicking the top-left tenant dropdown menu.

Once you're inside one Team, there is no in-page "switch-team" button. You must sign out and re-enter through [accounts.auth0.com](https://accounts.auth0.com) to select a different Team.

Once invited to a Team, you will need to grant yourself Admin permissions for the tenant by following these steps:
- Navigate to the Team > Members page (eg. https://accounts.auth0.com/teams/CLIENT_TEAM_ID/members).
- Click the ellipses ("...") next to your user and select "Manage Tenant Access".
- Click "Add Tenant Access", select the tenant, and then select "Admin".

### Auth0 Application Setup

1. Create a new application, selecting "Regular Web Application" as the application type.
2. Name: Project name in title case (eg. "[Client Name] Reporting Dashboard").
3. Under **Settings** of the new application, do the following:
   - Copy the Domain, to the `AUTH0_DOMAIN` value in your `.env` file
   - Copy the Client ID to the `STREAMLIT_AUTH_CLIENT_ID` value
   - and Client Secret to the `STREAMLIT_AUTH_CLIENT_SECRET` value
   - Set `STREAMLIT_AUTH_PROVIDER=auth0` in your `.env` file (if not already set)
   - (FYI: you can skip adding the https://YOUR-RAILWAY-APP-URL.railway.app if you have not deployed to Railway yet)
   - Application Login URI: `https://YOUR-RAILWAY-APP-URL.railway.app/`
   - Allowed Callback URLs: `http://localhost:8501/oauth2callback, https://YOUR-RAILWAY-APP-URL.railway.app/oauth2callback`
   - Allowed Logout URLs: `http://localhost:8501, https://YOUR-RAILWAY-APP-URL.railway.app`
   - Allowed Web Origins: `http://localhost:8501, https://YOUR-RAILWAY-APP-URL.railway.app`

   > 💡 **For Multiple Domains/Environments:** To support multiple domains and environments (staging, production, etc.), add their respective URLs to the `Allowed...` fields, separated by commas. Each environment deployment (e.g., on Railway) will also need its own `STREAMLIT_AUTH_REDIRECT_URI` environment variable set to its specific callback URL.

4. Scroll to the bottom of Settings, and under **Advanced Settings** > Grant Types, ensure "Authorization Code" is selected.
5. Click **Save**
6. While still in Advanced Settings, go to the Endpoints tab and copy the "OpenID Configuration" URL (eg. `https://YOUR-AUTH0-DOMAIN.us.auth0.com/.well-known/openid-configuration`). You will need this for the `STREAMLIT_AUTH_SERVER_METADATA_URL` environment variable.
7. Back at the top of the page, under Credentials > Application Authentication, select **Client Secret (Basic)** as the authentication method and click Save.

**NOTE:** Pay attention to how we're using "http://localhost:8501" as the authorized option for the dev environment. When you have two Streamlit apps running at the same time locally, one of them will automatically get pushed to the next port, in which case you will see issues with logins and authentication.

### Machine-to-Machine Application Setup

To enable a Streamlit admin interface for user management, create an M2M application (kind of like a Service Account). Ideally, you would create one M2M application for each distinct backend service that needs to interact with the Auth0 Management API.

1. In Auth0 Dashboard, go to **Applications** > Create Application
2. Choose Machine to Machine Applications as the type
3. Name it to clearly associate it with the application (e.g., "[App Name] M2M")
4. Select Auth0 Management API from the available APIs
5. Grant these minimum scopes:
   - `create:users` - Create new users
   - `read:users` - List user profiles
   - `update:users` - Update user profiles (eg. manually verify user)
   - `read:users_app_metadata` - Manage role assignments
   - `update:users_app_metadata` - Manage role assignments
   - `create:user_tickets` - Create password reset tickets
6. Also consider these for debugging/diagnostics:
   - `read:connections` - Read database connections
   - `read:clients` - Read client applications
   - `read:client_grants` - Read client grants

6. Save the Client ID and Client Secret in your `.env` file:
   ```env
   AUTH0_M2M_CLIENT_ID=your_m2m_client_id
   AUTH0_M2M_CLIENT_SECRET=your_m2m_client_secret
   ```

### Database Connection Setup

While you *can* use the default "Username-Password-Authentication" database connection, if you think there is any chance that you will have additional apps under the same Auth0 account, it is strongly recommended to create a new (dedicated) database connection for the application.

⚠️ **IMPORTANT:** It is not possible to rename a database connection after creation - so take care to name it appropriately. [The only workaround](https://community.auth0.com/t/can-you-change-a-database-connection-name-after-creation/117185/3) is to create a new database connection with the new name and then Export/Import the users.

1. Navigate to **Authentication > Database** in Auth0 Dashboard.
2. Click **Create Database Connection**.
3. Give the connection a permanent name (use format `<app_name>-users`, ex: `sales-dashboard-users`).
3. Set the `AUTH0_DATABASE_CONNECTION_NAME` environment variable to match this name (e.g., `AUTH0_DATABASE_CONNECTION_NAME=sales-dashboard-users`)
4. If building an invite-only application, toggle on "Disable Sign Ups".
5. Click Create.
6. In the **Applications** tab of the newly created connection, enable for both applications you just created.

### Disabling Public Sign-ups (Invite-Only Use Case)

⚠️ **IMPORTANT:** Consider disabling "Enable Application Connections" to ensure new applications don't automatically inherit all connections, which may inadvertently allow social registration/login on new apps and bypass the invite-only system. You can find this on-by-default setting in Tenant Settings at **Settings** > Advanced, locate and toggle off "Enable Application Connections".

Since invited users don't need email verification, disable Auth0's automatic emails to avoid confusion. In Branding > Email Templates, set both "Verification Email" and "Welcome Email" status to "Template disabled". When creating users via the Management API, we will also use `verify_email: false` to prevent verification emails.

For private/internal applications, ensure that you have disabled public registration on the database connection so that only invited users can access the application:

1. Navigate to **Authentication > Database** in Auth0 Dashboard
2. Select your database connection
3. Go to **Settings** tab
4. Toggle **"Disable Sign Ups"** to the ON position
5. Click **Save**

This prevents users from self-registering. All new users must be invited through the Streamlit admin interface.

### Login Verification with Auth0 Actions

⚠️ **IMPORTANT:** By default, Auth0 allows **ALL USERS** to register and access the application. This is highly undesirable for private/internal applications, and you will want to disable public registration if you haven't done so already in [Disabling Public Sign-ups (Invite-Only Use Case)](#disabling-public-sign-ups-invite-only-use-case).

This action handles user verification and ensures that even if social logins are enabled later, only *invited* users can access the application. Users invited through the Streamlit `auth_admin.py` page receive an `invited: true` flag in their metadata.

Go to Actions > Triggers > `post-login` > Add Action (+) > From scratch.

```js
// Name: "Post-Login Verification"
exports.onExecutePostLogin = async (event, api) => {
  // Dynamically determine the namespace from the redirect URI to support multiple environments.
  const redirectUri = new URL(event.request.query.redirect_uri);
  const namespace = `${redirectUri.origin}/claims`;

  // Always add roles to the token
  const roles = event.user.app_metadata?.roles || [];
  api.idToken.setCustomClaim(`${namespace}/roles`, roles);

  // Include email_verified in the ID token
  api.idToken.setCustomClaim("email_verified", event.user.email_verified);

  // TODO: Couldn't figure out how to deny access if `!event.user.email_verified` because (as of 2025-05-07)  Streamlit
  // does not propagate errors that appear during the OAuth flow and user just gets redirected back to home page without
  // any indication of what went wrong. Just handling unverified users inside the app for now.
  // See: https://github.com/streamlit/streamlit/issues/10160

  // Check if user was invited (has the invited flag or has roles assigned)
  const wasInvited = event.user.app_metadata?.invited === true || roles.length > 0;

  // For new users (first login), ensure they were invited
  if (event.stats.logins_count === 1 && !wasInvited) {
    // This is a first-time login without invitation
    api.access.deny("not_invited", "Access denied: Please contact an administrator for an invitation.");
  }

  // Optional: Check email verification for database connections
  if (event.connection.strategy === "auth0" && !event.user.email_verified) {
    console.log("User email not verified:", event.user.email);
  }
};
```

Back on the Triggers page, drag your Action into the visual flow editor and click "Apply" to save.

**Note on Domain Whitelisting:** If you need to whitelist entire domains (e.g., `*@company.com`), you can add domain checking logic to the Pre-User-Registration and Post-Login actions. However, for most private applications, the invite-only approach is more secure and manageable.

### Role-Based Access Control Overview

The way to get role-based access control on Auth0's free plan is to use the `app_metadata` field and use a Streamlit admin interface to manage role assignments and permissions.

For more details (as this can be quite complex), see the [Role-Based Access Control](role_based_access_control.md) file.

### Email Provider Setup

Auth0 requires an external email provider for sending customized verification and invitation emails.

In cases where invitation emails fail to deliver, the application's Auth Admin page (`/auth_admin`) provides two fallback mechanisms. First, an admin can manually verify a user's email, bypassing the need for the user to click a verification link. Second, if a user still cannot log in, an admin can generate a secure, one-time password reset link that can be shared through an alternative, trusted channel.

Mailgun is recommended if you have a domain name, otherwise Gmail is a good option.

#### Mailgun

Offers a generous free tier or 100 emails/month.

1. Sign up at [mailgun.com](https://mailgun.com)
2. Add a sending subdomain (e.g., `mg.yourdomain.com`)
3. Configure DNS records in your domain provider:
   - SPF: Host = `mg`, Value = Mailgun's SPF record
   - DKIM: Host = `pic._domainkey.mg`, Value = Mailgun's DKIM record
   - MX records as provided by Mailgun
4. (In Auth0 Dashboard) **Branding > Email Provider > Mailgun**:
   - **From**: `no-reply@mg.yourdomain.com`
   - **API Key**: Your Mailgun Private API Key
   - **Domain**: `mg.yourdomain.com`
   - **Region**: Match your Mailgun account region

#### Gmail

1. Turn on 2-Step Verification in your Google account and create an App Password [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. In Auth0 → **Branding → Email Provider** → *Use my own email provider* → **SMTP Provider**. Enter as below. Save and click Send Test Email.
3. Done. Typical Workspace quotas are 500 recipients/day for consumer Gmail and 2,000 for paid Workspace.

| Setting  | Value                                                         |
| -------- | ------------------------------------------------------------- |
| Host     | `smtp.gmail.com`                                              |
| Port     | 587 (STARTTLS) or 465 (SSL)                                   |
| Username | full Gmail address                                            |
| Password | App Password (generated after enabling 2FA)                   |

#### Email Template Setup

In Branding > Email Templates, you can customize the **Change Password (Link)** email template.

Set Subject to: `{% if user.email_verified %}Password Reset for {{organization.name}} {{ application.name }}{% else %}Welcome to {{organization.name}} {{ application.name }} – Set Your Password{% endif %}`

Set Redirect To: `{{ application.callback_domain }}`

In the Message body make the following changes:

- From: "You have submitted a password change request!" *There may be two places to change this.*
- To: "{% if user.email_verified %}You have submitted a password change request!{% else %}You've been invited to {{organization.name}} {{ application.name }} - set your password.{% endif %}"

- From: "If it was you, confirm the password change"
- To: "Confirm your account and change your password here:"

Click Save.

### Auth0 Environment Variables & Generating the Secrets File

All your environment variables should now be set.

Run the following command to generate the secrets file:
```bash
python scripts/generate_secrets.py
```

Run the following command to create the your admin user account:
```bash
python scripts/auth_admin_setup.py
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
6. The application uses a custom start command that generates the Streamlit secrets file from environment variables before starting[1]. You will need to update the custom start command in the service Settings > Deploy > Custom Start Command (this might create some downtime):
   ```bash
   python scripts/generate_secrets.py && streamlit run app.py
   ```
7. Redeploy the changes.
8. Test the authentication flow in production; if it works, add and commit authentication to all pages/views.

[1] Streamlit `st.login()` uses the `secrets.toml` file for authentication, but Railway does not support secrets files. So we use a custom start command to generate the secrets file from environment variables. See also this workaround that extends the secrets singleton: https://github.com/streamlit/streamlit/issues/10543#issuecomment-2869172025

## Auth0 Extras and Details

### Social Login Connections

To add social login options (Google, Microsoft, GitHub, etc.):
1. Go to **Authentication > Social > Create Connection**
2. Select the desired provider and follow setup instructions
3. Enable for your application in the connection settings

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