# Sensors

Sensors are interfaces for reading data from physical hardware. Simmate provides
built-in support for common lab hardware like temperature probes and cameras.

## Temperature (DS18B20)

The `DS18B20` class provides a simple interface for 1-wire temperature probes.
It handles file I/O automatically and supports both single-reading and continuous
logging.

### Basic Use

```python
from simmate.apps.lab_automation.sensors import DS18B20

# Auto-finds the first connected sensor
sensor = DS18B20()

# Get temperature in Celsius and Fahrenheit
temp_c, temp_f = sensor.get_temperature()
print(f"Current Temperature: {temp_c}°C")
```

### Logging to CSV

You can log temperature data directly to a CSV file for long-term monitoring.

```python
sensor.start_logging(
    output_file="lab_monitor.csv",
    interval=60,  # seconds
    total_hours=24,
)
```

---

## Camera (OpenCV)

The `Camera` class uses OpenCV to interface with USB cameras. It supports
capturing single frames, running timelapses, and compiling videos.

### Basic Use

```python
from simmate.apps.lab_automation.sensors import Camera

# Access the first USB camera (index 0)
cam = Camera(camera_index=0)

# Capture a frame and save it
cam.capture_frame("latest_capture.jpg")
```

### Timelapse & Video

You can automate image capture over time and compile the results into a video.

```python
# Capture a frame every 5 minutes for 12 hours
cam.start_timelapse(
    output_dir="reaction_timelapse",
    interval=300,
    total_hours=12,
)

# Compile images into an MP4 video
Camera.create_timelapse(
    image_folder="reaction_timelapse",
    output_video="reaction_video.mp4",
)
```

---

## Context Managers

Both `DS18B20` and `Camera` support "lazy" connections (opening/closing on every
call) and explicit context managers (keeping the connection open). Use context
managers for high-speed captures or frequent readings.

```python
with Camera(0) as cam:
    for i in range(100):
        cam.capture_frame(f"burst_{i}.jpg")
```
