from gpiozero import DigitalOutputDevice, Motor

from simmate.apps.lab_automation.controllers import Controller, TimeProportional
from simmate.apps.lab_automation.sensors.temperature import DS18B20


class StirringHotPlate:
    """
    A unified interface for a stirring hot plate equipped with a magnetic
    spinner, a heating element controlled via an SSR, and a DS18B20
    temperature probe.

    This class combines a `Motor` for stirring, a `DigitalOutputDevice` for
    heating (via SSR), and a `DS18B20` sensor for closed-loop temperature
    control using a `Controller` (defaulting to `TimeProportional`).

    Example:
    ```python
    from simmate.apps.lab_automation.devices import StirringHotPlate

    # Initialize with GPIO pins
    plate = StirringHotPlate(
        stirrer_pins=(17, 27),
        heater_pin=22,
    )

    # Set targets
    plate.set_stir_speed(0.5)
    plate.set_temperature(50.0)

    # Run control loop
    try:
        while True:
            temp = plate.update()
            print(f"Current Temp: {temp}°C")
    finally:
        plate.stop()
    ```
    """

    def __init__(
        self,
        stirrer_pins: tuple[int, int],
        heater_pin: int,
        temp_sensor_id: str = None,
        temp_controller: Controller = None,
    ):
        """
        Initialize the stirring hot plate.

        Args:
            stirrer_pins: A tuple of (forward_pin, backward_pin) for the motor.
            heater_pin: The GPIO pin controlling the SSR for the heater.
            temp_sensor_id: The unique ID of the DS18B20 sensor. If None,
                it auto-finds the first available sensor.
            temp_controller: The controller to use for the heater. If None,
                it defaults to a TimeProportional controller.
        """
        self.stirrer = Motor(*stirrer_pins)
        self.heater = DigitalOutputDevice(heater_pin)
        self.temp_sensor = DS18B20(temp_sensor_id)

        # Use TimeProportional for the heater since it's an SSR.
        # Default proportional band and cycle time are reasonable for small
        # lab heaters, but may need tuning.
        self.temp_controller = temp_controller or TimeProportional(
            setpoint=0,
            proportional_band=10.0,
            cycle_time=2.0,
        )

    def set_stir_speed(self, speed: float):
        """
        Sets the stirrer speed.

        Args:
            speed: A value between -1.0 and 1.0. Positive values spin forward,
                negative values spin backward. 0 stops the stirrer.
        """
        if speed == 0:
            self.stirrer.stop()
        elif speed > 0:
            self.stirrer.forward(speed)
        else:
            self.stirrer.backward(abs(speed))

    def set_temperature(self, temperature: float):
        """
        Sets the target temperature for the hot plate.

        Args:
            temperature: The target temperature in Celsius.
        """
        self.temp_controller.setpoint = temperature

    def update(self) -> float:
        """
        Updates the heater state based on the current temperature.
        This should be called frequently in a loop to maintain stable
        temperature control.

        Returns:
            The current temperature in Celsius.
        """
        current_temp, _ = self.temp_sensor.get_temperature()
        output = self.temp_controller.eval(current_temp)

        if output > 0:
            self.heater.on()
        else:
            self.heater.off()

        return current_temp

    def stop(self):
        """
        Stops both the stirrer and the heater immediately.
        """
        self.stirrer.stop()
        self.heater.off()
