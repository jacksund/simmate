# -*- coding: utf-8 -*-

import requests

from simmate.engine import Workflow


class WebApiWorkflow(Workflow):
    """
    The base Web API workflow that many other workflows inherit from. This class
    encapulates logic for calling external APIs (e.g. a REST API) and handling
    common functionality and errors (e.g. chunking the cal, connection errors, etc.).

    Most commonly, this class is used for Deployed AI/ML models that are hosted
    as microservices elsewhere.
    """

    use_database = False
    _parameter_methods = Workflow._parameter_methods + ["_get_payload"]

    api_url: str = None
    """
    The full REST API endpoint that should be called for this method
    """

    repo_url: str = None
    """
    Because Web APIs are often hosted as a microservice elsewhere, their code
    is hosted elsewhere as well. This points to the Web API's source code.
    """

    maintainer: str = None
    """
    The current maintainer of this API endpoint and service.
    """

    chunk_input: str = None  # e.g. "molecules"
    chunk_size: int = None  # e.g. 10000

    timeout: float = None  # per chunk

    @classmethod
    def run_config(cls, **kwargs):
        if not cls.api_url:
            raise Exception(
                "'DeployedModel' workflows require the 'api_url' attribute to be set"
            )

        # TODO: add in chunking functionality for call api's with massive
        # datasets (e.g. >1mil molecules)

        response = requests.post(
            cls.api_url,
            json=cls._get_payload(**kwargs),
            timeout=cls.timeout,
        )
        response_data = response.json()
        return cls._reformat_response(response_data)

    @staticmethod
    def _get_payload(**kwargs) -> dict:
        # by default, we just pass all input parameters as dictionary. In the
        # large majority of cases, this method should be modified though.
        return kwargs

    @staticmethod
    def _reformat_response(response: dict) -> dict:
        # by default, we don't modify the returned data. But if the model returns
        # data in an undesirable
        return response
