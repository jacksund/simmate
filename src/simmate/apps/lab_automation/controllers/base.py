from abc import ABC, abstractmethod


class Controller(ABC):
    """
    Base class for all control algorithms in the lab_automation app.

    This class defines the standard interface for controllers, ensuring they
    all implement the `eval` method for processing sensor data.
    """

    @abstractmethod
    def eval(self, input_: float, dt: float = None) -> float:
        """
        Processes the input measurement and returns the control output.

        Args:
            input_: The current measurement from the sensor.
            dt: The time step since the last update. Optional, as some
                controllers (like PID) use it for integration/differentiation,
                while others (like On/Off) may ignore it.

        Returns:
            The calculated control output.
        """
        raise NotImplementedError
