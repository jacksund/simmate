# -*- coding: utf-8 -*-


from .base import Controller


class OnOff(Controller):
    """
    A simple on-off (bang-bang) controller with deadband.

    This controller provides basic two-state control (e.g., On/Off, High/Low).
    It includes a deadband (hysteresis) to prevent rapid cycling when the
    input is near the setpoint.
    """

    def __init__(
        self,
        setpoint: float = 0,
        deadband: float = 0.0,
        on_output: float = 1.0,
        off_output: float = 0.0,
        auto_mode: bool = True,
    ):
        """
        Initialize a new OnOff controller.

        Args:
            setpoint: The target value the controller tries to maintain.
            deadband: The range around the setpoint where no state change occurs.
                The controller switches to 'on' when error > deadband/2 and
                to 'off' when error < -deadband/2.
            on_output: The output value when the controller is in the 'on' state.
            off_output: The output value when the controller is in the 'off' state.
            auto_mode: Whether the controller is enabled.
        """
        self.setpoint = setpoint
        self.deadband = deadband
        self.on_output = on_output
        self.off_output = off_output
        self.auto_mode = auto_mode
        self._last_output = off_output

    def eval(self, input_: float, dt: float = None) -> float:
        """
        Update the controller state and return the output.

        Args:
            input_: The current measurement of the system being controlled.

        Returns:
            The controller output (either on_output or off_output).
        """
        if not self.auto_mode:
            return self._last_output

        error = self.setpoint - input_

        if error > self.deadband / 2:
            self._last_output = self.on_output
        elif error < -self.deadband / 2:
            self._last_output = self.off_output

        return self._last_output

    def __repr__(self):
        return (
            "{self.__class__.__name__}("
            "setpoint={self.setpoint!r}, deadband={self.deadband!r}, "
            "on_output={self.on_output!r}, off_output={self.off_output!r}, "
            "auto_mode={self.auto_mode!r}"
            ")"
        ).format(self=self)
