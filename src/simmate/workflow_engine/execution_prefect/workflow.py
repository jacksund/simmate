# -*- coding: utf-8 -*-

from functools import cache  # cached_property doesnt work with classmethod

from prefect.client import get_client
from prefect.context import FlowRunContext
from prefect.flows import Flow
from prefect.orion.schemas.filters import FlowFilter, FlowRunFilter
from prefect.packaging import OrionPackager
from prefect.packaging.serializers import PickleSerializer
from prefect.states import State
from prefect.tasks import task  # present only for convience imports elsewhere

from simmate.utilities import async_to_sync


class PrefectWorkflow:
    @classmethod
    def run(cls, **kwargs) -> State:
        """
        runs the workflow locally in a prefect context
        """

        subflow = cls._to_prefect_flow()
        state = subflow(return_state=True, **kwargs)

        # We don't want to block and wait because this might disable parallel
        # features of subflows. We therefore return the state and let the
        # user decide if/when to block.
        # result = state.result()

        return state

    @classmethod
    def run_cloud(cls, return_future: bool = True, **kwargs) -> str:
        """
        This schedules the workflow to run remotely on Prefect Cloud.

        #### Parameters

        - `labels`:
            a list of labels to schedule the workflow with

        - `wait_for_run`:
            whether to wait for the workflow to finish. If False, the workflow
            will simply be submitted and then exit. The default is True.

        - `**kwargs`:
            all options that are normally passed to the workflow.run() method

        #### Returns

        - The flow run id that was used in prefect cloud.


        #### Usage

        Make sure you have Prefect properly configured and have registered your
        workflow with the backend.

        Note that this method can be viewed as a fork of:
            - from prefect.tasks.prefect.flow_run import create_flow_run
        It can also be viewed as a more convenient way to call to client.create_flow_run.
        I don't accept any other client.create_flow_run() inputs besides 'labels'.
        This may change in the future if I need to set flow run names or schedules.
        """

        # Prefect does not properly deserialize objects that have
        # as as_dict or to_dict method, so we use a custom method to do that here
        parameters_serialized = cls._serialize_parameters(**kwargs)
        # BUG: What if we are submitting using a filename? We don't want to
        # submit to a cluster and have the job fail because it doesn't have
        # access to the file. One solution could be to deserialize right before
        # serializing in the next line in order to ensure parameters that
        # accept file names are submitted with all necessary data.

        # Now we submit the workflow.
        run_id = cls._submit_to_prefect(parameters=parameters_serialized)

        cls._register_calculation(run_id=run_id, **kwargs)
        # BUG: Will there be a race condition here? What if the workflow finishes
        # and tries writing to the databse before this is done?
        # BUG: if parameters are improperly set, this line will fail, while the
        # job submission (above) will suceed. Should I cancel the flow run if
        # this occurs?

        if return_future:
            raise Exception("Prefect cannot return futures from submisson.")

        # return the flow run_id for the user
        return run_id

    @classmethod
    @property
    def tags(cls) -> list[str]:
        """
        Lists of tags to submit a the workflow with when using run_cloud.
        """
        return [
            "simmate",
            cls.name_type,
            cls.name_calculator,
        ]

    @staticmethod
    def _get_run_id(raise_if_no_context: bool = True):
        """
        grabs the prefect flow run id from context (if there is one)
        """
        # Grab the flow run id for reference.
        run_context = FlowRunContext.get()
        if run_context:
            run_id = str(run_context.flow_run.id)
            return run_id
        elif not run_context and not raise_if_no_context:
            return None  # no error is raised
        else:
            raise Exception("Cannot detetect a Prefect FlowRunContext")

    @classmethod
    @cache
    def _to_prefect_flow(cls) -> Flow:
        """
        Converts this workflow into a Prefect flow
        """

        # Instead of the @flow decorator, we build the flow instance directly
        flow = Flow(
            fn=cls._run_full,
            name=cls.name_full,
            version=cls.version,
            # Skip type checking because I don't have robust typing yet
            # e.g. Structure type inputs also accept inputs like a filename
            validate_parameters=False,
        )

        # as an extra, we set this attribute to the prefect flow instance, which
        # allows us to access the source Simmate Workflow easily with Prefect's
        # context managers.
        flow.simmate_workflow = cls

        return flow

    @classmethod
    @property
    @cache
    @async_to_sync
    async def depolyment_id_prefect(cls) -> str:
        """
        Grabs the deployment id from the prefect database if it exists, and
        if not, creates the depolyment and then returns the id.

        This is a synchronous and cached version of `_get_depolyment_id_prefect` and
        this is the preferred method to use for beginners.
        """
        return await cls._get_depolyment_id_prefect()

    @classmethod
    async def _get_depolyment_id_prefect(cls) -> str:
        """
        Grabs the deployment id from the prefect database if it exists, and
        if not, creates the depolyment and then returns the id.

        This is an asynchronous method and should only be used when within
        other async methods. Beginners should instead use the `depolyment_id_prefect`
        property.
        """

        async with get_client() as client:
            response = await client.read_deployments(
                flow_filter=FlowFilter(
                    name={"any_": [cls.name_full]},
                ),
            )

        # If this is the first time accessing the deployment id, we will need
        # to create the deployment
        if not response:
            deployment_id = await cls._create_deployment_prefect()

        # there should only be one deployment associated with this workflow
        # if it's been deployed already.
        elif len(response) == 1:
            deployment_id = str(response[0].id)

        else:
            raise Exception("There are duplicate deployments for this workflow!")

        return deployment_id

    @classmethod
    async def _create_deployment_prefect(cls) -> str:
        """
        Registers this workflow to the prefect database as a deployment.

        This method should not be called directly. It will be called by
        other methods when appropriate
        """

        # raise error until python-deployments are supported again
        raise Exception(
            "Prefect 2.0 has removed the ability to create deployments in "
            "python, so this feature is currently disabled."
        )
        # When this is removed, be sure to re-add the test_workflow_cloud unittest

        from prefect.deployments import Deployment

        # NOTE: we do not use the client.create_deployment method because it
        # is called within the Deployment.create() method for us.
        deployment = Deployment(
            name=cls.name_full,
            flow=cls._to_prefect_flow(),
            packager=OrionPackager(serializer=PickleSerializer()),
            # OPTIMIZE: it would be better if I could figure out the ImportSerializer
            # here. Only issue is that prefect would need to know to import AND
            # call a method.
            tags=cls.tags,
        )

        deployment_id = await deployment.create()

        return str(deployment_id)  # convert from UUID to str first

    @classmethod
    @async_to_sync
    async def _submit_to_prefect(cls, **kwargs) -> str:
        """
        Submits a flow run to prefect cloud.

        This method should not be used directly. Instead use `_run_prefect_cloud`.
        """

        # The reason we have this code as a separate method is because we want
        # to isolate Prefect's async calls from Django's sync-restricted calls
        # (i.e. django raises errors if called within an async context).
        # Therefore, methods like `_run_prefect_cloud` can't have both this async code
        # AND methods like _register_calculation that make sync database calls.

        async with get_client() as client:
            response = await client.create_flow_run_from_deployment(
                deployment_id=await cls._get_depolyment_id_prefect(),
                **kwargs,
            )

        flow_run_id = str(response.id)
        return flow_run_id

    @classmethod
    @property
    @async_to_sync
    async def nflows_submitted(cls) -> int:
        """
        Queries Prefect to see how many workflows are in a scheduled, running,
        or pending state.
        """

        async with get_client() as client:
            response = await client.read_flow_runs(
                flow_filter=FlowFilter(
                    name={"any_": [cls.name_full]},
                ),
                flow_run_filter=FlowRunFilter(
                    state={"type": {"any_": ["SCHEDULED", "PENDING", "RUNNING"]}}
                ),
            )

        return len(response)
