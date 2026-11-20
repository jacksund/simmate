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

## Inventory Requests

The `InventoryRequest` table tracks requests for new batches of substances or mixtures. One table covers three common uses:

- **Targets:** compounds that a chemist or project wants made next
- **Remakes:** more of a substance or mixture that was made in-house before
- **Orders:** items to buy from a supplier, or to have custom-made by a contract lab (CRO)

A request's type is not stored. Instead, it comes from two things:

- Whether the substance or mixture already had batches when the request was made. Requests for new items are shown as "New", and the rest as "Remake".
- `fulfillment_type`, which is how the material will be sourced: `Internal Synthesis`, `External Synthesis`, or `Purchased`. It is left empty until this is decided, and it can be changed later (e.g. if a vendor can't supply an item, it can be made in-house instead).

Each request ends with the `batch` that fulfilled it, and its `status` is one of:

| Stage | Statuses |
|---|---|
| Open | Under Review, Approved, In Progress, On Hold |
| Closed | Completed, Failed, Rejected, Canceled, Duplicate |
| Admin | Staged for Deletion |

Together, `status` and `fulfillment_type` cover the statuses that separate tracking systems often use. For example:

| Older status | `status` | `fulfillment_type` |
|---|---|---|
| Proposed | Under Review | (any) |
| Ready for Ordering | Approved | Purchased |
| Ordered | In Progress | Purchased or External Synthesis |
| Synthesized | Completed | Internal Synthesis |
| Synthesis Failed | Failed | Internal Synthesis |
| Vendor Synthesis Failed | Failed | External Synthesis |
| Unavailable from Vendor | Failed | Purchased |
| Proposal Rejected or Order Denied | Rejected | (any) |
| Ordering Mistake | Canceled | Purchased |

Every change to a request is saved to its history, which is used to find how long it has sat in its current status (`status_age`) and how long it took to complete (`days_to_completed`). These are refreshed nightly by the inventory app's schedule (see `simmate compute scheduler start`).

To make a request, click "Request More" in the "Requests" tab of a substance or mixture page.

--------------------------------------------------------------------------------
