from simmate.compute import schedule

from .models import InventoryRequest


@schedule(interval="daily", at="03:00")
def run_update_inventory_request_statuses():
    """
    Nightly task to refresh how long each inventory request has sat in its
    current status (`status_age`) and how long completed ones took
    (`days_to_completed`).
    """
    InventoryRequest.update_status_age()
    InventoryRequest.update_days_to_completed()
