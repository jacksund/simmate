import cv2
import time
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class Camera:
    """
    Utility for interfacing with a camera using OpenCV. Supports single frames,
    timelapses, and video compilation.

    Example usage:
    ```python
    from simmate.apps.lab_automation.sensors import Camera

    # Use as a context manager for automatic opening/closing
    with Camera(camera_index=0) as cam:
        # Capture a single frame
        cam.capture_frame("snapshot.jpg")

        # Run a timelapse (e.g. 10 frames, 1 minute apart)
        cam.start_timelapse(
            output_dir="experiment_frames",
            interval=60,
            total_frames=10,
        )

    # Compile the frames into a video (static method)
    Camera.create_timelapse(
        image_folder="experiment_frames",
        output_video="experiment.mp4",
        fps=5,
    )
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

    def capture_frame(self, filename: str | Path = None, add_timestamp: bool = True):
        """
        Captures a single frame. Flushes the buffer to ensure image freshness.
        """
        if not self._cap:
            self.open()

        # Flush buffer (grab 5 frames) to ensure we don't get a stale image
        for _ in range(5):
            self._cap.grab()
        
        ret, frame = self._cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame")

        if add_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                frame, timestamp, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )

        if filename:
            cv2.imwrite(str(filename), frame)
        
        return frame

    def start_timelapse(
        self,
        output_dir: str | Path = "timelapse_frames",
        interval: int = 300,
        total_frames: int = None,
        total_hours: float = None,
    ):
        """
        Captures frames at regular intervals.
        """
        if total_frames is None:
            if total_hours is None:
                raise ValueError("Provide either total_frames or total_hours")
            total_frames = int((total_hours * 3600) // interval)

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting timelapse: {total_frames} frames, {interval}s interval")
        
        for i in range(total_frames):
            filename = output_path / f"frame_{i:05d}.jpg"
            try:
                self.capture_frame(filename=filename)
                logger.info(f"Saved {filename}")
            except Exception as e:
                logger.error(f"Frame {i} failed: {e}")

            if i < total_frames - 1:
                time.sleep(interval)

    @staticmethod
    def create_timelapse(
        image_folder: str | Path, 
        output_video: str | Path, 
        fps: int = 100
    ):
        """
        Compiles JPEG images in a folder into a video file.
        """
        folder = Path(image_folder)
        images = sorted(list(folder.glob("*.jpg")))
        
        if not images:
            logger.warning(f"No images found in {image_folder}")
            return

        # Use first image to determine video dimensions
        frame = cv2.imread(str(images[0]))
        h, w, _ = frame.shape
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        video = cv2.VideoWriter(str(output_video), fourcc, fps, (w, h))

        for img_path in images:
            video.write(cv2.imread(str(img_path)))

        video.release()
        logger.info(f"Video saved to {output_video}")
