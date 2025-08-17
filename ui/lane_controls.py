#!/usr/bin/env python3
"""
Lane Detection Controls UI Module
Provides UI controls for lane detection settings
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from lane_detection.lane_detector import LaneDetector
    from lane_detection.lane_visualizer import LaneVisualizer


class LaneControlPanel:
    """Lane detection control panel"""
    
    def __init__(self, parent: tk.Widget, lane_detector: "LaneDetector", 
                 lane_visualizer: "LaneVisualizer"):
        self.parent = parent
        self.lane_detector = lane_detector
        self.lane_visualizer = lane_visualizer
        self.widgets: Dict[str, Any] = {}
        
        # Callback functions
        self.on_lane_detection_changed: Optional[Callable] = None
        
        self.setup_lane_controls()
    
    def setup_lane_controls(self):
        """Setup the lane detection control interface"""
        # Main lane control frame
        main_frame = ttk.LabelFrame(self.parent, text="Lane Detection", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Detection control frame
        detection_frame = ttk.LabelFrame(main_frame, text="Detection Control", padding=5)
        detection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Enable/Disable lane detection
        self.widgets["detection_enabled_var"] = tk.BooleanVar(value=False)
        detection_check = ttk.Checkbutton(
            detection_frame,
            text="Enable Lane Detection",
            variable=self.widgets["detection_enabled_var"],
            command=self._on_detection_toggle
        )
        detection_check.pack(side=tk.LEFT, padx=5)
        
        # Confidence threshold
        confidence_frame = ttk.LabelFrame(main_frame, text="Confidence Threshold", padding=5)
        confidence_frame.pack(fill=tk.X, pady=(0, 10))
        
        confidence_control_frame = ttk.Frame(confidence_frame)
        confidence_control_frame.pack(fill=tk.X, pady=2)
        ttk.Label(confidence_control_frame, text="Threshold:", width=12).pack(side=tk.LEFT)
        self.widgets["confidence_scale"] = ttk.Scale(
            confidence_control_frame,
            from_=0.1,
            to=1.0,
            orient=tk.HORIZONTAL,
            command=lambda val: self._on_confidence_change(float(val))
        )
        self.widgets["confidence_scale"].set(0.5)  # Default value
        self.widgets["confidence_scale"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.widgets["confidence_label"] = ttk.Label(confidence_control_frame, text="0.5", width=6)
        self.widgets["confidence_label"].pack(side=tk.RIGHT)
        
        # Visualization options frame
        viz_frame = ttk.LabelFrame(main_frame, text="Visualization Options", padding=5)
        viz_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Show points toggle
        self.widgets["show_points_var"] = tk.BooleanVar(value=True)
        points_check = ttk.Checkbutton(
            viz_frame,
            text="Show Lane Points",
            variable=self.widgets["show_points_var"],
            command=self._on_viz_option_change
        )
        points_check.pack(side=tk.LEFT, padx=5)
        
        # Show lines toggle
        self.widgets["show_lines_var"] = tk.BooleanVar(value=True)
        lines_check = ttk.Checkbutton(
            viz_frame,
            text="Show Lane Lines",
            variable=self.widgets["show_lines_var"],
            command=self._on_viz_option_change
        )
        lines_check.pack(side=tk.LEFT, padx=5)
        
        # Show filled area toggle
        self.widgets["show_filled_var"] = tk.BooleanVar(value=False)
        filled_check = ttk.Checkbutton(
            viz_frame,
            text="Show Filled Area",
            variable=self.widgets["show_filled_var"],
            command=self._on_viz_option_change
        )
        filled_check.pack(side=tk.LEFT, padx=5)
        
        # Line thickness control
        thickness_frame = ttk.LabelFrame(main_frame, text="Line Thickness", padding=5)
        thickness_frame.pack(fill=tk.X, pady=(0, 10))
        
        thickness_control_frame = ttk.Frame(thickness_frame)
        thickness_control_frame.pack(fill=tk.X, pady=2)
        ttk.Label(thickness_control_frame, text="Thickness:", width=12).pack(side=tk.LEFT)
        self.widgets["thickness_scale"] = ttk.Scale(
            thickness_control_frame,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            command=lambda val: self._on_thickness_change(int(float(val)))
        )
        self.widgets["thickness_scale"].set(3)  # Default value
        self.widgets["thickness_scale"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.widgets["thickness_label"] = ttk.Label(thickness_control_frame, text="3", width=6)
        self.widgets["thickness_label"].pack(side=tk.RIGHT)
        
        # Action buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Start/Stop detection button
        self.widgets["start_stop_btn"] = ttk.Button(
            button_frame,
            text="Start Detection",
            command=self._on_start_stop_detection
        )
        self.widgets["start_stop_btn"].pack(side=tk.LEFT, padx=(0, 5))
        
        # Reset settings button
        reset_btn = ttk.Button(
            button_frame,
            text="Reset Settings",
            command=self._on_reset_settings
        )
        reset_btn.pack(side=tk.RIGHT)
        
        # Status label
        self.widgets["status_label"] = ttk.Label(main_frame, text="Status: Stopped", 
                                                foreground="red")
        self.widgets["status_label"].pack(fill=tk.X, pady=(10, 0))
    
    def _on_detection_toggle(self):
        """Handle detection enable/disable toggle"""
        enabled = self.widgets["detection_enabled_var"].get()
        print(f"Lane detection {'enabled' if enabled else 'disabled'}")
        
        if self.on_lane_detection_changed:
            self.on_lane_detection_changed("detection_toggle", enabled)
    
    def _on_confidence_change(self, value: float):
        """Handle confidence threshold change"""
        # Update label
        if "confidence_label" in self.widgets:
            self.widgets["confidence_label"].config(text=f"{value:.1f}")
        
        # Update detector
        self.lane_detector.set_confidence_threshold(value)
        
        print(f"Lane detection confidence threshold: {value:.1f}")
        
        if self.on_lane_detection_changed:
            self.on_lane_detection_changed("confidence", value)
    
    def _on_viz_option_change(self):
        """Handle visualization option changes"""
        show_points = self.widgets["show_points_var"].get()
        show_lines = self.widgets["show_lines_var"].get()
        show_filled = self.widgets["show_filled_var"].get()
        
        # Update visualizer
        self.lane_visualizer.set_visualization_options(
            show_points=show_points,
            show_lines=show_lines,
            show_filled_area=show_filled
        )
        
        print(f"Visualization options: points={show_points}, lines={show_lines}, filled={show_filled}")
        
        if self.on_lane_detection_changed:
            self.on_lane_detection_changed("visualization", {
                "show_points": show_points,
                "show_lines": show_lines,
                "show_filled": show_filled
            })
    
    def _on_thickness_change(self, thickness: int):
        """Handle line thickness change"""
        # Update label
        if "thickness_label" in self.widgets:
            self.widgets["thickness_label"].config(text=str(thickness))
        
        # Update visualizer
        self.lane_visualizer.set_line_thickness(thickness)
        
        print(f"Lane line thickness: {thickness}")
        
        if self.on_lane_detection_changed:
            self.on_lane_detection_changed("thickness", thickness)
    
    def _on_start_stop_detection(self):
        """Handle start/stop detection button"""
        if self.lane_detector.is_running():
            # Stop detection
            self.lane_detector.stop_detection()
            self.widgets["start_stop_btn"].config(text="Start Detection")
            self.widgets["status_label"].config(text="Status: Stopped", foreground="red")
            print("Lane detection stopped")
        else:
            # Start detection
            if self.lane_detector.start_detection():
                self.widgets["start_stop_btn"].config(text="Stop Detection")
                self.widgets["status_label"].config(text="Status: Running", foreground="green")
                print("Lane detection started")
            else:
                messagebox.showerror("Error", "Failed to start lane detection")
    
    def _on_reset_settings(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Reset all lane detection settings to defaults?"):
            # Reset confidence threshold
            self.widgets["confidence_scale"].set(0.5)
            self.widgets["confidence_label"].config(text="0.5")
            self.lane_detector.set_confidence_threshold(0.5)
            
            # Reset visualization options
            self.widgets["show_points_var"].set(True)
            self.widgets["show_lines_var"].set(True)
            self.widgets["show_filled_var"].set(False)
            self.lane_visualizer.set_visualization_options(True, True, False)
            
            # Reset line thickness
            self.widgets["thickness_scale"].set(3)
            self.widgets["thickness_label"].config(text="3")
            self.lane_visualizer.set_line_thickness(3)
            
            print("Lane detection settings reset to defaults")
            
            if self.on_lane_detection_changed:
                self.on_lane_detection_changed("reset", None)
    
    def set_lane_detection_callback(self, callback: Callable):
        """Set callback for lane detection changes"""
        self.on_lane_detection_changed = callback
    
    def update_status(self, is_running: bool):
        """Update status display"""
        if is_running:
            self.widgets["start_stop_btn"].config(text="Stop Detection")
            self.widgets["status_label"].config(text="Status: Running", foreground="green")
        else:
            self.widgets["start_stop_btn"].config(text="Start Detection")
            self.widgets["status_label"].config(text="Status: Stopped", foreground="red")
