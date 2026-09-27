# -*- coding: utf-8 -*-

from django.shortcuts import render


def home(request):
    """
    Compute dashboard showing key operational metrics, workflow runs,
    worker pool status, and cluster resource health.
    """
    summary_cards = [
        {
            "title": "Active Workers",
            "value": "16",
            "subtext": "14 busy, 2 idle",
            "badge_text": "+4 scaling up",
            "badge_class": "bg-success-subtle text-success border border-success",
            "icon": "bi-cpu",
            "icon_bg": "bg-primary-subtle text-primary",
        },
        {
            "title": "Active Calculations",
            "value": "42",
            "subtext": "9 queued in backlog",
            "badge_text": "SLURM & Cloud",
            "badge_class": "bg-info-subtle text-info border border-info",
            "icon": "bi-gear-wide-connected",
            "icon_bg": "bg-info-subtle text-info",
        },
        {
            "title": "Completed Workflows",
            "value": "18,492",
            "subtext": "99.4% success rate",
            "badge_text": "+342 today",
            "badge_class": "bg-success-subtle text-success border border-success",
            "icon": "bi-check2-circle",
            "icon_bg": "bg-success-subtle text-success",
        },
        {
            "title": "Cataloged Structures",
            "value": "1,452,890",
            "subtext": "Across 6 databases",
            "badge_text": "Synced 10m ago",
            "badge_class": "bg-secondary-subtle text-secondary border border-secondary",
            "icon": "bi-database",
            "icon_bg": "bg-warning-subtle text-warning",
        },
    ]

    workflow_distribution = [
        {
            "name": "Relaxation (VASP / QE)",
            "runs": "8,321",
            "percentage": 45,
            "color_class": "bg-primary",
        },
        {
            "name": "Static Energy",
            "runs": "5,548",
            "percentage": 30,
            "color_class": "bg-info",
        },
        {
            "name": "Electronic Structure (DOS/BS)",
            "runs": "2,774",
            "percentage": 15,
            "color_class": "bg-success",
        },
        {
            "name": "Molecular Dynamics & NEB",
            "runs": "1,849",
            "percentage": 10,
            "color_class": "bg-warning",
        },
    ]

    recent_calculations = [
        {
            "run_id": "calc-849201",
            "workflow": "relaxation.vasp.matproj",
            "formula": "LiFePO4",
            "status": "Running",
            "elapsed": "4m 12s",
            "worker": "slurm-node-03",
        },
        {
            "run_id": "calc-849200",
            "workflow": "static-energy.vasp.matproj",
            "formula": "MoS2",
            "status": "Running",
            "elapsed": "11m 45s",
            "worker": "slurm-node-01",
        },
        {
            "run_id": "calc-849199",
            "workflow": "population-analysis.bader.default",
            "formula": "SrTiO3",
            "status": "Queued",
            "elapsed": "In Queue",
            "worker": "pending",
        },
        {
            "run_id": "calc-849198",
            "workflow": "band-structure.vasp.quality01",
            "formula": "CsPbI3",
            "status": "Completed",
            "elapsed": "38m 20s",
            "worker": "cloud-k8s-pod-07",
        },
        {
            "run_id": "calc-849197",
            "workflow": "density-of-states.vasp.matproj",
            "formula": "BaTiO3",
            "status": "Completed",
            "elapsed": "24m 05s",
            "worker": "cloud-k8s-pod-02",
        },
        {
            "run_id": "calc-849196",
            "workflow": "dynamics.vasp.molecular-dynamics",
            "formula": "GaN",
            "status": "Completed",
            "elapsed": "2h 15m",
            "worker": "slurm-node-04",
        },
        {
            "run_id": "calc-849195",
            "workflow": "relaxation.vasp.staged",
            "formula": "YBa2Cu3O7",
            "status": "Failed",
            "elapsed": "1m 30s",
            "worker": "slurm-node-02",
        },
    ]

    cluster_health = [
        {
            "name": "HPC SLURM Partition",
            "description": "Compute cluster for high-memory DFT calculations",
            "status": "Healthy",
            "status_class": "text-success",
            "cpu_usage": 92,
            "cores_active": "120 / 128 Cores",
            "memory": "720 GB / 1 TB",
        },
        {
            "name": "Kubernetes Cloud Pool",
            "description": "Autoscaling cloud workers for lightweight jobs",
            "status": "Operational",
            "status_class": "text-success",
            "cpu_usage": 64,
            "cores_active": "32 / 48 Cores",
            "memory": "192 GB / 256 GB",
        },
        {
            "name": "Database & RDKit Extensions",
            "description": "PostgreSQL instance with scientific indices",
            "status": "Optimal",
            "status_class": "text-success",
            "cpu_usage": 28,
            "cores_active": "Storage 42 GB / 250 GB",
            "memory": "IOPS 2,400 / 3,000",
        },
        {
            "name": "Message Broker & Cache",
            "description": "Redis task queue and session backend",
            "status": "Optimal",
            "status_class": "text-success",
            "cpu_usage": 14,
            "cores_active": "Latency 1.1 ms",
            "memory": "Memory 210 MB / 4 GB",
        },
    ]

    context = {
        "page_title": "Compute Dashboard",
        "breadcrumbs": ["Apps", "Compute"],
        "summary_cards": summary_cards,
        "workflow_distribution": workflow_distribution,
        "recent_calculations": recent_calculations,
        "cluster_health": cluster_health,
    }
    return render(request, "compute/home.html", context)
