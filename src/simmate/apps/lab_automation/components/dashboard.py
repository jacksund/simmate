# -*- coding: utf-8 -*-

from django.utils import timezone

from simmate.website.htmx.components import HtmxComponent

from .sensors import AmbientTempComponent, HumidityComponent, SimulatedSensorComponent

# NOTE: everything below is placeholder data until real devices, agents, and
# task scheduling are connected. The sensor readings are simulated separately
# (see `sensors.py`).

HOTPLATES = [
    {
        "name": "Hotplate 1",
        "experiment": "Synthesis of YBa2Cu3O7",
        "current_step": "Ramp to 150 °C",
        "time_remaining": "2h 15m",
        "owner": "John Doe",
        "status_text": "Running",
        "status_theme": "primary",
        "temp_component": "hotplate-temp-component",
        "stir_component": "hotplate-stir-component",
    },
    {
        "name": "Hotplate 2",
        "experiment": "Calcination of Sample C",
        "current_step": "Hold at 80 °C",
        "time_remaining": "45m",
        "owner": "Jane Smith",
        "status_text": "Running",
        "status_theme": "primary",
        "temp_component": "hotplate2-temp-component",
        "stir_component": "hotplate2-stir-component",
    },
]

TASK_COLUMNS = [
    # (key, title, icon, bootstrap color)
    ("scheduled", "Scheduled", "bi-calendar-event", "secondary"),
    ("preparing", "Preparing", "bi-box-seam", "info"),
    ("running", "Running", "bi-play-circle", "primary"),
    ("completed", "Completed", "bi-check-circle", "success"),
    ("failed", "Failed", "bi-x-circle", "danger"),
]

PRIORITY_THEMES = {"high": "danger", "medium": "warning", "low": "secondary"}

TASKS = {
    "scheduled": [
        {
            "name": "Calcination of Sample C",
            "duration": "12h",
            "owner": "John Doe",
            "priority": "high",
            "equipment": "Furnace 1",
        },
        {
            "name": "Furnace maintenance",
            "duration": "4h",
            "owner": "Auto-Agent",
            "priority": "low",
            "equipment": "Furnace 2",
        },
        {
            "name": "Prepare Precursors",
            "duration": "1h",
            "owner": "Jane Smith",
            "priority": "medium",
            "equipment": "Fume Hood",
        },
    ],
    "preparing": [
        {
            "name": "Weighing Reactants for D",
            "status": "In Fume Hood",
            "owner": "Jane Smith",
            "equipment": "Scale 2",
        },
        {
            "name": "Calibration of Hotplate 2",
            "status": "Warming Up",
            "owner": "Auto-Agent",
            "equipment": "Hotplate 2",
        },
    ],
    "running": [
        {
            "name": "Synthesis of YBa2Cu3O7",
            "progress": 65,
            "eta": "2h 15m",
            "owner": "John Doe",
            "equipment": "Furnace 1",
        },
        {
            "name": "Stirring Precursor B",
            "progress": 80,
            "eta": "10m",
            "owner": "Jane Smith",
            "equipment": "Hotplate 1",
        },
        {
            "name": "Data Collection Run",
            "progress": 15,
            "eta": "5h",
            "owner": "Auto-Agent",
            "equipment": "Spectrometer",
        },
    ],
    "completed": [
        {
            "name": "Milling of Precursor A",
            "time": "2 hours ago",
            "owner": "John Doe",
            "equipment": "Ball Mill",
        },
        {
            "name": "Data export to LIMS",
            "time": "5 hours ago",
            "owner": "System",
            "equipment": "Server",
        },
        {
            "name": "Sample Cleaning",
            "time": "1 day ago",
            "owner": "Jane Smith",
            "equipment": "Ultrasonic Bath",
        },
    ],
    "failed": [
        {
            "name": "XRD Analysis of Batch 12",
            "reason": "Sample Contamination",
            "owner": "Jane Smith",
            "equipment": "XRD",
        },
        {
            "name": "Auto-sampler calibration",
            "reason": "Timeout",
            "owner": "Auto-Agent",
            "equipment": "Auto-sampler",
        },
    ],
}

AGENT_STATUS_THEMES = {
    "Active": ("success", "bi-check-circle"),
    "Under Maintenance": ("warning", "bi-tools"),
    "On Vacation": ("secondary", "bi-pause-circle"),
}

AGENTS = [
    {
        "name": "RoboChemist Alpha",
        "type": "Autonomous Robot",
        "is_robot": True,
        "status": "Active",
        "current_task": "Weighing out reactants",
        "objective": "High-throughput Synthesis Prep",
        "location": "Scale 2",
        "icon": "bi-robot",
        "progress": 45,
    },
    {
        "name": "Jane Smith",
        "type": "Lead Chemist",
        "is_robot": False,
        "status": "Active",
        "current_task": "Setting up glassware",
        "objective": "Preparation for Calcination",
        "location": "Fume Hood 1",
        "icon": "bi-person-badge",
        "progress": 80,
    },
    {
        "name": "Auto-Sampler Unit 1",
        "type": "Autonomous Robot",
        "is_robot": True,
        "status": "Under Maintenance",
        "current_task": "Recalibrating sensors",
        "objective": "Routine Checkup",
        "location": "XRD Room",
        "icon": "bi-cpu",
        "progress": 15,
    },
    {
        "name": "John Doe",
        "type": "Researcher",
        "is_robot": False,
        "status": "On Vacation",
        "current_task": None,
        "objective": "Rest and Recharge",
        "location": "Out of Office",
        "icon": "bi-person",
        "progress": 0,
    },
    {
        "name": "Dr. Sarah Lee",
        "type": "Chemist",
        "is_robot": False,
        "status": "Active",
        "current_task": "Running XRD on Batch 12",
        "objective": "Phase Identification",
        "location": "XRD Room",
        "icon": "bi-person-badge",
        "progress": 60,
    },
    {
        "name": "Cleaning Drone Beta",
        "type": "Autonomous Robot",
        "is_robot": True,
        "status": "Active",
        "current_task": "Cleaning Glassware",
        "objective": "Lab Hygiene & Maintenance",
        "location": "Sink 1",
        "icon": "bi-stars",
        "progress": 90,
    },
]

AI_SUMMARY = (
    "Current focus is on synthesizing high-purity YBa2Cu3O7 superconductor samples. "
    "Recent XRD results from Batch 11 indicate an optimal calcination profile, so the "
    "current task (Batch 12) is replicating those exact parameters. "
    "Hotplate 1 is currently pre-heating for the next synthesis step while "
    "Hotplate 2 performs calcination for Sample C. "
    "All environment sensors are nominal. Lab humidity is perfectly controlled at 35%."
)


class LabDashboardComponent(HtmxComponent):
    """
    Lab automation dashboard showing lab conditions, equipment, the task
    board, and the people & robots working in the lab.

    The sensor cards are separate components that refresh themselves, so this
    component does not set a `refresh_interval` (which would rebuild them).
    """

    template_name = "lab_automation/dashboard.html"

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def get_context(self):
        ctx = super().get_context()
        ctx.update(
            last_updated=timezone.now(),
            sensor_refresh_interval=SimulatedSensorComponent.refresh_interval,
            summary_cards=self.get_summary_cards(),
            alerts=self.get_alerts(),
            hotplates=HOTPLATES,
            task_columns=self.get_task_columns(),
            agents=self.get_agents(),
            ai_summary=AI_SUMMARY,
        )
        return ctx

    # -------------------------------------------------------------------------
    # Data
    # -------------------------------------------------------------------------

    @staticmethod
    def get_summary_cards() -> list[dict]:
        """
        Builds the KPI cards shown at the top of the dashboard.

        Returns:
            A list of dictionaries, each describing a single card.
        """
        nrunning = len(TASKS["running"])
        nqueued = len(TASKS["scheduled"]) + len(TASKS["preparing"])
        nfailed = len(TASKS["failed"])

        nactive = sum(a["status"] == "Active" for a in AGENTS)
        nrobots = sum(a["is_robot"] and a["status"] == "Active" for a in AGENTS)
        nmaintenance = sum(a["status"] == "Under Maintenance" for a in AGENTS)

        nhotplates = len(HOTPLATES)

        return [
            {
                "title": "Running Tasks",
                "value": f"{nrunning:,}",
                "subtext": f"{nqueued} scheduled or preparing",
                "badge_text": f"{nfailed} failed" if nfailed else "none failed",
                "badge_theme": "danger" if nfailed else "success",
                "icon": "bi-play-circle",
                "icon_theme": "primary",
            },
            {
                "title": "Equipment",
                "value": f"{nhotplates}",
                "subtext": "hotplates running experiments",
                "badge_text": "all online",
                "badge_theme": "success",
                "icon": "bi-thermometer-high",
                "icon_theme": "danger",
            },
            {
                "title": "Agents Active",
                "value": f"{nactive} / {len(AGENTS)}",
                "subtext": f"{nrobots} robots · {nactive - nrobots} people",
                "badge_text": (
                    f"{nmaintenance} in maintenance" if nmaintenance else "all ready"
                ),
                "badge_theme": "warning" if nmaintenance else "success",
                "icon": "bi-robot",
                "icon_theme": "success",
            },
            {
                "title": "Lab Climate",
                "value": f"{AmbientTempComponent.target:.1f} °C",
                "subtext": f"{HumidityComponent.target:.0f}% humidity",
                "badge_text": "nominal",
                "badge_theme": "success",
                "icon": "bi-thermometer-half",
                "icon_theme": "info",
            },
        ]

    @staticmethod
    def get_alerts() -> list[dict]:
        """
        Collects issues that likely need someone to step in.

        Returns:
            A list of dictionaries with a `level` (bootstrap color), `icon`,
            and `message`.
        """
        alerts = []
        for task in TASKS["failed"]:
            alerts.append(
                {
                    "level": "danger",
                    "icon": "bi-x-octagon",
                    "message": (
                        f"{task['name']} failed on {task['equipment']}: "
                        f"{task['reason']}"
                    ),
                    "owner": task["owner"],
                }
            )
        for agent in AGENTS:
            if agent["status"] == "Under Maintenance":
                alerts.append(
                    {
                        "level": "warning",
                        "icon": "bi-tools",
                        "message": (
                            f"{agent['name']} is under maintenance "
                            f"({agent['current_task'].lower()})"
                        ),
                        "owner": agent["location"],
                    }
                )
        for task in TASKS["scheduled"]:
            if task["priority"] == "high":
                alerts.append(
                    {
                        "level": "warning",
                        "icon": "bi-flag",
                        "message": (
                            f"High-priority task '{task['name']}' is waiting "
                            f"on {task['equipment']}"
                        ),
                        "owner": task["owner"],
                    }
                )
        return alerts

    @staticmethod
    def get_task_columns() -> list[dict]:
        """
        Groups tasks into the columns of the task board. Scheduled tasks also
        get a `priority_theme`.
        """
        columns = []
        for key, title, icon, theme in TASK_COLUMNS:
            tasks = [
                {**task, "priority_theme": PRIORITY_THEMES.get(task.get("priority"))}
                for task in TASKS[key]
            ]
            columns.append(
                dict(key=key, title=title, icon=icon, theme=theme, tasks=tasks)
            )
        return columns

    @staticmethod
    def get_agents() -> list[dict]:
        """
        Adds the badge theme & icon for each agent's status.
        """
        agents = []
        for agent in AGENTS:
            theme, icon = AGENT_STATUS_THEMES[agent["status"]]
            agents.append({**agent, "badge_theme": theme, "badge_icon": icon})
        return agents
