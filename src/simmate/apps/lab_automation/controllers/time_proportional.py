import time

from .base import Controller


class TimeProportional(Controller):
    """
    A time-proportional controller (PWM) based on a proportional band.

    This controller calculates a duty cycle based on the error between the
    setpoint and the input, scaled across a proportional band. It then modulates
    a digital output (On/Off) over a fixed cycle time to approximate a
    continuous output.
    """

    def __init__(
        self,
        setpoint: float = 0,
        proportional_band: float = 10.0,
        cycle_time: float = 1.0,
        on_output: float = 1.0,
        off_output: float = 0.0,
        auto_mode: bool = True,
    ):
        """
        Initialize a new TimeProportional controller.

        Args:
            setpoint: The target value the controller tries to maintain.
            proportional_band: The range over which the duty cycle is scaled
                from 0% to 100%. For heating, if error >= proportional_band,
                duty cycle is 100%. If error <= 0, duty cycle is 0%.
            cycle_time: The duration (in seconds) of one full PWM cycle.
            on_output: The output value during the 'On' portion of the cycle.
            off_output: The output value during the 'Off' portion of the cycle.
            auto_mode: Whether the controller is enabled.
        """
        self.setpoint = setpoint
        self.proportional_band = proportional_band
        self.cycle_time = cycle_time
        self.on_output = on_output
        self.off_output = off_output
        self.auto_mode = auto_mode
        self._last_output = off_output

        self._cycle_start_time = time.monotonic()

    def eval(self, input_: float, dt: float = None) -> float:
        """
        Update the controller state and return the output based on PWM.

        Args:
            input_: The current measurement of the system being controlled.
            dt: The time step since the last update. Optional.

        Returns:
            The controller output (either on_output or off_output).
        """
        if not self.auto_mode:
            return self._last_output

        error = self.setpoint - input_

        # Calculate duty cycle (0.0 to 1.0)
        # Assuming heating mode: positive error (input < setpoint) increases duty
        if error <= 0:
            duty_cycle = 0.0
        elif error >= self.proportional_band:
            duty_cycle = 1.0
        else:
            duty_cycle = error / self.proportional_band

        now = time.monotonic()
        elapsed_in_cycle = now - self._cycle_start_time

        if elapsed_in_cycle >= self.cycle_time:
            self._cycle_start_time = now
            elapsed_in_cycle = 0.0

        on_time = duty_cycle * self.cycle_time

        if elapsed_in_cycle < on_time:
            self._last_output = self.on_output
        else:
            self._last_output = self.off_output

        return self._last_output

    def __repr__(self):
        return (
            "{self.__class__.__name__}("
            "setpoint={self.setpoint!r}, proportional_band={self.proportional_band!r}, "
            "cycle_time={self.cycle_time!r}, on_output={self.on_output!r}, "
            "off_output={self.off_output!r}, auto_mode={self.auto_mode!r}"
            ")"
        ).format(self=self)
