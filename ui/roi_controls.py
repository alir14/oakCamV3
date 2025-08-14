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

        # Mouse ROI selection toggle
        self.widgets["mouse_roi_var"] = tk.BooleanVar(value=False)
        mouse_roi_check = ttk.Checkbutton(
            global_frame,
            text="Enable Mouse ROI Selection",
            variable=self.widgets["mouse_roi_var"],
            command=self._on_mouse_roi_toggle
        )
        mouse_roi_check.pack(side=tk.LEFT, padx=5)

        # Reset all button
        reset_all_btn = ttk.Button(
            global_frame,
            text="Reset All ROI",
            command=self._on_reset_all
        )
        reset_all_btn.pack(side=tk.RIGHT, padx=5)

        # Instructions frame
        instructions_frame = ttk.LabelFrame(main_frame, text="Mouse ROI Instructions", padding=5)
        instructions_frame.pack(fill=tk.X, pady=(0, 10))
        
        instructions_text = """Mouse ROI Selection:
1. Enable 'Mouse ROI Selection' above
2. Click and drag on CAM_A display to select ROI region
3. Release mouse to apply the ROI
4. ROI will be automatically enabled and applied to camera
5. Use exposure compensation slider to fine-tune exposure within ROI"""
        
        instructions_label = ttk.Label(instructions_frame, text=instructions_text, justify=tk.LEFT)
        instructions_label.pack(fill=tk.X, padx=5, pady=5)

        # ROI Settings frame (only for CAM_A)
        roi_settings_frame = ttk.LabelFrame(main_frame, text="ROI Settings (CAM_A)", padding=5)
        roi_settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Focus region toggle
        self.widgets["CAM_A_focus_var"] = tk.BooleanVar(value=False)
        focus_check = ttk.Checkbutton(
            roi_settings_frame,
            text="Use ROI for Focus",
            variable=self.widgets["CAM_A_focus_var"],
            command=lambda: self._on_focus_toggle("CAM_A")
        )
        focus_check.pack(side=tk.LEFT, padx=5)

        # Exposure compensation
        exposure_frame = ttk.LabelFrame(main_frame, text="Exposure Compensation", padding=5)
        exposure_frame.pack(fill=tk.X, pady=(0, 10))

        exposure_control_frame = ttk.Frame(exposure_frame)
        exposure_control_frame.pack(fill=tk.X, pady=2)
        ttk.Label(exposure_control_frame, text="Compensation:", width=12).pack(side=tk.LEFT)
        self.widgets["CAM_A_exposure_scale"] = ttk.Scale(
            exposure_control_frame,
            from_=-9,
            to=9,
            orient=tk.HORIZONTAL,
            command=lambda val: self._on_exposure_change("CAM_A", int(float(val)))
        )
        self.widgets["CAM_A_exposure_scale"].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.widgets["CAM_A_exposure_label"] = ttk.Label(exposure_control_frame, text="0", width=6)
        self.widgets["CAM_A_exposure_label"].pack(side=tk.RIGHT)

        # Apply and Reset buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        apply_btn = ttk.Button(
            button_frame,
            text="Apply ROI Settings",
            command=lambda: self._on_apply_roi("CAM_A")
        )
        apply_btn.pack(side=tk.LEFT, padx=(0, 5))

        reset_btn = ttk.Button(
            button_frame,
            text="Reset CAM_A ROI",
            command=lambda: self._on_reset_camera("CAM_A")
        )
        reset_btn.pack(side=tk.RIGHT)

        # Initialize values from current settings
        self._update_controls_from_settings("CAM_A")

    def _create_camera_tabs(self):
        """Create tabs for each connected camera - DEPRECATED"""
        # This method is no longer used since we simplified the UI
        pass

    def _create_camera_tab(self, camera_name: str):
        """Create a tab for a specific camera - DEPRECATED"""
        # This method is no longer used since we simplified the UI
        pass

    def _update_controls_from_settings(self, camera_name: str):
        """Update UI controls from current ROI settings"""
        roi_settings = self.roi_manager.get_roi_settings(camera_name)
        if not roi_settings:
            return

        # Update checkboxes (only focus region since enable is handled by mouse)
        self.widgets[f"{camera_name}_focus_var"].set(roi_settings.focus_region)

        # Update scales and labels
        self.widgets[f"{camera_name}_exposure_scale"].set(roi_settings.exposure_compensation)
        self.widgets[f"{camera_name}_exposure_label"].config(text=f"{roi_settings.exposure_compensation:+d}")

    def _on_overlay_toggle(self):
        """Handle overlay visibility toggle"""
        visible = self.widgets["overlay_var"].get()
        self.roi_manager.set_roi_overlay_visibility(visible)

    def _on_mouse_roi_toggle(self):
        """Handle mouse ROI selection toggle"""
        enabled = self.widgets["mouse_roi_var"].get()
        self.roi_manager.enable_mouse_roi(enabled)
        if self.on_roi_changed:
            self.on_roi_changed("mouse_roi")

    def _on_roi_enabled(self, camera_name: str):
        """Handle ROI enable/disable - apply immediately"""
        enabled = self.widgets[f"{camera_name}_enabled_var"].get()
        print(f"UI: ROI {'enabled' if enabled else 'disabled'} for {camera_name}")
        self.roi_manager.enable_roi(camera_name, enabled)
        if self.on_roi_changed:
            self.on_roi_changed(camera_name)

    def _on_focus_toggle(self, camera_name: str):
        """Handle focus region toggle - apply immediately"""
        enabled = self.widgets[f"{camera_name}_focus_var"].get()
        print(f"UI: ROI focus region {'enabled' if enabled else 'disabled'} for {camera_name}")
        self.roi_manager.set_focus_region(camera_name, enabled)
        if self.on_roi_changed:
            self.on_roi_changed(camera_name)

    def _on_exposure_change(self, camera_name: str, value: int):
        """Handle exposure compensation change (update UI only, don't apply to camera)"""
        # Update UI label only
        self.widgets[f"{camera_name}_exposure_label"].config(text=f"{value:+d}")

    def _on_apply_roi(self, camera_name: str):
        """Apply ROI settings to camera"""
        # Get current UI values
        exposure = int(self.widgets[f"{camera_name}_exposure_scale"].get())
        focus_region = self.widgets[f"{camera_name}_focus_var"].get()
        
        print(f"UI: Applying ROI settings for {camera_name}: exp={exposure:+d}, focus={focus_region}")
        
        # Apply all settings to ROI manager
        self.roi_manager.set_exposure_compensation(camera_name, exposure)
        self.roi_manager.set_focus_region(camera_name, focus_region)
        
        # Show feedback
        print(f"UI: ROI settings applied for {camera_name}: exp={exposure:+d}, focus={focus_region}")
        
        if self.on_roi_changed:
            self.on_roi_changed(camera_name)

    def _on_reset_camera(self, camera_name: str):
        """Reset ROI settings for a specific camera"""
        print(f"UI: Resetting ROI settings for {camera_name}")
        self.roi_manager.reset_roi_settings(camera_name)
        self._update_controls_from_settings(camera_name)
        if self.on_roi_changed:
            self.on_roi_changed(camera_name)

    def _on_reset_all(self):
        """Reset all ROI settings"""
        if messagebox.askyesno("Reset ROI", "Reset all ROI settings to defaults?"):
            print("UI: Resetting all ROI settings")
            self.roi_manager.reset_all_roi_settings()
            self._update_controls_from_settings("CAM_A")
            if self.on_roi_changed:
                self.on_roi_changed("all")

    def refresh_camera_tabs(self):
        """Refresh camera tabs when cameras are connected/disconnected - DEPRECATED"""
        # This method is no longer used since we simplified the UI
        pass

    def set_roi_changed_callback(self, callback: Callable):
        """Set callback for ROI changes"""
        self.on_roi_changed = callback

    def update_mouse_roi_status(self):
        """Update mouse ROI status in UI"""
        if "mouse_roi_var" in self.widgets:
            current_status = self.roi_manager.is_mouse_roi_enabled()
            self.widgets["mouse_roi_var"].set(current_status)
