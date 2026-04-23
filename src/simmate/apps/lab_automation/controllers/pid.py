import time

from .base import Controller


class PID(Controller):
    """
    A simple Proportional-Integral-Derivative (PID) controller.

    This controller calculates a control output based on the error between a
    setpoint and a measured input. It is suitable for a wide range of continuous
    control applications.

    This implementation is a fork of the `simple_pid` library:
    https://github.com/m-lundberg/simple-pid/tree/master
    """

    def __init__(
        self,
        Kp: float = 1.0,
        Ki: float = 0.0,
        Kd: float = 0.0,
        setpoint: float = 0,
        sample_time: float = 0.01,
        output_limits: tuple[float | None, float | None] = (None, None),
        auto_mode: bool = True,
        proportional_on_measurement: bool = False,
        differential_on_measurement: bool = True,
        error_map: callable = None,
        starting_output: float = 0.0,
    ):
        """
        Initialize a new PID controller.

        Args:
            Kp: The proportional gain.
            Ki: The integral gain.
            Kd: The derivative gain.
            setpoint: The target value the PID tries to achieve.
            sample_time: The time (in seconds) to wait before generating a new
                output. If set to None, the PID computes a new value every time
                it is called.
            output_limits: The lower and upper limits for the output. Prevents
                the output from exceeding these bounds and avoids integral
                windup.
            auto_mode: Whether the controller is enabled.
            proportional_on_measurement: Whether to calculate the proportional
                term directly on the input rather than the error.
            differential_on_measurement: Whether to calculate the differential
                term directly on the input rather than the error.
            error_map: An optional function to transform the error value.
            starting_output: The initial output value when the controller starts.
        """
        self.Kp, self.Ki, self.Kd = Kp, Ki, Kd
        self.setpoint = setpoint
        self.sample_time = sample_time

        self._min_output, self._max_output = None, None
        self._auto_mode = auto_mode
        self.proportional_on_measurement = proportional_on_measurement
        self.differential_on_measurement = differential_on_measurement
        self.error_map = error_map

        self._proportional = 0
        self._integral = 0
        self._derivative = 0

        self._last_time = None
        self._last_output = None
        self._last_error = None
        self._last_input = None

        self.output_limits = output_limits
        self.reset()

        # Set initial state of the controller
        self._integral = self._clamp(starting_output, output_limits)

    def eval(self, input_: float, dt: float = None) -> float:
        """
        Calculate and return the control output based on the current input.

        If `sample_time` has not elapsed, the last calculated output is
        returned.

        Args:
            input_: The current measurement of the system.
            dt: An optional time step to use for calculations. If None, the
                real elapsed time since the last update is used.

        Returns:
            The calculated control output.
        """
        if not self.auto_mode:
            return self._last_output

        now = time.monotonic()
        if dt is None:
            dt = now - self._last_time if (now - self._last_time) else 1e-16
        elif dt <= 0:
            raise ValueError("dt has negative value {}, must be positive".format(dt))

        if (
            self.sample_time is not None
            and dt < self.sample_time
            and self._last_output is not None
        ):
            # Only update every sample_time seconds
            return self._last_output

        # Compute error terms
        error = self.setpoint - input_
        d_input = input_ - (
            self._last_input if (self._last_input is not None) else input_
        )
        d_error = error - (
            self._last_error if (self._last_error is not None) else error
        )

        # Check if must map the error
        if self.error_map is not None:
            error = self.error_map(error)

        # Compute the proportional term
        if not self.proportional_on_measurement:
            # Regular proportional-on-error, simply set the proportional term
            self._proportional = self.Kp * error
        else:
            # Add the proportional error on measurement to error_sum
            self._proportional -= self.Kp * d_input

        # Compute integral and derivative terms
        self._integral += self.Ki * error * dt
        self._integral = self._clamp(
            self._integral, self.output_limits
        )  # Avoid integral windup

        if self.differential_on_measurement:
            self._derivative = -self.Kd * d_input / dt
        else:
            self._derivative = self.Kd * d_error / dt

        # Compute final output
        output = self._proportional + self._integral + self._derivative
        output = self._clamp(output, self.output_limits)

        # Keep track of state
        self._last_output = output
        self._last_input = input_
        self._last_error = error
        self._last_time = now

        return output

    def __repr__(self):
        return (
            "{self.__class__.__name__}("
            "Kp={self.Kp!r}, Ki={self.Ki!r}, Kd={self.Kd!r}, "
            "setpoint={self.setpoint!r}, sample_time={self.sample_time!r}, "
            "output_limits={self.output_limits!r}, auto_mode={self.auto_mode!r}, "
            "proportional_on_measurement={self.proportional_on_measurement!r}, "
            "differential_on_measurement={self.differential_on_measurement!r}, "
            "error_map={self.error_map!r}"
            ")"
        ).format(self=self)

    @property
    def components(self):
        """
        The P-, I-, and D-terms from the last computation as a tuple.
        """
        return self._proportional, self._integral, self._derivative

    @property
    def tunings(self):
        """
        The tunings used by the controller as a tuple (Kp, Ki, Kd).
        """
        return self.Kp, self.Ki, self.Kd

    @tunings.setter
    def tunings(self, tunings):
        """
        Sets the PID tunings.
        """
        self.Kp, self.Ki, self.Kd = tunings

    @property
    def auto_mode(self):
        """
        Whether the controller is currently enabled.
        """
        return self._auto_mode

    @auto_mode.setter
    def auto_mode(self, enabled: bool):
        """
        Enable or disable the PID controller.
        """
        self.set_auto_mode(enabled)

    def set_auto_mode(self, enabled: bool, last_output: float = None):
        """
        Enable or disable the PID controller.

        When switching from manual to auto mode, the integral term can be
        initialized to a specific value to ensure a smooth transition.

        Args:
            enabled: Whether to enable auto mode.
            last_output: The initial output value to use for the integral term
                when starting auto mode.
        """
        if enabled and not self._auto_mode:
            # Switching from manual mode to auto, reset
            self.reset()

            self._integral = last_output if (last_output is not None) else 0
            self._integral = self._clamp(self._integral, self.output_limits)

        self._auto_mode = enabled

    @property
    def output_limits(self):
        """
        The current output limits as a tuple (lower, upper).
        """
        return self._min_output, self._max_output

    @output_limits.setter
    def output_limits(self, limits: tuple[float | None, float | None]):
        """
        Sets the output limits.
        """
        if limits is None:
            self._min_output, self._max_output = None, None
            return

        min_output, max_output = limits

        if (None not in limits) and (max_output < min_output):
            raise ValueError("lower limit must be less than upper limit")

        self._min_output = min_output
        self._max_output = max_output

        self._integral = self._clamp(self._integral, self.output_limits)
        self._last_output = self._clamp(self._last_output, self.output_limits)

    def reset(self):
        """
        Reset the PID controller's internal state.
        """
        self._proportional = 0
        self._integral = 0
        self._derivative = 0

        self._integral = self._clamp(self._integral, self.output_limits)

        self._last_time = time.monotonic()
        self._last_output = None
        self._last_input = None
        self._last_error = None

    @staticmethod
    def _clamp(value, limits):
        lower, upper = limits
        if value is None:
            return None
        elif (upper is not None) and (value > upper):
            return upper
        elif (lower is not None) and (value < lower):
            return lower
        return value
