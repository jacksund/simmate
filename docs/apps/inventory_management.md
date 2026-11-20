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

To make a single request, click "Request More" in the "Requests" tab of a substance or mixture page. To request many items at once, make a request list (see below).

--------------------------------------------------------------------------------

## Request Lists

Requests are often made in groups, such as a round of 40 targets for a project or a batch of items to order from one supplier. The `InventoryRequestList` table keeps these together. Each list (e.g. "RL-12") has a title, description, and project, and its requests link back to it through their `request_list` column.

### Making a List

Go to `/data/InventoryRequestList/new/` (or click "New List" on the Inventory Request Lists table). The form has three parts:

1. **List Info:** the title, description, and project.
2. **Shared Values:** values for every request in the list, such as the requester, priority, fulfillment type, and supplier.
3. **Items:** one row per request. Rows can be loaded from a CSV or Excel (`.xlsx`) file, pasted as text, or added by hand. Every row can be edited before the list is saved.

Each row's `item` is a substance ID (e.g. `BCD-012-3456`), a mixture ID (e.g. `BCDF-123`), or a SMILES. New SMILES are registered as substances when the list is saved. A list can have up to 100 requests.

Files must have a header row. Only the `item` column is required, and the other columns are optional:

| Column | Example | Other accepted names |
|---|---|---|
| `item` | BCD-012-3456 or CCO | substance, substance_id, mixture, mixture_id, smiles, compound, id |
| `amount` | 50 | |
| `amount_units` | mg | units, unit |
| `fulfillment_type` | Internal Synthesis, External Synthesis, or Purchased | fulfillment |
| `priority` | Low, Medium, or High | |
| `needed_by` | 2026-12-31 | |
| `supplier` | Sigma-Aldrich | vendor |
| `supplier_catalog_number` | 50-177-2891 | catalog_number, product_number |
| `estimated_cost` | 120.50 (USD) | cost |
| `comments` | Needed for the dose-response assay | comment, notes |

Headers are matched ignoring case, spaces, and punctuation (e.g. "Amount Units" works). A template with these columns can be downloaded from the form. Pasted text can be cells copied from Excel, or one item per line with an optional amount and units (e.g. `BCD-012-3456, 50, mg`).

Any cell that is left blank uses the shared value of that column. A row can give its own value, but can't clear a shared value. The requester, assignee, and project are only set for the whole list.

### Checks Before Saving

Every row is checked as the table is edited. Each row shows whether its item is an existing substance, an existing mixture, a new substance, or invalid. Problems are listed on their row:

- **Errors** must be fixed before saving. Examples are an unknown ID, an invalid SMILES, an amount without units, or a priority that isn't one of the options.
- **Warnings** are an item that is listed more than once, or an item that already has open requests. To save anyway, click "Save Anyway".

The list and all of its requests are saved together, so either every request is made or none are. New requests start as "Under Review" and are requested by the submitter, unless a different requester is chosen.

### Tracking a List

A list's status comes from its requests:

| Status | When |
|---|---|
| Open | any request is still open (e.g. "In Progress") |
| Completed | every request is completed |
| Closed | no request is open, but some did not complete (e.g. "Failed" or "Canceled") |
| Empty | the list has no requests |

The list's page shows its progress, how many requests are at each status, and the requests themselves. From there, admins can click "Edit in Table" and then "Select All" and "Update" to change up to 100 requests at once (e.g. to approve or assign all of them). New comments are added after any existing comments.

### Making Lists in Python

The website's form uses `InventoryRequestList.create_with_requests`, which can also be used in scripts:

``` python
from simmate.apps.inventory_management.models import InventoryRequestList

request_list = InventoryRequestList.create_with_requests(
    title="Round 3 targets",
    rows=[
        dict(item="BCD-012-3456", amount="50", amount_units="mg"),
        dict(item="CCO", priority="High"),
    ],
    shared=dict(fulfillment_type="Internal Synthesis", priority="Medium"),
    submitted_by=user,
)
```

If any row is invalid, a `ValidationError` is raised with every message and nothing is saved. Use `InventoryRequestList.check_rows` to check rows without saving, and `allow_warnings=True` to save even if there are warnings.

--------------------------------------------------------------------------------
