#!/usr/bin/env python3
"""
ROI Controls UI Module
Provides UI controls for ROI (Region of Interest) settings
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from camera.roi_manager import ROIManager, ROISettings


class ROIControlPanel:
    """ROI control panel with tabbed interface for each camera"""

    def __init__(self, parent: tk.Widget, roi_manager: "ROIManager"):
        self.parent = parent
        self.roi_manager = roi_manager
        self.widgets: Dict[str, Any] = {}
        self.camera_tabs: Dict[str, ttk.Frame] = {}
        
        # Callback functions
        self.on_roi_changed: Optional[Callable] = None
        
        self.setup_roi_controls()

    def setup_roi_controls(self):
        """Setup the ROI control interface"""
        # Main ROI control frame
        main_frame = ttk.LabelFrame(self.parent, text="ROI Controls", padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Global controls frame
        global_frame = ttk.LabelFrame(main_frame, text="Global Settings", padding=5)
        global_frame.pack(fill=tk.X, pady=(0, 10))

        # Overlay visibility toggle
        self.widgets["overlay_var"] = tk.BooleanVar(value=True)
        overlay_check = ttk.Checkbutton(
            global_frame,
            text="Show ROI Overlay",
            variable=self.widgets["overlay_var"],
            command=self._on_overlay_toggle
        )
        overlay_check.pack(side=tk.LEFT, padx=5)

        # Reset all button
        reset_all_btn = ttk.Button(
            global_frame,
            text="Reset All ROI",
            command=self._on_reset_all
        )
        reset_all_btn.pack(side=tk.RIGHT, padx=5)

        # Notebook for camera-specific controls
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs for each camera
        self._create_camera_tabs()

    def _create_camera_tabs(self):
        """Create tabs for each connected camera"""
        # Clear existing tabs
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self.camera_tabs.clear()

        # Create tabs only for CAM_A (ROI is only for CAM_A)
        connected_cameras = self.roi_manager.camera_controller.get_connected_cameras()
        if "CAM_A" in connected_cameras:
            self._create_camera_tab("CAM_A")
        else:
            # Show a message if CAM_A is not connected
            no_camera_frame = ttk.Frame(self.notebook)
            self.notebook.add(no_camera_frame, text="ROI")
            ttk.Label(no_camera_frame, text="CAM_A not connected\nROI is only available for CAM_A", 
                     justify=tk.CENTER).pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    def _create_camera_tab(self, camera_name: str):
        """Create a tab for a specific camera"""
        # Create tab frame
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=camera_name)
        self.camera_tabs[camera_name] = tab_frame

        # Enable/Disable ROI
        enable_frame = ttk.LabelFrame(tab_frame, text="ROI Control", padding=5)
        enable_frame.pack(fill=tk.X, pady=(0, 10))

        self.widgets[f"{camera_name}_enabled_var"] = tk.BooleanVar(value=False)
        enable_check = ttk.Checkbutton(
            enable_frame,
            text="Enable ROI",
            variable=self.widgets[f"{camera_name}_enabled_var"],
            command=lambda: self._on_roi_enabled(camera_name)
        )
        enable_check.pack(side=tk.LEFT, padx=5)

        # Focus region toggle
        self.widgets[f"{camera_name}_focus_var"] = tk.BooleanVar(value=False)
        focus_check = ttk.Checkbutton(
            enable_frame,
            text="Use for Focus",
            variable=self.widgets[f"{camera_name}_focus_var"],
            command=lambda: self._on_focus_toggle(camera_name)
        )
        focus_check.pack(side=tk.RIGHT, padx=5)

        # Position controls
        position_frame = ttk.LabelFrame(tab_frame, text="ROI Position", padding=5)
        position_frame.pack(fill=tk.X, pady=(0, 10))

        # X position
        x_frame = ttk.Frame(position_frame)
        x_frame.pack(fill=tk.X, pady=2)
        ttk.Label(x_frame, text="Center X:", width=10).pack(side=tk.LEFT)
        self.widgets[f"{camera_name}_x_scale"] = ttk.Scale(
            x_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            command=lambda val: self._on_position_change(camera_name, 'x', float(val))
        )
        self.widgets[f"{camera_name}_x_scale"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.widgets[f"{camera_name}_x_label"] = ttk.Label(x_frame, text="0.50", width=6)
        self.widgets[f"{camera_name}_x_label"].pack(side=tk.RIGHT)

        # Y position
        y_frame = ttk.Frame(position_frame)
        y_frame.pack(fill=tk.X, pady=2)
        ttk.Label(y_frame, text="Center Y:", width=10).pack(side=tk.LEFT)
        self.widgets[f"{camera_name}_y_scale"] = ttk.Scale(
            y_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            command=lambda val: self._on_position_change(camera_name, 'y', float(val))
        )
        self.widgets[f"{camera_name}_y_scale"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.widgets[f"{camera_name}_y_label"] = ttk.Label(y_frame, text="0.50", width=6)
        self.widgets[f"{camera_name}_y_label"].pack(side=tk.RIGHT)

        # Size controls
        size_frame = ttk.LabelFrame(tab_frame, text="ROI Size", padding=5)
        size_frame.pack(fill=tk.X, pady=(0, 10))

        # Width
        width_frame = ttk.Frame(size_frame)
        width_frame.pack(fill=tk.X, pady=2)
        ttk.Label(width_frame, text="Width:", width=10).pack(side=tk.LEFT)
        self.widgets[f"{camera_name}_width_scale"] = ttk.Scale(
            width_frame,
            from_=0.1,
            to=1.0,
            orient=tk.HORIZONTAL,
            command=lambda val: self._on_size_change(camera_name, 'width', float(val))
        )
        self.widgets[f"{camera_name}_width_scale"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.widgets[f"{camera_name}_width_label"] = ttk.Label(width_frame, text="0.30", width=6)
        self.widgets[f"{camera_name}_width_label"].pack(side=tk.RIGHT)

        # Height
        height_frame = ttk.Frame(size_frame)
        height_frame.pack(fill=tk.X, pady=2)
        ttk.Label(height_frame, text="Height:", width=10).pack(side=tk.LEFT)
        self.widgets[f"{camera_name}_height_scale"] = ttk.Scale(
            height_frame,
            from_=0.1,
            to=1.0,
            orient=tk.HORIZONTAL,
            command=lambda val: self._on_size_change(camera_name, 'height', float(val))
        )
        self.widgets[f"{camera_name}_height_scale"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.widgets[f"{camera_name}_height_label"] = ttk.Label(height_frame, text="0.30", width=6)
        self.widgets[f"{camera_name}_height_label"].pack(side=tk.RIGHT)

        # Exposure compensation
        exposure_frame = ttk.LabelFrame(tab_frame, text="Exposure Compensation", padding=5)
        exposure_frame.pack(fill=tk.X, pady=(0, 10))

        exposure_control_frame = ttk.Frame(exposure_frame)
        exposure_control_frame.pack(fill=tk.X, pady=2)
        ttk.Label(exposure_control_frame, text="Compensation:", width=12).pack(side=tk.LEFT)
        self.widgets[f"{camera_name}_exposure_scale"] = ttk.Scale(
            exposure_control_frame,
            from_=-9,
            to=9,
            orient=tk.HORIZONTAL,
            command=lambda val: self._on_exposure_change(camera_name, int(float(val)))
        )
        self.widgets[f"{camera_name}_exposure_scale"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.widgets[f"{camera_name}_exposure_label"] = ttk.Label(exposure_control_frame, text="0", width=6)
        self.widgets[f"{camera_name}_exposure_label"].pack(side=tk.RIGHT)

        # Apply ROI button
        apply_frame = ttk.Frame(tab_frame)
        apply_frame.pack(fill=tk.X, pady=(10, 0))
        apply_btn = ttk.Button(
            apply_frame,
            text="Apply ROI Settings",
            command=lambda: self._on_apply_roi(camera_name)
        )
        apply_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Reset button for this camera
        reset_btn = ttk.Button(
            apply_frame,
            text=f"Reset {camera_name} ROI",
            command=lambda: self._on_reset_camera(camera_name)
        )
        reset_btn.pack(side=tk.RIGHT)

        # Initialize values from current settings
        self._update_controls_from_settings(camera_name)

    def _update_controls_from_settings(self, camera_name: str):
        """Update UI controls from current ROI settings"""
        roi_settings = self.roi_manager.get_roi_settings(camera_name)
        if not roi_settings:
            return

        # Update checkboxes
        self.widgets[f"{camera_name}_enabled_var"].set(roi_settings.enabled)
        self.widgets[f"{camera_name}_focus_var"].set(roi_settings.focus_region)

        # Update scales and labels
        self.widgets[f"{camera_name}_x_scale"].set(roi_settings.x)
        self.widgets[f"{camera_name}_x_label"].config(text=f"{roi_settings.x:.2f}")
        
        self.widgets[f"{camera_name}_y_scale"].set(roi_settings.y)
        self.widgets[f"{camera_name}_y_label"].config(text=f"{roi_settings.y:.2f}")
        
        self.widgets[f"{camera_name}_width_scale"].set(roi_settings.width)
        self.widgets[f"{camera_name}_width_label"].config(text=f"{roi_settings.width:.2f}")
        
        self.widgets[f"{camera_name}_height_scale"].set(roi_settings.height)
        self.widgets[f"{camera_name}_height_label"].config(text=f"{roi_settings.height:.2f}")
        
        self.widgets[f"{camera_name}_exposure_scale"].set(roi_settings.exposure_compensation)
        self.widgets[f"{camera_name}_exposure_label"].config(text=f"{roi_settings.exposure_compensation:+d}")

    def _on_overlay_toggle(self):
        """Handle overlay visibility toggle"""
        visible = self.widgets["overlay_var"].get()
        self.roi_manager.set_roi_overlay_visibility(visible)

    def _on_roi_enabled(self, camera_name: str):
        """Handle ROI enable/disable - apply immediately"""
        enabled = self.widgets[f"{camera_name}_enabled_var"].get()
        self.roi_manager.enable_roi(camera_name, enabled)
        if self.on_roi_changed:
            self.on_roi_changed(camera_name)

    def _on_focus_toggle(self, camera_name: str):
        """Handle focus region toggle - apply immediately"""
        enabled = self.widgets[f"{camera_name}_focus_var"].get()
        self.roi_manager.set_focus_region(camera_name, enabled)
        if self.on_roi_changed:
            self.on_roi_changed(camera_name)

    def _on_position_change(self, camera_name: str, axis: str, value: float):
        """Handle position change (update UI only, don't apply to camera)"""
        # Update UI labels only
        if axis == 'x':
            self.widgets[f"{camera_name}_x_label"].config(text=f"{value:.2f}")
        elif axis == 'y':
            self.widgets[f"{camera_name}_y_label"].config(text=f"{value:.2f}")

    def _on_size_change(self, camera_name: str, dimension: str, value: float):
        """Handle size change (update UI only, don't apply to camera)"""
        # Update UI labels only
        if dimension == 'width':
            self.widgets[f"{camera_name}_width_label"].config(text=f"{value:.2f}")
        elif dimension == 'height':
            self.widgets[f"{camera_name}_height_label"].config(text=f"{value:.2f}")

    def _on_exposure_change(self, camera_name: str, value: int):
        """Handle exposure compensation change (update UI only, don't apply to camera)"""
        # Update UI label only
        self.widgets[f"{camera_name}_exposure_label"].config(text=f"{value:+d}")

    def _on_apply_roi(self, camera_name: str):
        """Apply ROI settings to camera"""
        # Get current UI values
        x = self.widgets[f"{camera_name}_x_scale"].get()
        y = self.widgets[f"{camera_name}_y_scale"].get()
        width = self.widgets[f"{camera_name}_width_scale"].get()
        height = self.widgets[f"{camera_name}_height_scale"].get()
        exposure = int(self.widgets[f"{camera_name}_exposure_scale"].get())
        enabled = self.widgets[f"{camera_name}_enabled_var"].get()
        focus_region = self.widgets[f"{camera_name}_focus_var"].get()
        
        # Apply all settings to ROI manager
        self.roi_manager.set_roi_position(camera_name, x, y)
        self.roi_manager.set_roi_size(camera_name, width, height)
        self.roi_manager.set_exposure_compensation(camera_name, exposure)
        self.roi_manager.enable_roi(camera_name, enabled)
        self.roi_manager.set_focus_region(camera_name, focus_region)
        
        # Show feedback
        print(f"ROI settings applied for {camera_name}: pos=({x:.2f},{y:.2f}), size=({width:.2f}x{height:.2f}), exp={exposure:+d}, enabled={enabled}, focus={focus_region}")
        
        if self.on_roi_changed:
            self.on_roi_changed(camera_name)

    def _on_reset_camera(self, camera_name: str):
        """Reset ROI settings for a specific camera"""
        self.roi_manager.reset_roi_settings(camera_name)
        self._update_controls_from_settings(camera_name)
        if self.on_roi_changed:
            self.on_roi_changed(camera_name)

    def _on_reset_all(self):
        """Reset all ROI settings"""
        if messagebox.askyesno("Reset ROI", "Reset all ROI settings to defaults?"):
            self.roi_manager.reset_all_roi_settings()
            for camera_name in self.camera_tabs:
                self._update_controls_from_settings(camera_name)
            if self.on_roi_changed:
                self.on_roi_changed("all")

    def refresh_camera_tabs(self):
        """Refresh camera tabs when cameras are connected/disconnected"""
        self._create_camera_tabs()

    def set_roi_changed_callback(self, callback: Callable):
        """Set callback for ROI changes"""
        self.on_roi_changed = callback
