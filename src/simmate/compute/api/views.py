# -*- coding: utf-8 -*-

import base64
import json

import cloudpickle
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from simmate.compute.work_item import WorkItem


@csrf_exempt
def get_next_work_item(request):
    """
    API endpoint for remote workers to pull the next pending WorkItem.
    Expects JSON data: {"tags": ["simmate", "custom"]}
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    tags = data.get("tags", ["simmate"])

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


@csrf_exempt
def update_work_item(request, work_item_id):
    """
    API endpoint for remote workers to submit the result of a WorkItem.
    Expects JSON data:
    {
        "status": "F" or "E" or "P",
        "result": "<base64_encoded_pickled_result>",
        "command_not_found": true/false
    }
    """
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON."}, status=400)

    status = data.get("status")
    result_b64 = data.get("result")
    command_not_found = data.get("command_not_found", False)

    if not status or not result_b64:
        return JsonResponse({"detail": "Missing status or result data."}, status=400)

    try:
        result_binary = base64.b64decode(result_b64)
    except Exception:
        return JsonResponse({"detail": "Invalid base64 result data."}, status=400)

    with transaction.atomic():
        try:
            workitem = WorkItem.objects.select_for_update().get(pk=work_item_id)
        except WorkItem.DoesNotExist:
            return JsonResponse({"detail": "WorkItem not found."}, status=404)

        if command_not_found:
            nfailures = workitem.command_not_found_failures + 1
            if nfailures == 2:
                workitem.status = "C"
                workitem.result_binary = result_binary
                workitem.save()
            else:
                workitem.command_not_found_failures = nfailures
                workitem.status = "P"  # marked as PENDING to retry
                workitem.save()
            return JsonResponse({"detail": "Command not found handled."}, status=200)

        workitem.result_binary = result_binary
        workitem.status = status
        workitem.save()

    return JsonResponse({"detail": "WorkItem updated successfully."}, status=200)
