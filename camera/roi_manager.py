#!/usr/bin/env python3
"""
ROI (Region of Interest) Manager Module
Handles ROI-based exposure and focus control for OAK cameras
Based on Luxonis depthai-core camera_roi_exposure_focus.py example
"""

import depthai as dai
import numpy as np
import cv2
from typing import Dict, Optional, Tuple, List, Callable
from dataclasses import dataclass
import threading
import time


@dataclass
class ROISettings:
    """ROI settings for a camera"""
    enabled: bool = False
    x: float = 0.5  # Center X (0.0 to 1.0)
    y: float = 0.5  # Center Y (0.0 to 1.0)
    width: float = 0.3  # Width (0.0 to 1.0)
    height: float = 0.3  # Height (0.0 to 1.0)
    exposure_compensation: int = 0  # -9 to 9
    focus_region: bool = False  # Whether to use ROI for focus


class ROIManager:
    """Manages ROI-based camera controls for exposure and focus"""

    def __init__(self, camera_controller):
        self.camera_controller = camera_controller
        self.roi_settings: Dict[str, ROISettings] = {}
        self.roi_thread: Optional[threading.Thread] = None
        self.running = False
        
        # ROI visualization settings
        self.show_roi_overlay = True
        self.roi_color = (0, 255, 0)  # Green
        self.roi_thickness = 2
        
        # Mouse interaction settings
        self.mouse_roi_enabled = False
        self.mouse_roi_active = False
        self.mouse_start_point: Optional[Tuple[int, int]] = None
        self.mouse_current_point: Optional[Tuple[int, int]] = None
        self.mouse_roi_camera: Optional[str] = None
        
        # Settings change tracking
        self.settings_changed: Dict[str, bool] = {}
        self.last_applied_settings: Dict[str, Dict] = {}
        
        # Callback for UI updates
        self.on_roi_updated: Optional[Callable] = None
        
        # ROI settings will be initialized when cameras are connected

    def _initialize_roi_settings(self):
        """Initialize ROI settings for CAM_A only"""
        connected_cameras = self.camera_controller.get_connected_cameras()
        if "CAM_A" in connected_cameras and "CAM_A" not in self.roi_settings:
            self.roi_settings["CAM_A"] = ROISettings()
            self.settings_changed["CAM_A"] = True
            self.last_applied_settings["CAM_A"] = {}
            print("ROI settings initialized for CAM_A")

    def initialize_for_cameras(self):
        """Initialize ROI settings for newly connected cameras"""
        self._initialize_roi_settings()

    def start_roi_processing(self):
        """Start ROI processing thread"""
        if self.running:
            return
            
        self.running = True
        self.roi_thread = threading.Thread(target=self._roi_processing_loop, daemon=True)
        self.roi_thread.start()
        print("ROI processing started")

    def stop_roi_processing(self):
        """Stop ROI processing thread"""
        self.running = False
        if self.roi_thread and self.roi_thread.is_alive():
            self.roi_thread.join(timeout=1.0)
        print("ROI processing stopped")

    def _roi_processing_loop(self):
        """Main ROI processing loop - only for CAM_A"""
        while self.running:
            try:
                # Only process CAM_A
                if "CAM_A" in self.roi_settings:
                    roi_settings = self.roi_settings["CAM_A"]
                    if roi_settings.enabled:
                        # Check if settings have changed or need initial application
                        if self._settings_have_changed("CAM_A", roi_settings):
                            print(f"ROI settings changed, applying new settings...")
                            self._apply_roi_settings("CAM_A", roi_settings)
                            self._mark_settings_applied("CAM_A", roi_settings)
                
                time.sleep(0.1)  # 10 FPS update rate
                
            except Exception as e:
                print(f"ROI processing error: {e}")
                time.sleep(0.1)

    def _settings_have_changed(self, camera_name: str, roi_settings: ROISettings) -> bool:
        """Check if ROI settings have changed since last application"""
        if camera_name not in self.last_applied_settings:
            return True
        
        last_settings = self.last_applied_settings[camera_name]
        current_settings = {
            'enabled': roi_settings.enabled,
            'x': roi_settings.x,
            'y': roi_settings.y,
            'width': roi_settings.width,
            'height': roi_settings.height,
            'exposure_compensation': roi_settings.exposure_compensation,
            'focus_region': roi_settings.focus_region
        }
        
        return last_settings != current_settings

    def _mark_settings_applied(self, camera_name: str, roi_settings: ROISettings):
        """Mark that settings have been applied to camera"""
        self.last_applied_settings[camera_name] = {
            'enabled': roi_settings.enabled,
            'x': roi_settings.x,
            'y': roi_settings.y,
            'width': roi_settings.width,
            'height': roi_settings.height,
            'exposure_compensation': roi_settings.exposure_compensation,
            'focus_region': roi_settings.focus_region
        }
        self.settings_changed[camera_name] = False

    def _apply_roi_settings(self, camera_name: str, roi_settings: ROISettings):
        """Apply ROI settings to a specific camera"""
        try:
            # Create camera control
            ctrl = dai.CameraControl()
            
            # Set ROI for exposure
            if roi_settings.enabled:
                # IMPORTANT: ROI requires auto exposure to be enabled
                ctrl.setAutoExposureEnable()
                
                # Convert normalized coordinates to pixel coordinates
                frame = self.camera_controller.get_frame(camera_name)
                if frame is not None:
                    height, width = frame.shape[:2]
                    
                    # Calculate ROI rectangle in pixels (center-based to corner-based)
                    roi_center_x = int(roi_settings.x * width)
                    roi_center_y = int(roi_settings.y * height)
                    roi_w = int(roi_settings.width * width)
                    roi_h = int(roi_settings.height * height)
                    
                    # Convert center coordinates to top-left corner coordinates
                    roi_start_x = roi_center_x - roi_w // 2
                    roi_start_y = roi_center_y - roi_h // 2
                    
                    # Ensure ROI is within bounds
                    roi_start_x = max(0, min(roi_start_x, width - roi_w))
                    roi_start_y = max(0, min(roi_start_y, height - roi_h))
                    roi_w = min(roi_w, width - roi_start_x)
                    roi_h = min(roi_h, height - roi_start_y)
                    
                    # Set exposure ROI using individual parameters (like Luxonis example)
                    ctrl.setAutoExposureRegion(roi_start_x, roi_start_y, roi_w, roi_h)
                    
                    # Set focus ROI if enabled
                    if roi_settings.focus_region:
                        # IMPORTANT: Focus ROI requires auto focus to be enabled
                        ctrl.setAutoFocusMode(dai.CameraControl.AutoFocusMode.CONTINUOUS_VIDEO)
                        ctrl.setAutoFocusRegion(roi_start_x, roi_start_y, roi_w, roi_h)
                    
                    # Set exposure compensation
                    if roi_settings.exposure_compensation != 0:
                        ctrl.setAutoExposureCompensation(roi_settings.exposure_compensation)
                    
                    # Send control to camera
                    self.camera_controller.send_control_to_camera(camera_name, ctrl)
                    
                    print(f"ROI applied to {camera_name}: pos=({roi_start_x},{roi_start_y}), size=({roi_w}x{roi_h}), exp={roi_settings.exposure_compensation:+d}, focus={roi_settings.focus_region}")
                    
        except Exception as e:
            print(f"ROI application error for {camera_name}: {e}")

    # Mouse interaction methods
    def enable_mouse_roi(self, enabled: bool):
        """Enable or disable mouse-based ROI selection"""
        self.mouse_roi_enabled = enabled
        if not enabled:
            self.mouse_roi_active = False
            self.mouse_start_point = None
            self.mouse_current_point = None
            self.mouse_roi_camera = None
        print(f"Mouse ROI selection {'enabled' if enabled else 'disabled'}")

    def handle_mouse_event(self, camera_name: str, event: str, x: int, y: int, frame_width: int, frame_height: int):
        """Handle mouse events for ROI selection"""
        if not self.mouse_roi_enabled or camera_name != "CAM_A":
            return
        
        if event == "mousedown":
            # Start ROI selection
            self.mouse_roi_active = True
            self.mouse_start_point = (x, y)
            self.mouse_current_point = (x, y)
            self.mouse_roi_camera = camera_name
            print(f"ROI selection started at ({x}, {y})")
            
        elif event == "mousemove" and self.mouse_roi_active:
            # Update current mouse position
            self.mouse_current_point = (x, y)
            
        elif event == "mouseup" and self.mouse_roi_active:
            # End ROI selection and apply
            self.mouse_roi_active = False
            if self.mouse_start_point and self.mouse_current_point:
                self._apply_mouse_roi(camera_name, self.mouse_start_point, self.mouse_current_point, frame_width, frame_height)
            self.mouse_start_point = None
            self.mouse_current_point = None
            self.mouse_roi_camera = None

    def _apply_mouse_roi(self, camera_name: str, start_point: Tuple[int, int], end_point: Tuple[int, int], frame_width: int, frame_height: int):
        """Apply ROI based on mouse selection"""
        try:
            # Calculate ROI rectangle from mouse points
            x1, y1 = start_point
            x2, y2 = end_point
            
            # Ensure proper order (top-left to bottom-right)
            roi_start_x = min(x1, x2)
            roi_start_y = min(y1, y2)
            roi_end_x = max(x1, x2)
            roi_end_y = max(y1, y2)
            
            # Calculate center and size
            roi_center_x = (roi_start_x + roi_end_x) // 2
            roi_center_y = (roi_start_y + roi_end_y) // 2
            roi_width = roi_end_x - roi_start_x
            roi_height = roi_end_y - roi_start_y
            
            # Convert to normalized coordinates
            norm_center_x = roi_center_x / frame_width
            norm_center_y = roi_center_y / frame_height
            norm_width = roi_width / frame_width
            norm_height = roi_height / frame_height
            
            # Ensure minimum size
            min_size = 0.05  # 5% of frame
            norm_width = max(norm_width, min_size)
            norm_height = max(norm_height, min_size)
            
            print(f"Mouse ROI selection: raw=({roi_start_x},{roi_start_y})-({roi_end_x},{roi_end_y}), normalized=({norm_center_x:.3f},{norm_center_y:.3f}) size=({norm_width:.3f}x{norm_height:.3f})")
            
            # Update ROI settings
            if camera_name in self.roi_settings:
                old_settings = self.roi_settings[camera_name]
                print(f"Previous ROI settings: pos=({old_settings.x:.3f},{old_settings.y:.3f}), size=({old_settings.width:.3f}x{old_settings.height:.3f}), enabled={old_settings.enabled}")
                
                self.roi_settings[camera_name].x = norm_center_x
                self.roi_settings[camera_name].y = norm_center_y
                self.roi_settings[camera_name].width = norm_width
                self.roi_settings[camera_name].height = norm_height
                self.roi_settings[camera_name].enabled = True
                
                # Mark settings as changed to force re-application
                self.settings_changed[camera_name] = True
                
                # Notify UI of changes
                if self.on_roi_updated:
                    self.on_roi_updated(camera_name, self.roi_settings[camera_name])
                
                print(f"New ROI settings applied: pos=({norm_center_x:.3f},{norm_center_y:.3f}), size=({norm_width:.3f}x{norm_height:.3f}), enabled=True")
                
        except Exception as e:
            print(f"Mouse ROI application error: {e}")

    def set_roi_settings(self, camera_name: str, settings: ROISettings):
        """Set ROI settings for a specific camera"""
        if camera_name in self.roi_settings:
            self.roi_settings[camera_name] = settings
            self.settings_changed[camera_name] = True
            print(f"ROI settings updated for {camera_name}: pos=({settings.x:.3f},{settings.y:.3f}), size=({settings.width:.3f}x{settings.height:.3f}), enabled={settings.enabled}")
            if self.on_roi_updated:
                self.on_roi_updated(camera_name, settings)

    def get_roi_settings(self, camera_name: str) -> Optional[ROISettings]:
        """Get ROI settings for a specific camera"""
        return self.roi_settings.get(camera_name)

    def enable_roi(self, camera_name: str, enabled: bool):
        """Enable or disable ROI for a camera"""
        if camera_name in self.roi_settings:
            old_enabled = self.roi_settings[camera_name].enabled
            self.roi_settings[camera_name].enabled = enabled
            self.settings_changed[camera_name] = True
            print(f"ROI {'enabled' if enabled else 'disabled'} for {camera_name} (was {old_enabled})")
            if self.on_roi_updated:
                self.on_roi_updated(camera_name, self.roi_settings[camera_name])

    def set_roi_position(self, camera_name: str, x: float, y: float):
        """Set ROI center position (normalized coordinates)"""
        if camera_name in self.roi_settings:
            old_x, old_y = self.roi_settings[camera_name].x, self.roi_settings[camera_name].y
            self.roi_settings[camera_name].x = max(0.0, min(1.0, x))
            self.roi_settings[camera_name].y = max(0.0, min(1.0, y))
            self.settings_changed[camera_name] = True
            print(f"ROI position changed for {camera_name}: ({old_x:.3f},{old_y:.3f}) -> ({x:.3f},{y:.3f})")
            if self.on_roi_updated:
                self.on_roi_updated(camera_name, self.roi_settings[camera_name])

    def set_roi_size(self, camera_name: str, width: float, height: float):
        """Set ROI size (normalized coordinates)"""
        if camera_name in self.roi_settings:
            old_width, old_height = self.roi_settings[camera_name].width, self.roi_settings[camera_name].height
            self.roi_settings[camera_name].width = max(0.1, min(1.0, width))
            self.roi_settings[camera_name].height = max(0.1, min(1.0, height))
            self.settings_changed[camera_name] = True
            print(f"ROI size changed for {camera_name}: ({old_width:.3f}x{old_height:.3f}) -> ({width:.3f}x{height:.3f})")
            if self.on_roi_updated:
                self.on_roi_updated(camera_name, self.roi_settings[camera_name])

    def set_exposure_compensation(self, camera_name: str, compensation: int):
        """Set exposure compensation (-9 to 9)"""
        if camera_name in self.roi_settings:
            old_comp = self.roi_settings[camera_name].exposure_compensation
            self.roi_settings[camera_name].exposure_compensation = max(-9, min(9, compensation))
            self.settings_changed[camera_name] = True
            print(f"ROI exposure compensation changed for {camera_name}: {old_comp:+d} -> {compensation:+d}")
            if self.on_roi_updated:
                self.on_roi_updated(camera_name, self.roi_settings[camera_name])

    def set_focus_region(self, camera_name: str, enabled: bool):
        """Enable or disable ROI for focus control"""
        if camera_name in self.roi_settings:
            old_focus = self.roi_settings[camera_name].focus_region
            self.roi_settings[camera_name].focus_region = enabled
            self.settings_changed[camera_name] = True
            print(f"ROI focus region {'enabled' if enabled else 'disabled'} for {camera_name} (was {old_focus})")
            if self.on_roi_updated:
                self.on_roi_updated(camera_name, self.roi_settings[camera_name])

    def draw_roi_overlay(self, frame: np.ndarray, camera_name: str) -> np.ndarray:
        """Draw ROI overlay on frame - only for CAM_A"""
        if not self.show_roi_overlay or camera_name != "CAM_A" or camera_name not in self.roi_settings:
            return frame
        
        roi_settings = self.roi_settings[camera_name]
        if not roi_settings.enabled:
            return frame
        
        try:
            # Convert normalized coordinates to pixel coordinates (center-based to corner-based)
            height, width = frame.shape[:2]
            roi_center_x = int(roi_settings.x * width)
            roi_center_y = int(roi_settings.y * height)
            roi_w = int(roi_settings.width * width)
            roi_h = int(roi_settings.height * height)
            
            # Convert center coordinates to top-left corner coordinates
            roi_start_x = roi_center_x - roi_w // 2
            roi_start_y = roi_center_y - roi_h // 2
            
            # Ensure ROI is within bounds
            roi_start_x = max(0, min(roi_start_x, width - roi_w))
            roi_start_y = max(0, min(roi_start_y, height - roi_h))
            roi_w = min(roi_w, width - roi_start_x)
            roi_h = min(roi_h, height - roi_start_y)
            
            # Draw ROI rectangle
            cv2.rectangle(frame, (roi_start_x, roi_start_y), 
                         (roi_start_x + roi_w, roi_start_y + roi_h), 
                         self.roi_color, self.roi_thickness)
            
            # Draw center point
            center_x = roi_start_x + roi_w // 2
            center_y = roi_start_y + roi_h // 2
            cv2.circle(frame, (center_x, center_y), 3, self.roi_color, -1)
            
            # Add text label
            label = f"ROI: {roi_settings.exposure_compensation:+d}"
            if roi_settings.focus_region:
                label += " (Focus)"
            cv2.putText(frame, label, (roi_start_x, roi_start_y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.roi_color, 1)
            
            # Draw mouse selection rectangle if active
            if self.mouse_roi_active and self.mouse_roi_camera == camera_name:
                if self.mouse_start_point and self.mouse_current_point:
                    # Draw selection rectangle
                    cv2.rectangle(frame, self.mouse_start_point, self.mouse_current_point, 
                                 (255, 0, 0), 2)  # Blue for selection
                    
                    # Draw selection text
                    cv2.putText(frame, "Selecting ROI...", (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            
        except Exception as e:
            print(f"ROI overlay drawing error: {e}")
        
        return frame

    def reset_roi_settings(self, camera_name: str):
        """Reset ROI settings to defaults for a camera"""
        if camera_name in self.roi_settings:
            self.roi_settings[camera_name] = ROISettings()
            self.settings_changed[camera_name] = True
            print(f"ROI settings reset for {camera_name}")
            if self.on_roi_updated:
                self.on_roi_updated(camera_name, self.roi_settings[camera_name])

    def reset_all_roi_settings(self):
        """Reset ROI settings for all cameras"""
        for camera_name in self.roi_settings:
            self.reset_roi_settings(camera_name)

    def get_roi_info(self, camera_name: str) -> Dict:
        """Get ROI information for a camera"""
        if camera_name not in self.roi_settings:
            return {}
        
        roi_settings = self.roi_settings[camera_name]
        return {
            "enabled": roi_settings.enabled,
            "position": (roi_settings.x, roi_settings.y),
            "size": (roi_settings.width, roi_settings.height),
            "exposure_compensation": roi_settings.exposure_compensation,
            "focus_region": roi_settings.focus_region
        }

    def set_roi_overlay_visibility(self, visible: bool):
        """Set ROI overlay visibility"""
        self.show_roi_overlay = visible

    def set_roi_overlay_color(self, color: Tuple[int, int, int]):
        """Set ROI overlay color (BGR)"""
        self.roi_color = color

    def set_roi_overlay_thickness(self, thickness: int):
        """Set ROI overlay line thickness"""
        self.roi_thickness = max(1, thickness)

    def is_mouse_roi_enabled(self) -> bool:
        """Check if mouse ROI selection is enabled"""
        return self.mouse_roi_enabled

    def is_mouse_roi_active(self) -> bool:
        """Check if mouse ROI selection is currently active"""
        return self.mouse_roi_active
