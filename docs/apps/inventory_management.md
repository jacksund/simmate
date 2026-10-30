# Inventory Management

--------------------------------------------------------------------------------

## About

The `inventory_management` app is a website dashboard for tracking lab chemicals, containers, batches, and storage locations. Each chemical is registered once as a substance (e.g. an element, molecule, or material) with a human-readable ID, and physical samples are tracked as batches in containers. Substances can also be combined into mixtures.

--------------------------------------------------------------------------------

## Installation

1. Add `inventory_management` to the list of installed Simmate apps with:
``` bash
simmate config add inventory_management
```

2. Update your database to include custom tables from the app:
``` shell
simmate database update
```

3. Start the website and go to `/apps/inventory_management/`:
``` bash
simmate website start
```

--------------------------------------------------------------------------------
