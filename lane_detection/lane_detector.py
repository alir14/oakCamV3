#!/usr/bin/env python3
"""
Ultra-Fast Lane Detection Module
Based on Luxonis oak-examples neural-networks/generic-example
"""

import depthai as dai
import numpy as np
import cv2
from typing import Dict, Optional, Tuple, List
import threading
import time
import os


class LaneDetector:
    """Ultra-fast lane detection using OAK cameras"""
    
    def __init__(self, camera_controller):
        self.camera_controller = camera_controller
        self.device: Optional[dai.Device] = None
        self.pipeline: Optional[dai.Pipeline] = None
        self.running = False
        self.detection_thread: Optional[threading.Thread] = None
        
        # Model configuration
        self.model_path = "models/ultra-fast-lane-det-culane.superblob"
        self.input_size = (800, 288)  # Model input size
        self.confidence_threshold = 0.5
        
        # Detection results
        self.latest_results: Dict[str, np.ndarray] = {}
        self.processing_lock = threading.Lock()
        
        # Callback for results
        self.on_detection_result: Optional[callable] = None
        
    def setup_pipeline(self) -> bool:
        """Setup the lane detection pipeline"""
        try:
            # Check if model file exists
            if not os.path.exists(self.model_path):
                print(f"Model file not found: {self.model_path}")
                print("Please download the ultra-fast-lane-detection model")
                return False
            
            # For now, we'll use a hybrid approach that works with the existing camera controller
            # This allows us to use the real camera feed while implementing lane detection
            print("Lane detection pipeline setup (hybrid mode)")
            print("Model file found, using existing camera controller for frame processing")
            return True
            
        except Exception as e:
            print(f"Error creating lane detection pipeline: {e}")
            return False
    
    def start_detection(self) -> bool:
        """Start lane detection processing"""
        if self.running:
            return True
            
        if not self.setup_pipeline():
            return False
            
        try:
            # Use existing camera controller, no need for separate device
            self.running = True
            
            # Start detection thread
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
            
            print("Lane detection started with computer vision")
            return True
            
        except Exception as e:
            print(f"Error starting lane detection: {e}")
            return False
    
    def stop_detection(self):
        """Stop lane detection processing"""
        self.running = False
        
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2.0)
            
        if self.device:
            self.device.close()
            self.device = None
            
        print("Lane detection stopped")
    
    def _detection_loop(self):
        """Main detection processing loop"""
        try:
            while self.running:
                try:
                    # Get frame from existing camera controller
                    if self.camera_controller.device:
                        frame = self.camera_controller.get_frame("CAM_A")
                        if frame is not None:
                            # Process frame for lane detection
                            lanes = self._detect_lanes_in_frame(frame)
                            
                            # Store results
                            with self.processing_lock:
                                self.latest_results["CAM_A"] = lanes
                            
                            # Notify callback
                            if self.on_detection_result:
                                self.on_detection_result("CAM_A", lanes)
                    
                    time.sleep(0.033)  # ~30 FPS
                    
                except Exception as e:
                    print(f"Detection loop error: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"Detection thread error: {e}")
    
    def _detect_lanes_in_frame(self, frame: np.ndarray) -> np.ndarray:
        """Detect lanes in a frame using computer vision techniques"""
        try:
            # Convert to grayscale for edge detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply Canny edge detection
            edges = cv2.Canny(blurred, 50, 150)
            
            # Create a region of interest (ROI) for the road
            height, width = frame.shape[:2]
            roi_vertices = np.array([
                [(0, height), (width * 0.45, height * 0.6), (width * 0.55, height * 0.6), (width, height)]
            ], dtype=np.int32)
            
            # Create a mask for the ROI
            mask = np.zeros_like(edges)
            cv2.fillPoly(mask, roi_vertices, 255)
            
            # Apply the mask to the edges
            masked_edges = cv2.bitwise_and(edges, mask)
            
            # Use Hough Line Transform to detect lines
            lines = cv2.HoughLinesP(masked_edges, 1, np.pi/180, threshold=30, 
                                   minLineLength=30, maxLineGap=150)
            
            lanes = []
            if lines is not None:
                # Group lines by slope to identify left and right lanes
                left_lines = []
                right_lines = []
                
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    if x2 - x1 != 0:  # Avoid division by zero
                        slope = (y2 - y1) / (x2 - x1)
                        
                        # Filter lines by slope (lanes should be roughly vertical)
                        # Allow both steep lines (near vertical) and moderate slopes
                        if abs(slope) > 0.1:  # Allow moderate slopes
                            # Classify by x-position instead of slope
                            avg_x = (x1 + x2) / 2
                            if avg_x < width * 0.5:  # Left side of image
                                left_lines.append(line[0])
                            else:  # Right side of image
                                right_lines.append(line[0])
                
                # Create lane points from left lines
                if left_lines:
                    left_points = self._create_lane_points(left_lines, height, width, "left")
                    if len(left_points) > 3:  # Lower threshold
                        lanes.append(np.array(left_points))
                
                # Create lane points from right lines
                if right_lines:
                    right_points = self._create_lane_points(right_lines, height, width, "right")
                    if len(right_points) > 3:  # Lower threshold
                        lanes.append(np.array(right_points))
            
            return np.array(lanes)
            
        except Exception as e:
            print(f"Error detecting lanes in frame: {e}")
            return np.array([])
    
    def _create_lane_points(self, lines, height, width, lane_side):
        """Create lane points from detected lines"""
        try:
            points = []
            
            # For each y-coordinate, find the average x-coordinate of lines
            for y in range(height - 100, 0, -20):  # Start from bottom, go up
                x_coords = []
                
                for line in lines:
                    x1, y1, x2, y2 = line
                    
                    # Check if this line intersects with the current y-coordinate
                    if min(y1, y2) <= y <= max(y1, y2):
                        if x2 - x1 != 0:
                            slope = (y2 - y1) / (x2 - x1)
                            x = int(x1 + (y - y1) / slope)
                            x_coords.append(x)
                
                if x_coords:
                    # Use the average x-coordinate for this y-level
                    avg_x = int(np.mean(x_coords))
                    
                    # Filter out points that are too far from the expected lane position
                    if lane_side == "left" and avg_x < width * 0.6:
                        points.append((avg_x, y))
                    elif lane_side == "right" and avg_x > width * 0.4:
                        points.append((avg_x, y))
            

            return points
            
        except Exception as e:
            print(f"Error creating lane points: {e}")
            return []
    
    def _simulate_lane_detection(self, frame: np.ndarray) -> np.ndarray:
        """Simulate lane detection results for testing"""
        try:
            # Create simulated lane points
            height, width = frame.shape[:2]
            
            # Simulate left and right lane lines
            lanes = []
            
            # Left lane (curved line)
            left_lane = []
            for y in range(0, height, 20):
                x = int(width * 0.3 + 50 * np.sin(y / height * np.pi))
                if 0 <= x < width:
                    left_lane.append((x, y))
            
            if len(left_lane) > 5:
                lanes.append(np.array(left_lane))
            
            # Right lane (curved line)
            right_lane = []
            for y in range(0, height, 20):
                x = int(width * 0.7 + 50 * np.sin(y / height * np.pi))
                if 0 <= x < width:
                    right_lane.append((x, y))
            
            if len(right_lane) > 5:
                lanes.append(np.array(right_lane))
            
            return np.array(lanes)
            
        except Exception as e:
            print(f"Error simulating lane detection: {e}")
            return np.array([])
    
    def _process_inference_result(self, inference_result):
        """Process neural network inference result"""
        try:
            # Get output data - ultra-fast lane detection outputs probabilities for each lane
            # The model outputs 4 lanes: left, right, center, and other
            output_data = inference_result.getLayerFp16("output")
            
            # Reshape output to expected format (4 lanes, 288 rows, 800 columns)
            output_shape = (1, 4, 288, 800)  # (batch, lanes, height, width)
            output_array = np.array(output_data).reshape(output_shape)
            
            # Process lane detection results
            lanes = self._extract_lanes(output_array)
            
            # Store results
            with self.processing_lock:
                self.latest_results["CAM_A"] = lanes
            
            # Notify callback
            if self.on_detection_result:
                self.on_detection_result("CAM_A", lanes)
                
        except Exception as e:
            print(f"Error processing inference result: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_lanes(self, output_array: np.ndarray) -> np.ndarray:
        """Extract lane coordinates from model output"""
        try:
            # Ultra-fast lane detection outputs probability maps for each lane
            # Each lane has a 288x800 probability map where higher values indicate lane presence
            
            lanes = []
            for lane_idx in range(output_array.shape[1]):  # For each lane (0-3)
                lane_output = output_array[0, lane_idx, :, :]  # Get the lane probability map
                
                # Find lane points above confidence threshold
                lane_points = self._find_lane_points(lane_output)
                if len(lane_points) > 5:  # Only include lanes with enough points
                    lanes.append(np.array(lane_points))
            
            return np.array(lanes)
            
        except Exception as e:
            print(f"Error extracting lanes: {e}")
            return np.array([])
    
    def _find_lane_points(self, lane_output: np.ndarray) -> List[Tuple[int, int]]:
        """Find lane points from lane output"""
        try:
            points = []
            model_height, model_width = lane_output.shape
            
            # For each row in the model output, find the maximum probability point
            for y in range(model_height):
                row_probs = lane_output[y, :]
                max_idx = np.argmax(row_probs)
                max_prob = row_probs[max_idx]
                
                if max_prob > self.confidence_threshold:
                    # Convert model coordinates (800x288) to image coordinates
                    # The model output is 800x288, but we need to scale it to the actual image size
                    # For now, we'll assume the image is 1280x720 (you can adjust this)
                    image_width = 1280
                    image_height = 720
                    
                    x = int(max_idx * image_width / model_width)
                    y_img = int(y * image_height / model_height)
                    
                    # Ensure coordinates are within image bounds
                    if 0 <= x < image_width and 0 <= y_img < image_height:
                        points.append((x, y_img))
            
            return points
            
        except Exception as e:
            print(f"Error finding lane points: {e}")
            return []
    
    def get_latest_results(self, camera_name: str = "CAM_A") -> Optional[np.ndarray]:
        """Get latest detection results for a camera"""
        with self.processing_lock:
            return self.latest_results.get(camera_name)
    
    def set_confidence_threshold(self, threshold: float):
        """Set confidence threshold for lane detection"""
        self.confidence_threshold = max(0.0, min(1.0, threshold))
        print(f"Lane detection confidence threshold set to {self.confidence_threshold}")
    
    def set_detection_callback(self, callback: callable):
        """Set callback for detection results"""
        self.on_detection_result = callback
    
    def is_running(self) -> bool:
        """Check if lane detection is running"""
        return self.running
