# -*- coding: utf-8 -*-

"""
Mock data for the personal dashboard prototype (`/dashboard/`).

The dashboard is a board of self-contained widgets. Each widget is a dict with:

- `key`: unique id for the widget (used for a user's saved layout later on)
- `title` / `icon`: shown in the widget's header
- `app`: the app that provides the widget (used to group the widget catalog)
- `column`: which column of the board the widget is in ("main" or "side")
- `template`: the template that renders the widget's body
- `link` (optional): a "view all" link shown in the header
- `context`: the data the widget's template uses

Everything here is placeholder data. Once the layout is finalized, each widget
will be backed by a real (HTMX) component that apps register, and the default
layout below will be replaced by the user's saved layout.
"""

WIDGET_TEMPLATES = "core/dashboard/widgets"


def get_platform_pulse() -> list[dict]:
    """
    One compact KPI per installed app, each linking to that app's dashboard.
    Rendered with `core/basic_elements/summary_cards.html`.
    """
    return [
        {
            "title": "Compute",
            "value": "128",
            "subtext": "items queued · 16 workers online",
            "badge_text": "2 alerts",
            "badge_theme": "warning",
            "icon": "bi-cpu",
            "icon_theme": "primary",
            "link": "/apps/compute/",
        },
        {
            "title": "Inventory",
            "value": "4,350",
            "subtext": "containers in stock",
            "badge_text": "7 expiring",
            "badge_theme": "warning",
            "icon": "bi-box-seam",
            "icon_theme": "info",
            "link": "/apps/inventory_management/",
        },
        {
            "title": "Projects",
            "value": "23",
            "subtext": "active projects · 41 members",
            "badge_text": "3 need update",
            "badge_theme": "warning",
            "icon": "bi-kanban",
            "icon_theme": "success",
            "link": "/apps/project_management/",
        },
        {
            "title": "Data Catalogs",
            "value": "1.45M",
            "subtext": "crystals & molecules",
            "badge_text": "synced today",
            "badge_theme": "secondary",
            "icon": "bi-database",
            "icon_theme": "warning",
            "link": "/data/",
        },
    ]


def get_quick_actions() -> list[dict]:
    """
    Shortcuts shown in the dashboard header.
    """
    return [
        {"label": "Submit Workflow", "icon": "bi-play-circle", "url": "/workflows/"},
        {"label": "Explore Data", "icon": "bi-search", "url": "/data/"},
        {
            "label": "Log Reagent Usage",
            "icon": "bi-upc-scan",
            "url": "/apps/inventory_management/",
        },
        {
            "label": "New Project",
            "icon": "bi-plus-square",
            "url": "/apps/project_management/",
        },
    ]


def get_default_widgets() -> list[dict]:
    """
    The default widget layout for a signed-in user, in display order.
    """
    return [
        # ---------------------------------------------------------------------
        # left column
        {
            "key": "needs_attention",
            "title": "Needs My Attention",
            "icon": "bi-bell text-danger",
            "app": "Core",
            "column": "main",
            "template": f"{WIDGET_TEMPLATES}/needs_attention.html",
            "context": {
                "alerts": [
                    {
                        "level": "danger",
                        "icon": "bi-x-octagon",
                        "count": 3,
                        "message": "of your runs failed in the last 24h",
                        "app": "Compute",
                        "url": "/apps/compute/",
                    },
                    {
                        "level": "warning",
                        "icon": "bi-kanban",
                        "count": 1,
                        "message": "project you lead requires an update (Solid-State Electrolytes)",
                        "app": "Projects",
                        "url": "/apps/project_management/",
                    },
                    {
                        "level": "warning",
                        "icon": "bi-calendar-event",
                        "count": 2,
                        "message": "batches you recently used expire within 30 days",
                        "app": "Inventory",
                        "url": "/apps/inventory_management/",
                    },
                    {
                        "level": "info",
                        "icon": "bi-envelope",
                        "count": 5,
                        "message": "unread notifications",
                        "app": "Inbox",
                        "url": "/accounts/profile/",
                    },
                ],
            },
        },
        {
            "key": "my_runs",
            "title": "My Runs",
            "icon": "bi-cpu text-primary",
            "app": "Compute",
            "column": "main",
            "template": f"{WIDGET_TEMPLATES}/my_runs.html",
            "link": "/apps/compute/",
            "context": {
                "counts": [
                    {"label": "Running", "value": 4, "theme": "primary"},
                    {"label": "Queued", "value": 12, "theme": "secondary"},
                    {"label": "Completed (24h)", "value": 27, "theme": "success"},
                    {"label": "Failed (24h)", "value": 3, "theme": "danger"},
                ],
                "runs": [
                    {
                        "workflow": "relaxation.vasp.matproj",
                        "target": "LiFePO4",
                        "status": "Running",
                        "status_theme": "primary",
                        "duration": "1h 12m",
                        "when": "started 1h ago",
                    },
                    {
                        "workflow": "static-energy.vasp.matproj",
                        "target": "CsPbI3",
                        "status": "Errored",
                        "status_theme": "danger",
                        "duration": "4m",
                        "when": "2h ago",
                    },
                    {
                        "workflow": "band-structure.vasp.matproj-hse",
                        "target": "GaN",
                        "status": "Completed",
                        "status_theme": "success",
                        "duration": "3h 40m",
                        "when": "3h ago",
                    },
                    {
                        "workflow": "population-analysis.vasp-bader.badelf-pbesol",
                        "target": "Y2C",
                        "status": "Completed",
                        "status_theme": "success",
                        "duration": "52m",
                        "when": "5h ago",
                    },
                    {
                        "workflow": "relaxation.vasp.matproj",
                        "target": "Na3PS4",
                        "status": "Queued",
                        "status_theme": "secondary",
                        "duration": "—",
                        "when": "queued 6h ago",
                    },
                ],
            },
        },
        {
            "key": "results_digest",
            "title": "Latest Results",
            "icon": "bi-graph-up-arrow text-success",
            "app": "Workflows",
            "column": "main",
            "template": f"{WIDGET_TEMPLATES}/results_digest.html",
            "link": "/workflows/",
            "context": {
                "results": [
                    {
                        "target": "GaN",
                        "workflow": "Band Structure (HSE)",
                        "metrics": [
                            ("Band gap", "3.28 eV"),
                            ("Gap type", "direct"),
                        ],
                        "when": "3h ago",
                    },
                    {
                        "target": "Y2C",
                        "workflow": "Population Analysis (BadELF)",
                        "metrics": [
                            ("Electride sites", "1"),
                            ("e⁻ per site", "0.92"),
                        ],
                        "when": "5h ago",
                    },
                    {
                        "target": "Li3PS4",
                        "workflow": "Relaxation (MatProj)",
                        "metrics": [
                            ("Energy", "-4.71 eV/atom"),
                            ("ΔVolume", "+2.3%"),
                        ],
                        "when": "yesterday",
                    },
                ],
            },
        },
        # ---------------------------------------------------------------------
        # right column
        {
            "key": "inbox",
            "title": "Inbox",
            "icon": "bi-envelope text-info",
            "app": "Core",
            "column": "side",
            "template": f"{WIDGET_TEMPLATES}/inbox.html",
            "link": "/accounts/profile/",
            "context": {
                "notifications": [
                    {
                        "icon": "bi-check-circle text-success",
                        "message": "Band structure of GaN completed",
                        "when": "3h ago",
                        "is_read": False,
                    },
                    {
                        "icon": "bi-x-octagon text-danger",
                        "message": "3 static-energy runs errored (ZBRENT)",
                        "when": "2h ago",
                        "is_read": False,
                    },
                    {
                        "icon": "bi-person-plus text-primary",
                        "message": "You were added to “Perovskite Screening”",
                        "when": "yesterday",
                        "is_read": False,
                    },
                    {
                        "icon": "bi-chat-left-text text-secondary",
                        "message": "New comment on Solid-State Electrolytes",
                        "when": "2 days ago",
                        "is_read": True,
                    },
                ],
            },
        },
        {
            "key": "my_projects",
            "title": "My Projects",
            "icon": "bi-kanban text-success",
            "app": "Projects",
            "column": "side",
            "template": f"{WIDGET_TEMPLATES}/my_projects.html",
            "link": "/apps/project_management/",
            "context": {
                "projects": [
                    {
                        "name": "Solid-State Electrolytes",
                        "role": "Leader",
                        "status": "Requires Update",
                        "status_theme": "warning",
                        "when": "updated 11 months ago",
                    },
                    {
                        "name": "Perovskite Screening",
                        "role": "Member",
                        "status": "Active",
                        "status_theme": "success",
                        "when": "updated 2 days ago",
                    },
                    {
                        "name": "Electride Discovery",
                        "role": "Leader",
                        "status": "Active",
                        "status_theme": "success",
                        "when": "updated 1 week ago",
                    },
                ],
            },
        },
        {
            "key": "jump_back_in",
            "title": "Jump Back In",
            "icon": "bi-clock-history text-secondary",
            "app": "Core",
            "column": "side",
            "template": f"{WIDGET_TEMPLATES}/jump_back_in.html",
            "context": {
                "pages": [
                    {
                        "title": "MatprojStructure · Li-Fe-P-O",
                        "icon": "bi-table",
                        "url": "/data/",
                        "when": "20m ago",
                        "is_pinned": True,
                    },
                    {
                        "title": "Compute Dashboard",
                        "icon": "bi-speedometer",
                        "url": "/apps/compute/",
                        "when": "1h ago",
                        "is_pinned": False,
                    },
                    {
                        "title": "Container CNT-4821",
                        "icon": "bi-box-seam",
                        "url": "/apps/inventory_management/",
                        "when": "yesterday",
                        "is_pinned": False,
                    },
                    {
                        "title": "relaxation.vasp.matproj",
                        "icon": "bi-diagram-3",
                        "url": "/workflows/",
                        "when": "2 days ago",
                        "is_pinned": True,
                    },
                ],
            },
        },
    ]


def get_widget_catalog(active_keys: list[str]) -> list[dict]:
    """
    All widgets that a user could add to their dashboard, grouped by the app
    that provides them. Shown in the dashboard's "Customize" mode.

    Args:
        active_keys: The keys of widgets already on the user's dashboard.
    """
    catalog = {
        "Core": [
            (
                "needs_attention",
                "Needs My Attention",
                "bi-bell",
                "Alerts from every app, filtered to you",
            ),
            ("inbox", "Inbox", "bi-envelope", "Your unread notifications"),
            (
                "jump_back_in",
                "Jump Back In",
                "bi-clock-history",
                "Recently visited and pinned pages",
            ),
            (
                "watchlists",
                "Watchlists",
                "bi-binoculars",
                "Saved searches that notify you of new matches",
            ),
            (
                "team_activity",
                "Team Activity",
                "bi-activity",
                "A merged feed of runs, usage, and project updates",
            ),
        ],
        "Compute": [
            (
                "my_runs",
                "My Runs",
                "bi-cpu",
                "Your queued, running, and recent work items",
            ),
            (
                "compute_timeline",
                "Compute Timeline",
                "bi-bar-chart-line",
                "Work items finished over the last 24h",
            ),
        ],
        "Workflows": [
            (
                "results_digest",
                "Latest Results",
                "bi-graph-up-arrow",
                "Key outputs of your finished calculations",
            ),
        ],
        "Projects": [
            (
                "my_projects",
                "My Projects",
                "bi-kanban",
                "Projects you lead or belong to",
            ),
        ],
        "Inventory": [
            (
                "my_lab_activity",
                "My Lab Activity",
                "bi-box-seam",
                "Your recent reagent usage and expiring stock",
            ),
        ],
        "Data Catalogs": [
            (
                "recently_added",
                "Recently Added",
                "bi-hexagon",
                "New structures & molecules in the database",
            ),
        ],
        "Chatbot": [
            (
                "ask_your_data",
                "Ask Your Data",
                "bi-chat-dots",
                "Ask a question about your data or runs",
            ),
        ],
    }
    return [
        {
            "app": app,
            "widgets": [
                {
                    "key": key,
                    "title": title,
                    "icon": icon,
                    "description": description,
                    "is_active": key in active_keys,
                }
                for key, title, icon, description in widgets
            ],
        }
        for app, widgets in catalog.items()
    ]
