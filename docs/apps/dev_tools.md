# Dev Tools

--------------------------------------------------------------------------------

## About

The `dev_tools` app is a website dashboard for local diagnostics: git status, Docker containers, and Kubernetes pods. It is meant for developers working on Simmate itself.

!!! warning
    This dashboard is only served when `website.debug` is `True` in your settings, so it is never exposed on a production server.

--------------------------------------------------------------------------------

## Installation

1. Add `dev_tools` to the list of installed Simmate apps with:
``` bash
simmate config add dev_tools
```

2. Turn on debug mode for the website:
``` bash
simmate config update "website.debug=True"
```

3. Start the website and go to `/apps/dev_tools/`:
``` bash
simmate website start
```

--------------------------------------------------------------------------------
