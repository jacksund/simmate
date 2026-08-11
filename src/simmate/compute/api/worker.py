# -*- coding: utf-8 -*-

import base64
import logging
import time
import traceback

import cloudpickle
import requests
from rich import print

from simmate.config import settings
from simmate.utils import get_class

HEADER_ART = r"""
=====================================================================
   _____                  __        _      __         __
  / __(_)_ _  __ _  ___ _/ /____   | | /| / /__  ____/ /_____ ____
 _\ \/ /  ' \/  ' \/ _ `/ __/ -_)  | |/ |/ / _ \/ __/  '_/ -_) __/
/___/_/_/_/_/_/_/_/\_,_/\__/\__/   |__/|__/\___/_/ /_/\_\\__/_/
    (API Worker Mode)
=====================================================================
"""


class ApiWorker:
    """
    A worker that connects to a Simmate REST API for workflows submitted
    via the `run_cloud` method, rather than connecting directly to the database.
    """

    def __init__(
        self,
        tags: list = None,
        nitems_max: int = None,
        timeout: float = None,
        close_on_empty_queue: bool = False,
        waittime_on_empty_queue: float = 15,
        startup_method: str = None,
    ):
        self.server_url = settings.api.url.rstrip("/")
        self.tags = tags or ["simmate"]
        self.nitems_max = nitems_max if nitems_max else float("inf")
        self.timeout = timeout if timeout else float("inf")
        self.close_on_empty_queue = close_on_empty_queue
        self.waittime_on_empty_queue = waittime_on_empty_queue
        self.startup_method = startup_method

        self.session = requests.Session()
        if settings.api.key:
            self.session.headers.update({"Authorization": f"Token {settings.api.key}"})

        self.nitems_completed = 0

    def start(self):
        """
        Starts the worker process to begin working through WorkItems
        """

        try:
            print("[bold dark_cyan]" + HEADER_ART)
            logging.info(
                f"Starting API worker with tags {self.tags} pointing to {self.server_url}"
            )

            if self.startup_method:
                logging.info(f"Running startup method: '{self.startup_method}'")
                startup_method = get_class(self.startup_method)
                startup_method()

            time_start = time.time()
            self.nitems_completed = 0

            logging.info("Worker is ready & listening for WorkItems via API")

            while True:
                if (time.time() - time_start) > self.timeout:
                    logging.info(
                        "The time-limit for this worker has been hit. Shutting down."
                    )
                    return

                if self.nitems_completed >= self.nitems_max:
                    logging.info(
                        f"Maximum number of WorkItems reached ({self.nitems_max}). "
                        "Shutting down."
                    )
                    return

                # Request the next work item
                try:
                    response = self.session.post(
                        f"{self.server_url}/compute/work_items/next/",
                        json={"tags": self.tags},
                    )
                    response.raise_for_status()
                except requests.exceptions.RequestException as exc:
                    logging.warning(
                        f"Failed to connect to API: {exc}. Retrying in {self.waittime_on_empty_queue}s..."
                    )
                    time.sleep(self.waittime_on_empty_queue)
                    continue

                if response.status_code == 204:
                    # Queue is empty
                    if self.close_on_empty_queue:
                        logging.info("The task queue is empty. Shutting down.")
                        return
                    time.sleep(self.waittime_on_empty_queue)
                    continue

                workitem_data = response.json()
                workitem_id = workitem_data["id"]

                logging.info(f"Running WorkItem with id {workitem_id}")

                try:
                    fxn = cloudpickle.loads(base64.b64decode(workitem_data["fxn"]))
                    args = cloudpickle.loads(base64.b64decode(workitem_data["args"]))
                    kwargs = cloudpickle.loads(
                        base64.b64decode(workitem_data["kwargs"])
                    )
                except Exception as exc:
                    logging.error(f"Failed to unpickle WorkItem {workitem_id}: {exc}")
                    continue

                try:
                    result = fxn(*args, **kwargs)
                    status = "F"
                except Exception as exception:
                    traceback.print_exc()

                    logging.warning(
                        "Task failed with the error shown above. \n\n"
                        "If you are unfamilar with error tracebacks and find this error "
                        "difficult to read, you can learn more about these errors "
                        "here:\n https://realpython.com/python-traceback/\n\n"
                        "Please open a new issue on our github page if you believe "
                        "this is a bug:\n https://github.com/jacksund/simmate/issues/\n\n"
                    )

                    result = exception
                    status = "E"

                try:
                    result_pickled = cloudpickle.dumps(result)
                except Exception as exception:
                    result_pickled = cloudpickle.dumps(exception)
                    status = "E"

                result_b64 = base64.b64encode(result_pickled).decode("utf-8")

                # Send result back to API
                try:
                    update_response = self.session.post(
                        f"{self.server_url}/compute/work_items/{workitem_id}/update/",
                        json={
                            "status": status,
                            "result": result_b64,
                        },
                    )
                    update_response.raise_for_status()
                except requests.exceptions.RequestException as exc:
                    logging.error(
                        f"Failed to update WorkItem {workitem_id} result via API: {exc}"
                    )

                logging.info("Completed WorkItem")
                self.nitems_completed += 1

        except KeyboardInterrupt:
            logging.info("Stop signal recieved. Shutting down.")
