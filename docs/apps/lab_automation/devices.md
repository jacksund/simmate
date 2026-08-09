# Devices

Devices are high-level objects that combine sensors, actuators, and controllers
into a unified interface. They are designed to simplify the control of complex
laboratory equipment.

## Stirring Hot Plate

The `StirringHotPlate` class provides a single interface for managing a
hot plate with a magnetic stirrer and a temperature probe. It uses a
`TimeProportional` controller to manage the heater SSR based on the
temperature probe readings.

### Example Usage

```python
from simmate.apps.lab_automation.devices import StirringHotPlate

# Initialize the hot plate with GPIO pins
# stirrer_pins: (forward, backward)
# heater_pin: SSR control pin
plate = StirringHotPlate(
    stirrer_pins=(17, 27),
    heater_pin=22,
)

# Set the target stirrer speed (0.0 to 1.0)
plate.set_stir_speed(0.5)

# Set the target temperature in Celsius
plate.set_temperature(60.0)

# Run the control loop to maintain temperature
try:
    while True:
        current_temp = plate.update()
        print(f"Temperature: {current_temp:.1f} °C")
except KeyboardInterrupt:
    print("Stopping...")
finally:
    # Always stop the device when finished
    plate.stop()
```
