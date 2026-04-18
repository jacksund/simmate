# -*- coding: utf-8 -*-


class FuzzyLogic(object):
    """
    A simple fuzzy-logic-style controller mapping input ranges to fixed output values.

    This controller uses a set of rules to determine the output based on the
    input value's range. It is useful for non-linear control logic where specific
    input ranges should trigger specific discrete outputs.
    """

    def __init__(
        self,
        rules: list[dict],
        auto_mode: bool = True,
        default_output: float = None,
    ):
        """
        Initialize a new FuzzyLogic controller.

        Args:
            rules: A list of dictionaries, where each dictionary defines a rule.
                Example rule: {"min": 0, "max": 10, "output": 1.0}.
                Both "min" and "max" are optional (defaulting to -inf and +inf).
            auto_mode: Whether the controller is enabled.
            default_output: The output value returned if no rules match.
        """
        self.rules = rules
        self.auto_mode = auto_mode
        self.default_output = default_output
        self._last_output = default_output

    def eval(self, input_: float) -> float:
        """
        Update the controller state and return the output based on matching rules.

        Args:
            input_: The current measurement of the system being controlled.

        Returns:
            The controller output based on the first matching rule, or
            default_output if no rules match.
        """
        if not self.auto_mode:
            return self._last_output

        for rule in self.rules:
            min_val = rule.get("min", float("-inf"))
            max_val = rule.get("max", float("inf"))

            if min_val <= input_ < max_val:
                self._last_output = rule["output"]
                return self._last_output

        self._last_output = self.default_output
        return self._last_output

    def __repr__(self):
        return (
            "{self.__class__.__name__}("
            "rules={self.rules!r}, auto_mode={self.auto_mode!r}, "
            "default_output={self.default_output!r}"
            ")"
        ).format(self=self)
