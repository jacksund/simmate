# Project Management

--------------------------------------------------------------------------------

## About

The `project_management` app is a website dashboard for tracking project status, teams, and funding. Projects can be grouped with tags, and each user gets a wallet for tracking funding transactions between projects.

--------------------------------------------------------------------------------

## Installation

1. Add `project_management` to the list of installed Simmate apps with:
``` bash
simmate config add project_management
```

2. Update your database to include custom tables from the app:
``` shell
simmate database update
```

3. Start the website and go to `/apps/project_management/`:
``` bash
simmate website start
```

--------------------------------------------------------------------------------
