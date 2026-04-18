# Controllers Overview

Controllers are algorithms that help maintain a system at a desired setpoint by
processing sensor feedback and calculating the necessary actuator output.

## Common Control Applications

The table below provides examples of typical control systems in a laboratory
setting and the recommended controller type for each.

| Application | Sensor (Feedback) | Actuator (Output) | Typical Controller |
| :--- | :--- | :--- | :--- |
| Pressure | Transducer | Control Valve / Compressor | PID (Fast) |
| Motion | Encoder / Hall Effect | Stepper or Servo Motor | PID (High Precision) |
| Flow | Flow Meter | Pump Speed / Valve | PID or Feedforward |
| Level | Ultrasonic / Float | Intake Valve | On-Off or PID |
| pH | pH Probe | Peristaltic Pump | Fuzzy Logic |

---

## Available Controllers

Simmate provides several built-in controllers in the `simmate.apps.lab_automation.controllers` module.

### PID Controller

The Proportional-Integral-Derivative (PID) controller is the industry standard for
precise control of continuous systems.

```python
from simmate.apps.lab_automation.controllers import PID

controller = PID(Kp=1.0, Ki=0.1, Kd=0.05, setpoint=25.0)
output = controller.eval(current_temperature)
```

### On-Off (Bang-Bang) Controller

A simple controller that switches between two states. It is ideal for systems
where high precision is not required and simple hysteresis (deadband) is sufficient.

```python
from simmate.apps.lab_automation.controllers import OnOff

controller = OnOff(setpoint=25.0, deadband=1.0)
output = controller.eval(current_temperature)
```

### Time-Proportional (PWM) Controller

Useful for controlling digital actuators (like a heater relay) to simulate
continuous control.

```python
from simmate.apps.lab_automation.controllers import TimeProportional

controller = TimeProportional(setpoint=25.0, cycle_time=2.0)
output = controller.eval(current_temperature)
```

### Fuzzy Logic Controller

Allows for rule-based control logic, which is particularly useful for complex
or non-linear systems like pH control.

```python
from simmate.apps.lab_automation.controllers import FuzzyLogic

rules = [
    {"max": 20, "output": 1.0},
    {"min": 20, "max": 25, "output": 0.5},
    {"min": 25, "output": 0.0},
]
controller = FuzzyLogic(rules=rules)
output = controller.eval(current_temperature)
```
