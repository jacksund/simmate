import logging
import time

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
        stirrer_pins=(23, 24),
        heater_pin=16,
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
            proportional_band=20,
            cycle_time=4,
        )

    def set_stir_speed(self, speed: float):
        """
        Sets the stirrer speed.

        Args:
            speed: A value between -1.0 and 1.0. Positive values spin forward,
                negative values spin backward. 0 stops the stirrer.
        """
        logging.info(f"Setting stirrer speed to {speed}")
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
        logging.info(f"Setting target temperature to {temperature}°C")
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

        if output > 0 and not self.heater.is_active:
            logging.info("Heater turned ON")
            self.heater.on()
        elif output <= 0 and self.heater.is_active:
            logging.info("Heater turned OFF")
            self.heater.off()

        return current_temp

    def stop(self):
        """
        Stops both the stirrer and the heater immediately.
        """
        logging.info("Stopping stirrer and heater")
        self.stirrer.stop()
        self.heater.off()

    def run(
        self,
        temperature: float,
        stir_speed: float,
        total_time: float = None,
        update_interval: float = 0.25,
    ):
        """
        Runs the hot plate at the specified temperature and stir speed for
        a set amount of time.

        Args:
            temperature: The target temperature in Celsius.
            stir_speed: The stirrer speed (between -1.0 and 1.0).
            total_time: The total time (in seconds) to run. If None, it
                runs indefinitely until interrupted.
            update_interval: The time (in seconds) between each update of
                the control loop.
        """
        logging.info(
            f"Starting run: target={temperature}°C, stir_speed={stir_speed}, "
            f"duration={total_time if total_time else 'indefinite'}s"
        )
        self.set_temperature(temperature)
        self.set_stir_speed(stir_speed)

        start_time = time.monotonic()
        last_log_time = 0
        try:
            while True:
                current_time = time.monotonic()
                elapsed_time = current_time - start_time
                if total_time and elapsed_time > total_time:
                    logging.info("Total run time reached.")
                    break

                temp = self.update()

                # Log status every 10 seconds (or at every update if interval > 10)
                if current_time - last_log_time >= 10:
                    status_msg = f"Status: {temp:.2f}°C"
                    if total_time:
                        status_msg += f" ({elapsed_time:.1f}/{total_time}s)"
                    logging.info(status_msg)
                    last_log_time = current_time

                time.sleep(update_interval)
        except KeyboardInterrupt:
            logging.warning("Run interrupted by user.")
        finally:
            self.stop()
            logging.info("Run finished.")
