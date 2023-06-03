# Warren Lab App Installation

## Installation

1. Make sure you have Simmate installed and have reset your database.

2. Install the warrenapp using pip
``` shell
pip install warrenapp
```

3. Register the warrenapp with simmate by adding `- warrenapp.apps.SimmateWarrenConfig` to `~/simmate/my_env-apps.yaml`

4. Update your database to include custom tables from the warrenapp
``` shell
simmate database update
```
