# -*- coding: utf-8 -*-

from simmate.website.htmx.components.base import HtmxComponent


class TaskManagerComponent(HtmxComponent):
    template_name: str = "lab_automation/components/task_manager.html"

    @property
    def tasks(self) -> dict:
        return {
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
