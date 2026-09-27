# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    """
    Inventory Management dashboard view showing summaries of chemical substances,
    containers, storage locations, batches, and recent usage activity.
    """
    summary_cards = [
        {
            "title": "Substances",
            "value": "1,280",
            "subtext": "Unique chemical entities",
            "badge_text": "+14 this month",
            "badge_class": "bg-primary-subtle text-primary border border-primary-subtle",
            "icon": "bi-flask",
            "icon_bg": "bg-primary-subtle text-primary",
        },
        {
            "title": "Containers in Stock",
            "value": "4,350",
            "subtext": "3 low-stock warnings",
            "badge_text": "98% barcoded",
            "badge_class": "bg-success-subtle text-success border border-success",
            "icon": "bi-box-seam",
            "icon_bg": "bg-info-subtle text-info",
        },
        {
            "title": "Storage Locations",
            "value": "18",
            "subtext": "Freezers, cabinets, gloveboxes",
            "badge_text": "All In Bounds",
            "badge_class": "bg-success-subtle text-success border border-success",
            "icon": "bi-geo-alt",
            "icon_bg": "bg-success-subtle text-success",
        },
        {
            "title": "Active Batches",
            "value": "24",
            "subtext": "Formulated mixtures & lots",
            "badge_text": "Active QA",
            "badge_class": "bg-warning-subtle text-warning border border-warning",
            "icon": "bi-layers",
            "icon_bg": "bg-warning-subtle text-warning",
        },
    ]

    recent_usage = [
        {
            "substance": "Lithium Iron Phosphate (LiFePO4)",
            "container_id": "CNT-4821",
            "amount": "25.0 g",
            "user": "jacksund",
            "timestamp": "12m ago",
            "location": "Cabinet B-3",
        },
        {
            "substance": "Dimethyl Sulfoxide (DMSO, 99.9%)",
            "container_id": "CNT-1904",
            "amount": "100.0 mL",
            "user": "researcher_1",
            "timestamp": "45m ago",
            "location": "Flammables Unit 1",
        },
        {
            "substance": "Titanium(IV) Isopropoxide",
            "container_id": "CNT-7320",
            "amount": "15.0 mL",
            "user": "jacksund",
            "timestamp": "2h ago",
            "location": "Glovebox Chamber",
        },
        {
            "substance": "Barium Carbonate (BaCO3)",
            "container_id": "CNT-2291",
            "amount": "50.0 g",
            "user": "lab_tech",
            "timestamp": "4h ago",
            "location": "Solid Reagents Shelf",
        },
        {
            "substance": "Yttrium Oxide (Y2O3)",
            "container_id": "CNT-3110",
            "amount": "10.0 g",
            "user": "lab_tech",
            "timestamp": "Yesterday",
            "location": "Cabinet A-1",
        },
    ]

    storage_locations = [
        {
            "name": "-20 °C Freezer 01",
            "type": "Cold Storage",
            "temp": "-19.8 °C",
            "capacity": "82%",
            "status": "Nominal",
            "status_badge": "bg-success",
        },
        {
            "name": "Argon Glovebox 02",
            "type": "Inert Atmosphere",
            "temp": "< 0.5 ppm O2",
            "capacity": "65%",
            "status": "Active",
            "status_badge": "bg-success",
        },
        {
            "name": "Flammables Safety Cabinet",
            "type": "Hazardous Materials",
            "temp": "20.1 °C",
            "capacity": "91%",
            "status": "Near Capacity",
            "status_badge": "bg-warning",
        },
        {
            "name": "Desiccator Chamber A",
            "type": "Dry Storage",
            "temp": "12% RH",
            "capacity": "40%",
            "status": "Optimal",
            "status_badge": "bg-success",
        },
    ]

    context = {
        "page_title": "Inventory Management",
        "breadcrumbs": ["Apps", "Inventory Management"],
        "summary_cards": summary_cards,
        "recent_usage": recent_usage,
        "storage_locations": storage_locations,
    }
    return render(request, "inventory_management/home.html", context)
