# Settings and Configuration

Simmate uses a centralized settings system to manage everything from database connections to application-specific commands. This ensures that your research environment is reproducible and easy to configure across different machines.

---

## Viewing Your Current Settings

Before making any changes, you should check which settings Simmate is currently using. You can do this via the command line:

```bash
simmate config show
```

This command merges all settings from environment variables, YAML files, and built-in defaults to show you the final configuration. If you only want to see the settings you have manually defined (excluding defaults), use:

```bash
simmate config show --user-only
```

---

## How Settings are Loaded

Simmate builds its final configuration by merging user-defined settings with built-in defaults. When looking for user overrides, it checks the following sources in order of priority:

1. **Environment Variables**: Any variable prefixed with `SIMMATE__` (e.g., `SIMMATE__DATABASE__NAME`).
2. **`settings.yaml`**: A configuration file in your Simmate directory.
3. **Defaults**: If no overrides are found, Simmate uses its internal default values.

!!! danger "No Mixing of Sources"
    Simmate does not allow mixing sources. For example, if any environment variable starting with `SIMMATE__` is set, Simmate will **ignore all YAML files**. This prevents confusion about where a specific setting originated.

---

## Configuration Directory

By default, Simmate stores its configuration files, local databases, and log files in a folder named `simmate` within your home directory:

- **Windows**: `C:\Users\YourUser\simmate\`
- **Linux/Mac**: `~/simmate/`

You can override this location by setting the `SIMMATE_CONFIG_DIR` environment variable. Note that this variable does **not** use the `SIMMATE__` prefix because it is used to locate the settings themselves.

---

## Core Settings

These settings are used by the core Simmate framework and apply to all workflows and apps.

### Apps
The `apps` setting is a list of registered Simmate applications. Simmate comes with many apps enabled by default (such as VASP, Quantum Espresso, and Materials Project). 

If you want to register a custom app or limit Simmate to a specific set of apps, you can override this list in your settings:

```yaml
apps:
  - simmate.apps.configs.VaspConfig
  - my_custom_app.apps.Config
```

### Database
Simmate uses the Django ORM and supports multiple database backends. 

**SQLite (Default)**
The default is a local SQLite database named `database.sqlite3` stored in your configuration directory. To allow multiple projects to coexist on the same machine, you can change your `SIMMATE_CONFIG_DIR` environment variable to point to different directories.

**PostgreSQL**
For production or shared environments, PostgreSQL is recommended:

```yaml
database:
  engine: django.db.backends.postgresql
  name: simmate_db
  user: simmate_user
  password: your_password
  host: localhost
  port: 5432
```

### Website
The Simmate web interface can be configured for local development or production-scale deployments.

**Security and Access**
These settings control who can access your data and how the server identifies itself.

- `debug`: If `true`, Django's debug mode is enabled. Never use this in production.
- `require_login`: If `true`, users must be authenticated to view any data.
- `allowed_hosts`: List of host/domain names that this Simmate site can serve.
- `csrf_trusted_origins`: Origins allowed for CSRF-protected requests.

**Social Login and Email**
For production servers, you can enable social login (OAuth) and email notifications for error reporting and account verification:

```yaml
website:
  social_oauth:
    google:
      client_id: your_id
      secret: your_secret
  email:
    host: smtp.gmail.com
    port: 587
    host_user: simmate.team@gmail.com
    host_password: your_password
```

For more detailed information on configuring the web interface, see the **[Website full guide](./website/setup_and_config.md)**.

---

## App-Specific Settings

Many Simmate apps require specific configurations, such as the command used to run an external program or an API key for a third-party service.

Common app settings include:

- **VASP**: `vasp.default_command`
- **Quantum Espresso**: `quantum_espresso.default_command` and `quantum_espresso.psuedo_dir`
- **Bader**: `bader.default_command`
- **Materials Project**: `cas_registry.api_key` (for molecular data)

For detailed information on how to configure a specific app, please refer to the **[Apps tab](../apps/overview.md)**. Each app page includes a "Configuration" section with the relevant settings.

---

## Managing Settings

Simmate provides two primary ways to manage your settings: environment variables and the command-line interface.

### Environment Variables
When using environment variables, use double underscores (`__`) to represent nesting in the YAML structure and prefix everything with `SIMMATE__`. All keys should be uppercase.

| YAML Setting | Environment Variable |
| :--- | :--- |
| `database.name` | `SIMMATE__DATABASE__NAME` |
| `vasp.default_command` | `SIMMATE__VASP__DEFAULT_COMMAND` |
| `website.require_login` | `SIMMATE__WEBSITE__REQUIRE_LOGIN` |

!!! info "List Separators"
    For list-based settings (like `apps` or `website.allowed_hosts`), use a **space-separated** string when using environment variables:
    `export SIMMATE__APPS="simmate.apps.configs.VaspConfig simmate.apps.configs.BaderConfig"`

### Command Line
The `simmate config` command group provides several utilities for managing your settings from the terminal.

**View Current Settings**
To see the final merged settings currently in use:
```bash
simmate config show
```

**Save Settings to File**
To export your current configuration to a YAML file:
```bash
simmate config write
```
By default, this writes to a file named `settings.yaml` in your config directory.

**Update a Setting**
You can update settings directly using dot-notation:
```bash
simmate config update "vasp.default_command=mpirun -n 8 vasp_std > vasp.out"
```

**Add an App**
To quickly register a new app:
```bash
simmate config add vasp
```

**Test Configuration**
To verify if an app is properly configured (e.g., checking if the command exists):
```bash
simmate config test vasp
```

---

## Advanced Configuration

### Django Settings Override
If you need to override a Django setting that isn't explicitly exposed by Simmate, you can use the `django_settings` key. This dictionary is merged directly into Simmate's Django configuration.

```yaml
django_settings:
  DATA_UPLOAD_MAX_NUMBER_FIELDS: 10000
  SESSION_COOKIE_AGE: 86400
```
