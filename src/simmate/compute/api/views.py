# -*- coding: utf-8 -*-

import base64

import cloudpickle
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse

from simmate.compute.work_item import WorkItem
from simmate.config import settings
from simmate.website.utils import api_view


def check_worker_permissions(user) -> bool:
    """
    Checks if the user is allowed to act as an API worker based on simmate settings.
    Future implementations will query the project_management app and evaluate
    methods involving collateral_balance to decide if a user is allowed.
    """
    allowed = settings.website.enable_api_workers

    if not allowed or allowed in ["False", "false"]:
        return False
    elif allowed == "superuser-only":
        return user.is_superuser
    elif allowed == "staff-only":
        return user.is_staff or user.is_superuser
    elif allowed == "all-users":
        return True

    return False


@api_view(["POST"])
@login_required
def get_next_work_item(request):
    """
    API endpoint for remote workers to pull the next pending WorkItem.
    Expects JSON data: {"tags": ["simmate", "custom"]}
    """
    tags = request.data.get("tags", ["simmate"])

    if not check_worker_permissions(request.user):
        return JsonResponse(
            {"detail": "You do not have permission to run API workers."}, status=403
        )

    with transaction.atomic():
        # Query for PENDING WorkItems, lock it for editing, and update status
        workitem = (
            WorkItem.objects.select_for_update(skip_locked=True)
            .filter(status="P")
            .filter_by_tags(tags)
            .order_by("created_at")
            .first()
        )

        if not workitem:
            # Note: We return 200 with an empty detail here since empty JsonResponse
            # on 204 sometimes gets stripped or behaves poorly in standard requests
            return JsonResponse({"detail": "No pending work items found."}, status=204)

        # Update status to running
        workitem.status = "R"
        # We don't have a worker object for API workers at the moment, so worker is null
        workitem.save(update_fields=["status", "updated_at"])

    # Convert binary fields to base64 strings for JSON serialization
    response_data = {
        "id": str(workitem.id),
        "fxn": base64.b64encode(workitem.fxn).decode("utf-8"),
        "args": base64.b64encode(workitem.args).decode("utf-8"),
        "kwargs": base64.b64encode(workitem.kwargs).decode("utf-8"),
    }

    return JsonResponse(response_data)


@api_view(["POST"])
@login_required
def update_work_item(request, work_item_id):
    """
    API endpoint for remote workers to submit the result of a WorkItem.
    Expects JSON data:
    {
        "status": "F" or "E" or "P",
        "result": "<base64_encoded_pickled_result>"
    }
    """
    status = request.data.get("status")
    result_b64 = request.data.get("result")

    if not status or not result_b64:
        return JsonResponse({"detail": "Missing status or result data."}, status=400)

    if not check_worker_permissions(request.user):
        return JsonResponse(
            {"detail": "You do not have permission to run API workers."}, status=403
        )

    try:
        result_binary = base64.b64decode(result_b64)
    except Exception:
        return JsonResponse({"detail": "Invalid base64 result data."}, status=400)

    with transaction.atomic():
        try:
            workitem = WorkItem.objects.select_for_update().get(pk=work_item_id)
        except WorkItem.DoesNotExist:
            return JsonResponse({"detail": "WorkItem not found."}, status=404)

        workitem.result_binary = result_binary
        workitem.status = status
        workitem.save()

    return JsonResponse({"detail": "WorkItem updated successfully."}, status=200)
