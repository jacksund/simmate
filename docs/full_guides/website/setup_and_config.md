# Website Setup and Config

The Simmate website is built on top of [Django](https://www.djangoproject.com/), a high-level Python web framework. This guide covers how to set up and configure your website for both local development and production environments.

------------------------------------------------------------

## Local Server Setup

To start a Simmate server on your local computer, use the following command:

=== "command line"
    ``` bash
    simmate run-server
    ```

While this command is running, open your preferred browser (Chrome, Firefox, etc.) and navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

!!! tip
    You can view your current configuration at any time by running:
    ``` bash
    simmate config show
    ```

------------------------------------------------------------

## Production Server Setup

To set up a production-ready server for your team, you have three options:

1. **Managed Hosting:** Request our team to manage a server for you.
2. **Collaborate:** Join the official Simmate server and collaborate with us.
3. **Self-Hosted:** Set up and manage your own server.

For options 1 and 2, please contact us at `simmate.team@gmail.com`.

For option 3, we provide several starting points in the Simmate repository under the `envs/` directory:

* **Docker:** See `envs/docker/docker-compose.yaml` for a containerized setup.
* **Kubernetes:** See `envs/helm/` for a Helm chart to deploy Simmate on a cluster.

Ensure you have also completed the base Simmate tutorials, particularly the ones on [setting up a cloud database](/getting_started/use_a_cloud_database/quickstart.md) and [setting up computational resources](/getting_started/add_computational_resources/quickstart.md).

!!! warning
    For any production server, ensure you update your `SECRET_KEY`, `ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` settings. See the [General Settings](#general-settings) section below.

------------------------------------------------------------

## General Settings

You can configure your website behavior using environment variables, a `settings.yaml` file, or the `simmate config` command.

### Security and Networking

When deploying to a public server, you **must** update these settings:

| Setting | Environment Variable | Description |
| :--- | :--- | :--- |
| `secret_key` | `SIMMATE__WEBSITE__SECRET_KEY` | A unique, secret key for this particular Simmate installation. |
| `allowed_hosts` | `SIMMATE__WEBSITE__ALLOWED_HOSTS` | A list of strings representing the host/domain names that this Simmate site can serve. |
| `csrf_trusted_origins` | `SIMMATE__WEBSITE__CSRF_TRUSTED_ORIGINS` | A list of trusted origins for Unsafe requests (e.g. POST). |

Example `settings.yaml`:
```yaml
website:
  secret_key: "your-very-secret-key"
  allowed_hosts:
    - "simmate.example.com"
  csrf_trusted_origins:
    - "https://simmate.example.com"
```

### Access Control

| Setting | Environment Variable | Description |
| :--- | :--- | :--- |
| `require_login` | `SIMMATE__WEBSITE__REQUIRE_LOGIN` | Whether to require users to be logged in to access any part of the site. |
| `login_message` | `SIMMATE__WEBSITE__LOGIN_MESSAGE` | A message to display on the login page. |

### Email Settings

If you want your server to send automated emails (e.g. for password resets), you must configure an email backend.

| Setting | Environment Variable | Description |
| :--- | :--- | :--- |
| `email.host` | `SIMMATE__WEBSITE__EMAIL__HOST` | The host for sending emails (e.g. `smtp.gmail.com`). |
| `email.port` | `SIMMATE__WEBSITE__EMAIL__PORT` | The port for sending emails (e.g. `587`). |
| `email.host_user` | `SIMMATE__WEBSITE__EMAIL__HOST_USER` | The username for the email host. |
| `email.host_password` | `SIMMATE__WEBSITE__EMAIL__HOST_PASSWORD` | The password for the email host. |

------------------------------------------------------------

## Third-Party Sign-Ins

Simmate supports sign-ins via third-party accounts such as Google, GitHub, and Microsoft, thanks to the [`django-allauth`](https://github.com/pennersr/django-allauth) package.

By default, servers won't display these sign-in buttons. To enable them, you need to provide the Client ID and Secret for each provider.

### GitHub OAuth

1. Create a new OAuth application [here](https://github.com/settings/applications/new) using the following information:
    * **Application name:** My Simmate Server (or any name you prefer)
    * **Homepage URL:** `http://127.0.0.1:8000` (update to your domain in production)
    * **Authorization callback URL:** `http://127.0.0.1:8000/accounts/github/login/callback/`
2. Generate a new client secret and copy it along with the Client ID.
3. Configure Simmate using one of the following methods:

=== "Command Line"
    ```bash
    simmate config update website.social_oauth.github.client_id=YOUR_ID
    simmate config update website.social_oauth.github.secret=YOUR_SECRET
    ```

=== "settings.yaml"
    ```yaml
    website:
      social_oauth:
        github:
          client_id: YOUR_ID
          secret: YOUR_SECRET
    ```

=== "Environment Variables"
    ```bash
    export SIMMATE__WEBSITE__SOCIAL_OAUTH__GITHUB__CLIENT_ID=YOUR_ID
    export SIMMATE__WEBSITE__SOCIAL_OAUTH__GITHUB__SECRET=YOUR_SECRET
    ```

### Google OAuth

1. Follow the [Google Cloud Console guide](https://django-allauth.readthedocs.io/en/latest/providers.html#google) to create your OAuth credentials.
2. For the **Authorized redirect URI**, use `http://127.0.0.1:8000/accounts/google/login/callback/` (update to your domain in production).
3. Configure Simmate:

=== "Command Line"
    ```bash
    simmate config update website.social_oauth.google.client_id=YOUR_ID
    simmate config update website.social_oauth.google.secret=YOUR_SECRET
    ```

=== "settings.yaml"
    ```yaml
    website:
      social_oauth:
        google:
          client_id: YOUR_ID
          secret: YOUR_SECRET
    ```

### Microsoft OAuth

1. Register your application in the [Azure Portal](https://portal.azure.com/).
2. For the **Redirect URI**, use `http://127.0.0.1:8000/accounts/microsoft/login/callback/` (update to your domain in production).
3. Configure Simmate:

=== "Command Line"
    ```bash
    simmate config update website.social_oauth.microsoft.client_id=YOUR_ID
    simmate config update website.social_oauth.microsoft.secret=YOUR_SECRET
    ```

=== "settings.yaml"
    ```yaml
    website:
      social_oauth:
        microsoft:
          client_id: YOUR_ID
          secret: YOUR_SECRET
    ```

!!! note
    By default, Microsoft login is limited to organizations. You can further customize the `TENANT` setting in your Django configuration if needed.

------------------------------------------------------------
