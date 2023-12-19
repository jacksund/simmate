# Warren Lab App Installation

## Installation

1. Make sure you have Simmate installed and have reset your database.

2. Register the warrenapp with simmate by adding `- warrenapp.apps.WarrenConfig` to `~/simmate/my_env-apps.yaml`

3. Update your database to include custom tables from the warrenapp
``` shell
simmate database update
```
