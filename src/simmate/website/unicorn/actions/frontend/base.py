import logging
from abc import ABC, abstractmethod

from simmate.website.unicorn.serializer import dumps, loads

logger = logging.getLogger(__name__)


class FrontendAction(ABC):
    """
    Any action or update to be performed on the frontend via client-side
    javascript. Specifically, this defines the json response needed to call
    actions on the fronted.

    Objects of this class and its methods are typically generated by
    FrontendActions and then used to build a ComponentResponse. This whole
    process is managed by a ComponentRequest.
    """

    method_name: str = None
    """
    Name of the Component method that provided this FrontendAction
    """

    method_args: list[str] = None
    """
    List of args that were used in creating this FrontendAction
    """

    method_kwargs: list[str] = None
    """
    List of kwargs that were used in creating this FrontendAction
    """

    @property
    def is_metadata_set(self) -> bool:
        if None in (self.method_name, self.method_args, self.method_kwargs):
            return False
        else:
            return True

    def set_metadata(self, method_name, args: list = None, kwargs: dict = None):
        """
        The frontend often needs to know where this FrontendAction came from.
        This is method is often used in
        """
        self.method_name = method_name
        self.method_args = args if args is not None else []
        self.method_kwargs = kwargs if kwargs is not None else {}

    @abstractmethod
    def get_payload_value(self) -> any:
        """
        Sets what should be returned with the 'value' key in the final dict

        This can be treated as an abstractmethod and overwritten in subclasses.
        By default the __dict__ of the class will be returned
        """
        return self.value

    def to_dict(self) -> dict:
        """
        Converts this action to dictionary for the frontend to use.
        All values in the {key: value} output must be json-serialized or as
        basic python types (str, int, float, boolean).
        """
        # bug-check
        assert self.is_metadata_set

        try:

            value = self.get_payload_value()

            # json-serialize
            serialized_value = loads(dumps(value))
            serialized_args = loads(dumps(self.method_args))
            serialized_kwargs = loads(dumps(self.method_kwargs))

            return {
                "method": self.method_name,
                "args": serialized_args,
                "kwargs": serialized_kwargs,
                "value": serialized_value,
            }

        except Exception as e:
            # !!! Why do we fail silently here? - @jacksund
            logger.exception(e)

        return {}

    def get_response_data(self):
        """
        Builds on top of to_dict to format the ComponentResponse. This is needed
        because sometimes the response data for this frontend action is needed
        in multiple places (see PollUpdate as an example).

        By default it only updates the "return" value
        """
        return {"return": self.to_dict()}