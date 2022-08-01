# -*- coding: utf-8 -*-

import anyio
import time
import uuid
from functools import cached_property

from prefect.client import get_client
from prefect.exceptions import PrefectHTTPStatusError
from prefect.agent import OrionAgent
from prefect.settings import PREFECT_AGENT_QUERY_INTERVAL
from prefect.orion.schemas.filters import FlowRunFilter  # FlowFilter,

from simmate.utilities import async_to_sync

# This string is just something fancy to display in the console when a worker
# starts up.
# This uses "Small Slant" from https://patorjk.com/software/taag/
HEADER_ART = r"""
   _____                  __        _      __         __
  / __(_)_ _  __ _  ___ _/ /____   | | /| / /__  ____/ /_____ ____
 _\ \/ /  ' \/  ' \/ _ `/ __/ -_)  | |/ |/ / _ \/ __/  '_/ -_) __/
/___/_/_/_/_/_/_/_/\_,_/\__/\__/   |__/|__/\___/_/ /_/\_\\__/_/

"""


class Worker:
    """
    A worker is a process that checks the Prefect database for scheduled workflow
    runs and then submits them.

    Workers are only required when you are using a workflow's `run_cloud` method.

    This is effectively a combination of a Prefect Agent and Queue, where we
    configure default values for a queue and automatically perform the setup.
    """

    def __init__(
        self,
        queue_name: str = None,
        concurrency_limit: int = 1,
        nflows_max: int = None,
        timeout: float = None,
        close_on_empty_queue: bool = False,
    ):
        # This will be used when creating the queue
        self.concurrency_limit = concurrency_limit

        # if no name was given, we generate a random one
        if not queue_name:
            # generate a unique name for the worker, where we use uuid and take
            # the first 8 values (the rest is overkill for this application)
            unique_id = str(uuid.uuid4())[:8]
            queue_name = f"simmate-worker-{unique_id}"

        self.queue_name = queue_name

        # Grab the worker queue.
        # This is a cached property, so simply calling it and asserting that
        # it exists is sufficient to set everything up.
        assert self.queue_id

        # the maximum number of workitems to run before closing down
        # if no limit was set, we can go to infinity!
        self.nflows_max = nflows_max or float("inf")

        # Don't start a new workitem after this time. The worker will be shut down.
        # if no timeout was set, use infinity so we wait forever.
        self.timeout = timeout or float("inf")

        # whether to close if the queue is empty
        self.close_on_empty_queue = close_on_empty_queue

    @async_to_sync
    async def run(self):
        """
        Starts the worker and begins running scheduled workflows.
        """

        # !!! This method is really a fork of Prefect's `prefect agent start`
        # command, so a lot of this could be move to a prefect contribution.
        # https://github.com/PrefectHQ/prefect/blob/orion/src/prefect/cli/agent.py

        # print the header in the console to let the user know the worker started
        print(HEADER_ART)

        # establish starting point for the worker
        time_start = time.time()
        nflows_submitted = 0

        async with OrionAgent(work_queue_name=self.queue_name) as agent:

            print(f"Worker started! Looking for work from queue '{self.queue_name}'...")

            # Loop endlessly until one of the following happens...
            #   the timeout limit is hit
            #   the queue is empty
            #   the nitems limit is hit
            #   the user stops the process with ctrl+C  # BUG
            while True:

                # check for timeout before starting a new workitem and exit
                # if we've hit the limit.
                if (time.time() - time_start) > self.timeout:
                    print("The time-limit reached. Shutting down worker.")
                    break

                # check the number of jobs completed so far, and exit if we hit
                # the limit
                if nflows_submitted >= self.nflows_max:
                    print("Maxium number of workflow runs hit. Shutting down worker.")
                    break

                # Run and submit flows
                flows_new = await agent.get_and_submit_flow_runs()
                nflows_new = len(flows_new)

                # Keep track of the new runs we submit
                if nflows_new:
                    nflows_submitted += nflows_new
                    print(f"Found and submitted {nflows_new} new workflow runs.")

                # If our last query gave zero workflows submitted, then there's
                # a chance our queue is empty and we should shut down.
                # check the length of the queue and while it is empty, we want to
                # loop. The exception of looping endlessly is if we want the worker
                # to shutdown instead.
                # This is a special condition where we may want to close the
                # worker if the queue stays empty
                if nflows_new == 0 and self.close_on_empty_queue:
                    remaining = await self._get_remaining_runs()
                    if remaining == 0:
                        print("The queue is empty. Shutting down worker.")
                        break

                # Sleep until the next check
                await anyio.sleep(PREFECT_AGENT_QUERY_INTERVAL.value())
                # BUG: using anyio.sleep doesn't shut down the worker properly
                # and it just ignores the ctrl+c command.
                # This line works but doesn't stream logs while sleeping:
                # time.sleep(PREFECT_AGENT_QUERY_INTERVAL.value())
                # Therefore this code is not used:
                # try:
                #   << all code in the while loop >>
                # except KeyboardInterrupt:
                #     print(
                #         "Recieved keyboard signal to stop. Shutting down worker."
                #     )
                #     break

        # Delete the queue now that we are done with it
        print("Deleting queue and cleaning up...")
        await self._delete_queue()
        print("Successfully closed worker.")

    @cached_property
    @async_to_sync
    async def queue_id(self) -> str:
        """
        Grabs the queue id from the prefect database if it exists, and
        if not, creates the queue and then returns the id.

        This is a synchronous and cached version of `_get_queue_id` and
        this is the preferred method to use for beginners.
        """
        return await self._get_queue_id()

    async def _get_queue_id(self) -> str:
        """
        Grabs the queue id from the prefect database if it exists, and
        if not, creates the queue and then returns the id.

        This is an asynchronous method and should only be used when within
        other async methods. Beginners should instead use the `queue_id`
        property.
        """

        try:
            async with get_client() as client:
                response = await client.read_work_queue_by_name(
                    name=self.queue_name,
                )

            # There should only be one queue for each name, so this is returned
            # as a single value
            queue_id = str(response.id)

        # A 404 error will be raised when the queue doesn't exist
        except PrefectHTTPStatusError:
            # If this is the first time accessing the deployment id, we will need
            # to create the queue_id
            queue_id = await self._create_queue()

        return queue_id

    async def _create_queue(self) -> str:
        """
        Registers this queue to the prefect database.

        This method should not be called directly. It will be called by
        other methods when appropriate
        """

        async with get_client() as client:
            response = await client.create_work_queue(
                name=self.queue_name,
                tags=["simmate"],
            )

            # create_work_queue does not accept an input for concurrency, so
            # I need to update this in a 2nd call to the api
            await client.update_work_queue(
                id=str(response),
                concurrency_limit=self.concurrency_limit,
            )

        queue_id = str(response)

        return queue_id

    @staticmethod
    async def _get_remaining_runs() -> int:
        """
        Returns a count of the number of remaining workflow runs.

        This is used to determine when workers should shut down within the `run`
        method, and this method should not be called by users.
        """

        # get_runs_in_work_queue cant look past the concurrency limit
        # so we have to query for the allowed flow runs directly

        async with get_client() as client:
            response = await client.read_flow_runs(
                # BUG: Why won't this work...?
                # flow_filter=FlowFilter(
                #     tags={"all_": ["simmate"]},
                # ),
                flow_run_filter=FlowRunFilter(
                    state={"type": {"any_": ["SCHEDULED", "PENDING"]}}
                ),
            )
        return len(response)

    async def _delete_queue(self):
        """
        Deletes the work queue associated with this worker.

        This method is called automatically at the end of `run` and
        should not be called by users.
        """

        queue_id = await self._get_queue_id()

        async with get_client() as client:
            response = await client.delete_work_queue_by_id(
                id=queue_id,
            )
