import glob
import logging
import time
from datetime import datetime
from pathlib import Path


class DS18B20:
    """
    Utility for interfacing with a DS18B20 temperature sensor probe.

    This class supports "lazy" connections: you can call `get_temperature`
    directly, and it will handle opening/closing the device file automatically.
    This is ideal for long-interval logging (>60s) or multi-sensor setups.

    Example usage (Single Sensor):
    ```python
    from simmate.apps.lab_automation.sensors import DS18B20

    # Simple reading (auto-finds first sensor and handles file I/O)
    sensor = DS18B20()
    temp_c, temp_f = sensor.get_temperature()
    ```

    Example usage (Multi-Sensor Logging):
    ```python
    sensors = DS18B20.get_all_sensors()
    for i in range(10):
        for sensor in sensors:
            temp_c, _ = sensor.get_temperature()
            print(f"Sensor {sensor.device_id}: {temp_c} C")
        time.sleep(60)
    ```

    Example usage (Explicit Context):
    ```python
    # Use as a context manager if you want to keep the file handle open
    with DS18B20() as sensor:
        for i in range(10):
            temp_c, _ = sensor.get_temperature()
            print(temp_c)
            time.sleep(0.1)
    ```
    """

    BASE_DIR = Path("/sys/bus/w1/devices/")

    def __init__(self, device_id: str = None):
        if device_id:
            self.device_id = device_id
        else:
            # Auto-find the first 1-wire device starting with "28", specific to DS18B20
            devices = glob.glob(str(self.BASE_DIR / "28*"))
            if not devices:
                raise RuntimeError("No DS18B20 sensors found.")
            # Use the directory name as the device ID
            self.device_id = Path(devices[0]).name

        self.device_file = self.BASE_DIR / self.device_id / "w1_slave"
        self._file_handle = None

    def __repr__(self):
        return f"DS18B20(device_id='{self.device_id}')"

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()

    def open(self):
        """Opens the device file connection if not already open."""
        if self._file_handle:
            return

        if not self.device_file.exists():
            raise RuntimeError(f"Could not find device file at {self.device_file}")

        self._file_handle = open(self.device_file, "r")

    def close(self):
        """Closes the device file connection."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

    def get_temperature(self, wait_for_valid: bool = True):
        """
        Reads and parses the raw temperature data, converting it to Celsius
        and Fahrenheit. If the device file is closed, it will briefly open
        it to take the reading and then close it again.
        """
        # Track if we need to close the file after this capture
        was_closed = self._file_handle is None
        if was_closed:
            self.open()

        try:
            # Reads raw temperature data from the sensor
            self._file_handle.seek(0)
            lines = self._file_handle.readlines()

            # In some cases, we need to wait for a valid temperature reading
            while wait_for_valid and (not lines or lines[0].strip()[-3:] != "YES"):
                time.sleep(0.2)
                self._file_handle.seek(0)
                lines = self._file_handle.readlines()

            if not lines or len(lines) < 2:
                raise RuntimeError(f"Failed to read temperature from {self.device_id}")

            equals_pos = lines[1].find("t=")
            if equals_pos != -1:
                temp_string = lines[1][equals_pos + 2 :]
                temp_c = float(temp_string) / 1000.0  # Convert to Celsius
                temp_f = temp_c * 9.0 / 5.0 + 32.0  # Convert to Fahrenheit
                return temp_c, temp_f
            else:
                raise RuntimeError(
                    f"Could not parse temperature data from {self.device_id}"
                )

        finally:
            if was_closed:
                self.close()

    def start_logging(
        self,
        output_file: str | Path = "temperature_log.csv",
        interval: int = 60,
        total_readings: int = None,
        total_hours: float = None,
    ):
        """
        Logs temperature at regular intervals to a CSV file. If the sensor is
        not already opened via a context manager, it will open/close for
        every reading.
        """
        if total_readings is None:
            if total_hours is None:
                raise ValueError("Provide either total_readings or total_hours")
            total_readings = int((total_hours * 3600) // interval)

        output_path = Path(output_file)

        # Write header if file is new
        if not output_path.exists():
            with open(output_path, "w") as f:
                f.write("timestamp,temp_c,temp_f\n")

        logging.info(
            f"Starting temperature log for {self.device_id}: {total_readings} readings"
        )

        for i in range(total_readings):
            try:
                temp_c, temp_f = self.get_temperature()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(output_path, "a") as f:
                    f.write(f"{timestamp},{temp_c:.2f},{temp_f:.2f}\n")
                logging.info(f"Logged {self.device_id}: {temp_c:.2f}°C")
            except Exception as e:
                logging.error(
                    f"Logging failed for {self.device_id} at reading {i}: {e}"
                )

            if i < total_readings - 1:
                time.sleep(interval)

    @classmethod
    def get_all_sensors(cls):
        """
        Finds all DS18B20 sensors connected to the system by looking for
        directories starting with '28-' in the base 1-wire directory.
        """
        devices = glob.glob(str(cls.BASE_DIR / "28*"))
        return [cls(device_id=Path(d).name) for d in devices]
