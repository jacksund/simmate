import logging
import time
from datetime import datetime
from pathlib import Path

import cv2


class Camera:
    """
    Utility for interfacing with a camera using OpenCV. Supports single frames,
    timelapses, and video compilation.

    This class supports "lazy" connections: you can call `capture_frame`
    directly without a context manager, and it will handle opening/closing
    the camera automatically. This is ideal for long-interval timelapses
    (>60s) or multi-camera setups.

    Example usage (Single Camera):
    ```python
    from simmate.apps.lab_automation.sensors import Camera

    # Simple capture (auto-opens and auto-closes camera)
    cam = Camera(camera_index=0)
    cam.capture_frame("snapshot.jpg")
    ```

    Example usage (Multi-Camera Timelapse):
    ```python
    cameras = [Camera(0), Camera(1)]
    for i in range(10):
        for cam in cameras:
            cam.capture_frame(f"cam{cam.camera_index}_frame{i:03d}.jpg")
        time.sleep(60)
    ```

    Example usage (Explicit Context):
    ```python
    # Use as a context manager if you want to keep the connection open
    # (e.g. for high-speed captures)
    with Camera(camera_index=0) as cam:
        for i in range(10):
            cam.capture_frame(f"frame_{i}.jpg")
            time.sleep(0.1)
    ```
    """

    def __init__(
        self,
        camera_index: int = 0,
        res_width: int = 1920,
        res_height: int = 1080,
    ):
        self.camera_index = camera_index
        self.res_width = res_width
        self.res_height = res_height
        self._cap = None

    def __repr__(self):
        return f"Camera(index={self.camera_index}, resolution={self.res_width}x{self.res_height})"

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *_):
        self.close()

    def open(self):
        """Opens the camera connection if not already open."""
        if self._cap:
            return

        self._cap = cv2.VideoCapture(self.camera_index)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.res_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.res_height)

        if not self._cap.isOpened():
            raise RuntimeError(f"Could not access camera at index {self.camera_index}")

    def close(self):
        """Closes the camera connection."""
        if self._cap:
            self._cap.release()
            self._cap = None

    def capture_frame(
        self,
        filename: str | Path = None,
        add_timestamp: bool = True,
    ):
        """
        Captures a single frame. If the camera is closed, it will briefly open
        it to take the picture and then close it again.
        """
        # Track if we need to close the camera after this capture
        was_closed = self._cap is None
        if was_closed:
            self.open()

        try:
            # Flush buffer (grab 5 frames) to ensure we don't get a stale image
            for _ in range(5):
                self._cap.grab()

            ret, frame = self._cap.read()
            if not ret:
                raise RuntimeError(
                    f"Failed to capture frame from camera {self.camera_index}"
                )

            if add_timestamp:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(
                    frame,
                    timestamp,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )

            if filename:
                cv2.imwrite(str(filename), frame)

            return frame
        finally:
            if was_closed:
                self.close()

    def start_timelapse(
        self,
        output_dir: str | Path = "timelapse_frames",
        interval: int = 300,
        total_frames: int = None,
        total_hours: float = None,
    ):
        """
        Captures frames at regular intervals. If the camera is not already
        opened via a context manager, it will open/close for every frame.
        """
        if total_frames is None:
            if total_hours is None:
                raise ValueError("Provide either total_frames or total_hours")
            total_frames = int((total_hours * 3600) // interval)

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logging.info(
            f"Starting timelapse on Cam {self.camera_index}: {total_frames} frames"
        )

        for i in range(total_frames):
            filename = output_path / f"frame_{i:05d}.jpg"
            try:
                self.capture_frame(filename=filename)
                logging.info(f"Saved {filename}")
            except Exception as e:
                logging.error(f"Frame {i} failed: {e}")

            if i < total_frames - 1:
                time.sleep(interval)

    @staticmethod
    def create_timelapse(
        image_folder: str | Path,
        output_video: str | Path,
        fps: int = 100,
    ):
        """
        Compiles JPEG images in a folder into a video file.
        """
        folder = Path(image_folder)
        images = sorted(list(folder.glob("*.jpg")))

        if not images:
            logging.warning(f"No images found in {image_folder}")
            return

        # Use first image to determine video dimensions
        frame = cv2.imread(str(images[0]))
        h, w, _ = frame.shape

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        video = cv2.VideoWriter(str(output_video), fourcc, fps, (w, h))

        for img_path in images:
            video.write(cv2.imread(str(img_path)))

        video.release()
        logging.info(f"Video saved to {output_video}")
