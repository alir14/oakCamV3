import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class FileManager:
    """Handles file operations for capturing images and videos"""

    def __init__(self, save_directory: Optional[Path] = None):
        self.save_directory = save_directory or Path.cwd() / "captures"
        self.save_directory.mkdir(exist_ok=True)
        self.video_writers: Dict[str, cv2.VideoWriter] = {}
        self.recording = False
        self.recording_start_time: Optional[datetime] = None

        # Supported image formats
        self.image_formats = [".jpg", ".png", ".bmp", ".tiff"]
        # Supported video codecs
        self.video_codecs = {
            "MJPG": cv2.VideoWriter_fourcc(*"MJPG"),
            "XVID": cv2.VideoWriter_fourcc(*"XVID"),
            "MP4V": cv2.VideoWriter_fourcc(*"mp4v"),
            "H264": cv2.VideoWriter_fourcc(*"H264"),
        }
        self.current_codec = "MJPG"

    def set_save_directory(self, directory: Path) -> bool:
        """Set the save directory"""
        try:
            self.save_directory = directory
            self.save_directory.mkdir(exist_ok=True)
            return True
        except Exception as e:
            print(f"Save directory error: {e}")
            return False

    def get_save_directory(self) -> Path:
        """Get current save directory"""
        return self.save_directory

    def set_video_codec(self, codec: str):
        """Set video codec for recording"""
        if codec in self.video_codecs:
            self.current_codec = codec

    def capture_image(
        self,
        camera_name: str,
        image: np.ndarray,
        format: str = "jpg",
        custom_filename: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Capture and save an image
        Returns: (success: bool, filepath: str)
        """
        try:
            if custom_filename:
                filename = self.save_directory / f"{custom_filename}.{format}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[
                    :-3
                ]  # Include milliseconds
                filename = self.save_directory / f"{camera_name}_{timestamp}.{format}"

            success = cv2.imwrite(str(filename), image)
            return success, str(filename) if success else ""

        except Exception as e:
            print(f"Image capture error: {e}")
            return False, ""

    def capture_images_batch(
        self, images: Dict[str, np.ndarray], format: str = "jpg"
    ) -> tuple[int, List[str]]:
        """
        Capture multiple images with synchronized timestamp
        Returns: (success_count: int, filepaths: List[str])
        """
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S_%f")[:-3]
        # Date-based directory
        date_dir = self.save_directory / now.strftime("%Y-%m-%d")
        try:
            date_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Date dir error: {e}")
            date_dir = self.save_directory
        filepaths = []
        success_count = 0

        for camera_name, image in images.items():
            try:
                filename = date_dir / f"{camera_name}_{timestamp}.{format}"
                if cv2.imwrite(str(filename), image):
                    filepaths.append(str(filename))
                    success_count += 1
            except Exception as e:
                print(f"Batch capture error for {camera_name}: {e}")

        return success_count, filepaths

    def ensure_date_directory(self, dt: Optional[datetime] = None) -> Path:
        dt = dt or datetime.now()
        date_dir = self.save_directory / dt.strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir

    def start_video_recording(
        self,
        camera_names: List[str],
        width: int,
        height: int,
        fps: int,
        codec: Optional[str] = None,
        per_camera_resolutions: Optional[Dict[str, tuple[int, int]]] = None,
    ) -> tuple[bool, str]:
        """
        Start video recording for specified cameras
        Returns: (success: bool, message: str)
        """
        if self.recording:
            return False, "Recording already in progress"

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            codec_name = codec or self.current_codec
            fourcc = self.video_codecs.get(codec_name, self.video_codecs["MJPG"])

            # Determine file extension based on codec
            extension = "avi" if codec_name in ["MJPG", "XVID"] else "mp4"

            for camera_name in camera_names:
                # Resolve per-camera frame size
                if per_camera_resolutions and camera_name in per_camera_resolutions:
                    cam_w, cam_h = per_camera_resolutions[camera_name]
                else:
                    cam_w, cam_h = width, height
                filename = (
                    self.save_directory / f"{camera_name}_video_{timestamp}.{extension}"
                )
                writer = cv2.VideoWriter(str(filename), fourcc, fps, (cam_w, cam_h))

                if not writer.isOpened():
                    # Cleanup any opened writers
                    for w in self.video_writers.values():
                        w.release()
                    self.video_writers.clear()
                    return False, f"Failed to create video writer for {camera_name}"

                self.video_writers[camera_name] = writer

            self.recording = True
            self.recording_start_time = datetime.now()
            return True, f"Recording started for {len(camera_names)} cameras"

        except Exception as e:
            return False, f"Failed to start recording: {str(e)}"

    def write_video_frame(self, camera_name: str, frame: np.ndarray) -> bool:
        """Write frame to video file"""
        if not self.recording or camera_name not in self.video_writers:
            return False

        try:
            self.video_writers[camera_name].write(frame)
            return True
        except Exception as e:
            print(f"Video frame write error for {camera_name}: {e}")
            return False

    def stop_video_recording(self) -> tuple[bool, str, List[str]]:
        """
        Stop video recording
        Returns: (success: bool, message: str, filepaths: List[str])
        """
        if not self.recording:
            return False, "No recording in progress", []

        filepaths = []
        try:
            # Release all video writers and collect filenames
            for camera_name, writer in self.video_writers.items():
                # Try to get the filename from the writer (not directly available)
                # We'll reconstruct it from our naming convention
                timestamp = (
                    self.recording_start_time.strftime("%Y%m%d_%H%M%S")
                    if self.recording_start_time
                    else "unknown"
                )
                extension = "avi" if self.current_codec in ["MJPG", "XVID"] else "mp4"
                filepath = (
                    self.save_directory / f"{camera_name}_video_{timestamp}.{extension}"
                )
                filepaths.append(str(filepath))

                writer.release()

            self.video_writers.clear()
            self.recording = False
            self.recording_start_time = None

            duration = (
                (datetime.now() - self.recording_start_time).total_seconds()
                if self.recording_start_time
                else 0
            )
            return True, f"Recording stopped. Duration: {duration:.1f}s", filepaths

        except Exception as e:
            return False, f"Error stopping recording: {str(e)}", filepaths

    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self.recording

    def get_recording_duration(self) -> float:
        """Get current recording duration in seconds"""
        if not self.recording or not self.recording_start_time:
            return 0.0
        return (datetime.now() - self.recording_start_time).total_seconds()

    def cleanup(self):
        """Cleanup resources"""
        if self.recording:
            self.stop_video_recording()

    def get_available_space(self) -> tuple[float, float]:
        """
        Get available disk space in GB
        Returns: (free_space_gb: float, total_space_gb: float)
        """
        try:
            import shutil

            total, used, free = shutil.disk_usage(self.save_directory)
            return free / (1024**3), total / (1024**3)
        except Exception as e:
            print(f"Disk space check error: {e}")
            return 0.0, 0.0

    def list_captured_files(self, file_type: str = "all") -> List[Path]:
        """
        List captured files in save directory
        file_type: 'images', 'videos', or 'all'
        """
        try:
            files = []
            if file_type in ["images", "all"]:
                for ext in self.image_formats:
                    files.extend(self.save_directory.glob(f"*{ext}"))

            if file_type in ["videos", "all"]:
                for ext in [".avi", ".mp4", ".mov"]:
                    files.extend(self.save_directory.glob(f"*{ext}"))

            return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)

        except Exception as e:
            print(f"File listing error: {e}")
            return []

    def delete_file(self, filepath: Path) -> bool:
        """Delete a file"""
        try:
            filepath.unlink()
            return True
        except Exception as e:
            print(f"File deletion error: {e}")
            return False

    def get_file_info(self, filepath: Path) -> Optional[Dict]:
        """Get file information"""
        try:
            stat = filepath.stat()
            return {
                "name": filepath.name,
                "size_mb": stat.st_size / (1024**2),
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
            }
        except Exception as e:
            print(f"File info error: {e}")
            return None
