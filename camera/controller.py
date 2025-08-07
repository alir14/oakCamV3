#!/usr/bin/env python3
"""
Camera Controller Module
Handles all camera operations and DepthAI pipeline management
"""

import depthai as dai
import numpy as np
from typing import Dict, Optional, List


class CameraController:
    """Handles all camera operations and DepthAI pipeline management"""

    def __init__(self):
        self.device: Optional[dai.Device] = None
        self.pipeline: Optional[dai.Pipeline] = None
        self.cameras: Dict[str, dai.node.Camera] = {}
        self.control_queues: Dict[str, dai.DataInputQueue] = {}
        self.output_queues: Dict[str, dai.DataOutputQueue] = {}
        self.running = False

        # Available camera sockets
        self.camera_sockets = {
            "CAM_A": dai.CameraBoardSocket.CAM_A,
            "CAM_B": dai.CameraBoardSocket.CAM_B,
            "CAM_C": dai.CameraBoardSocket.CAM_C,
            "CAM_D": dai.CameraBoardSocket.CAM_D,
        }

    def connect(self) -> tuple[bool, str]:
        """
        Connect to the OAK PoE camera
        Returns: (success: bool, message: str)
        """
        try:
            # Create device - following camera_all.py approach
            self.device = dai.Device()

            # Get connected cameras using the correct method
            connected_cameras = self.device.getConnectedCameras()

            if not connected_cameras:
                return False, "No cameras found on the device"

            # Check if device supports IR laser projector (for depth cameras)
            try:
                if not self.device.setIrLaserDotProjectorIntensity(1):
                    print("IR laser projector not available on this device")
            except Exception as e:
                print(f"IR laser projector setup failed: {e}")

            # Log available cameras for debugging
            camera_names = [socket.name for socket in connected_cameras]
            print(f"Found cameras: {camera_names}")

            return (
                True,
                f"Connected to OAK device with {len(connected_cameras)} cameras: {', '.join(camera_names)}",
            )

        except Exception as e:
            return False, f"Failed to connect to camera: {str(e)}"

    def setup_pipeline(self, width: int, height: int, fps: int) -> bool:
        """Setup the DepthAI pipeline with specified parameters"""
        try:
            if not self.device:
                print("No device available for pipeline setup")
                return False

            # Create pipeline - following camera_all.py approach
            # Note: We DON'T use context manager here because we need to keep it alive
            self.pipeline = dai.Pipeline(self.device)
            connected_cameras = self.device.getConnectedCameras()

            print(f"Setting up pipeline for {len(connected_cameras)} cameras")

            for socket in connected_cameras:
                socket_name = socket.name
                print(f"Configuring camera {socket_name}")

                # Create camera node - exactly like camera_all.py
                cam = self.pipeline.create(dai.node.Camera).build(socket)
                self.cameras[socket_name] = cam

                # Create output queue - simplified approach from camera_all.py
                output_queue = cam.requestFullResolutionOutput().createOutputQueue()
                self.output_queues[socket_name] = output_queue

                # Create control queue for camera controls
                self.control_queues[socket_name] = cam.inputControl.createInputQueue()

                print(f"Successfully configured {socket_name}")

            print(f"Pipeline setup complete for {len(self.cameras)} cameras")
            return True

        except Exception as e:
            print(f"Pipeline setup error: {e}")
            import traceback

            traceback.print_exc()
            return False

    def start_streaming(self) -> bool:
        """Start the camera streaming"""
        try:
            if self.pipeline:
                self.pipeline.start()
                self.running = True
                print("Pipeline started successfully")
                return True
            return False
        except Exception as e:
            print(f"Streaming start error: {e}")
            return False

    def stop_streaming(self):
        """Stop camera streaming"""
        self.running = False
        if self.pipeline:
            try:
                self.pipeline.stop()
                print("Pipeline stopped")
            except:
                pass  # Pipeline might already be stopped

    def get_frame(self, camera_name: str) -> Optional[np.ndarray]:
        """Get latest frame from specified camera"""
        if camera_name in self.output_queues:
            queue = self.output_queues[camera_name]
            if queue.has():
                try:
                    frame = queue.get()
                    return frame.getCvFrame()
                except Exception as e:
                    print(f"Frame retrieval error for {camera_name}: {e}")
        return None

    def send_control_to_camera(self, camera_name: str, ctrl: dai.CameraControl):
        """Send control command to specific camera"""
        if camera_name in self.control_queues:
            try:
                self.control_queues[camera_name].send(ctrl)
            except Exception as e:
                print(f"Control send error for {camera_name}: {e}")

    def send_control_to_all_cameras(self, ctrl: dai.CameraControl):
        """Send control command to all cameras"""
        for camera_name, queue in self.control_queues.items():
            try:
                queue.send(ctrl)
            except Exception as e:
                print(f"Control send error for {camera_name}: {e}")

    def get_connected_cameras(self) -> List[str]:
        """Get list of connected camera names"""
        return list(self.cameras.keys())

    def is_running(self) -> bool:
        """Check if cameras are currently streaming"""
        return self.running and self.pipeline is not None

    def get_device_info(self) -> Optional[dict]:
        """Get device information"""
        if not self.device:
            return None

        try:
            return {
                "platform": self.device.getPlatform().name,
                "connected_cameras": len(self.device.getConnectedCameras()),
                "device_name": (
                    str(self.device.getDeviceName())
                    if hasattr(self.device, "getDeviceName")
                    else "Unknown"
                ),
            }
        except Exception as e:
            print(f"Device info error: {e}")
            return None

    def disconnect(self):
        """Disconnect and cleanup all resources"""
        self.stop_streaming()
        self.pipeline = None

        if self.device:
            try:
                # Cleanup device resources
                pass  # DepthAI handles cleanup automatically
            except:
                pass

        self.device = None
        self.cameras.clear()
        self.control_queues.clear()
        self.output_queues.clear()
        print("Camera controller disconnected")
