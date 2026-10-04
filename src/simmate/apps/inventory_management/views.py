# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    """
    Inventory Management dashboard. All metrics are rendered (and
    auto-refreshed) by the `InventoryDashboardComponent`.
    """
    context = {
        "page_title": "Inventory Management",
        "breadcrumbs": ["Apps", "Inventory Management"],
    }
    return render(request, "inventory_management/home.html", context)
