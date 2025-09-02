import os

from django.shortcuts import render


def home(request):
    dashboard_url = os.environ.get("ANALYSIS_DASHBOARD_URL", "http://localhost:8501/")
    context = {
        "dashboard_url": dashboard_url,
        "page_title": "Analysis Dashboard",
        "breadcrumbs": ["Analysis Dashboard"],
    }
    template = "analysis_dashboard/home.html"
    return render(request, template, context)
