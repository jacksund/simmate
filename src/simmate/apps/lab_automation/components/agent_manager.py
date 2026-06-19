# -*- coding: utf-8 -*-

from simmate.website.htmx.components.base import HtmxComponent

class AgentManagerComponent(HtmxComponent):
    template_name: str = "lab_automation/components/agent_manager.html"

    @property
    def agents(self) -> list:
        return [
            {
                "name": "RoboChemist Alpha",
                "type": "Autonomous AI Robot",
                "status": "Active",
                "current_task": "Weighing out reactants",
                "objective": "High-throughput Synthesis Prep",
                "location": "Scale 2",
                "icon": "fas fa-robot",
                "status_color": "success",
                "progress": 45,
            },
            {
                "name": "Jane Smith",
                "type": "Lead Chemist",
                "status": "Active",
                "current_task": "Setting up glassware",
                "objective": "Preparation for Calcination",
                "location": "Fume Hood 1",
                "icon": "fas fa-user-md",
                "status_color": "success",
                "progress": 80,
            },
            {
                "name": "Auto-Sampler Unit 1",
                "type": "Autonomous AI Robot",
                "status": "Under Maintenance",
                "current_task": "Recalibrating sensors",
                "objective": "Routine Checkup",
                "location": "XRD Room",
                "icon": "fas fa-microchip",
                "status_color": "warning",
                "progress": 15,
            },
            {
                "name": "John Doe",
                "type": "Researcher",
                "status": "On Vacation",
                "current_task": "None",
                "objective": "Rest and Recharge",
                "location": "Out of Office",
                "icon": "fas fa-umbrella-beach",
                "status_color": "secondary",
                "progress": 0,
            },
            {
                "name": "Dr. Sarah Lee",
                "type": "Chemist",
                "status": "Active",
                "current_task": "Running XRD on Batch 12",
                "objective": "Phase Identification",
                "location": "XRD Room",
                "icon": "fas fa-user-tie",
                "status_color": "success",
                "progress": 60,
            },
            {
                "name": "Cleaning Drone Beta",
                "type": "Autonomous AI Robot",
                "status": "Active",
                "current_task": "Cleaning Glassware",
                "objective": "Lab Hygiene & Maintenance",
                "location": "Sink 1",
                "icon": "fas fa-broom",
                "status_color": "success",
                "progress": 90,
            }
        ]
