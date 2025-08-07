#!/usr/bin/env python3
"""
Control Panel Module
Manages the camera control UI panel
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from camera.settings import CameraSettingsManager


class ControlPanel:
    """Manages the camera control UI panel"""

    def __init__(self, parent: tk.Widget, settings_manager: "CameraSettingsManager"):
        self.parent = parent
        self.settings_manager = settings_manager
        self.widgets: Dict[str, Any] = {}

        # Callback functions (to be set by main application)
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_capture: Optional[Callable] = None
        self.on_record_toggle: Optional[Callable] = None
        self.on_save_dir_change: Optional[Callable] = None
        self.on_settings_change: Optional[Callable] = None

        self.setup_controls()

    def setup_controls(self):
        """Setup all control widgets"""
        self._setup_connection_controls()
        self._setup_device_info()
        self._setup_resolution_controls()
        self._setup_auto_controls()  # This now creates the tabbed interface
        self._setup_action_controls()

    def _setup_connection_controls(self):
        """Setup connection status and buttons"""
        status_frame = ttk.LabelFrame(self.parent, text="Connection", padding=5)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_label = ttk.Label(
            status_frame, text="Disconnected", foreground="red"
        )
        self.status_label.pack(pady=2)

        button_frame = ttk.Frame(status_frame)
        button_frame.pack()

        self.connect_btn = ttk.Button(
            button_frame, text="Connect", command=self._on_connect_clicked
        )
        self.connect_btn.pack(side=tk.LEFT, padx=2)

        self.disconnect_btn = ttk.Button(
            button_frame, text="Disconnect", command=self._on_disconnect_clicked
        )
        self.disconnect_btn.pack(side=tk.LEFT, padx=2)

    def _setup_device_info(self):
        """Setup device information display"""
        info_frame = ttk.LabelFrame(self.parent, text="Device Info", padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.device_info_label = ttk.Label(
            info_frame, text="No device connected", font=("Arial", 9)
        )
        self.device_info_label.pack()

    def _setup_resolution_controls(self):
        """Setup resolution and FPS controls with dropdown"""
        res_frame = ttk.LabelFrame(self.parent, text="Stream Settings", padding=5)
        res_frame.pack(fill=tk.X, pady=(0, 10))

        # Resolution dropdown
        ttk.Label(res_frame, text="Resolution:").grid(
            row=0, column=0, sticky=tk.W, padx=2
        )

        # Common resolutions for OAK cameras
        self.resolution_options = [
            "320x240",
            "640x480",
            "800x600",
            "1280x720",
            "1280x800",
            "1920x1080",
            "1920x1200",
            "2560x1440",
            "3840x2160",
        ]

        current_width = self.settings_manager.get_setting("resolution_width")
        current_height = self.settings_manager.get_setting("resolution_height")
        current_resolution = f"{current_width}x{current_height}"

        # If current resolution is not in predefined list, add it
        if current_resolution not in self.resolution_options:
            self.resolution_options.append(current_resolution)

        self.widgets["resolution_var"] = tk.StringVar(value=current_resolution)
        resolution_dropdown = ttk.Combobox(
            res_frame,
            textvariable=self.widgets["resolution_var"],
            values=self.resolution_options,
            state="readonly",
            width=15,
        )
        resolution_dropdown.grid(row=0, column=1, padx=2, sticky=tk.W)

        # Custom resolution button
        custom_res_btn = ttk.Button(
            res_frame, text="Custom...", command=self._show_custom_resolution_dialog
        )
        custom_res_btn.grid(row=0, column=2, padx=2)

        # FPS dropdown
        ttk.Label(res_frame, text="FPS:").grid(row=1, column=0, sticky=tk.W, padx=2)

        fps_options = ["5", "10", "15", "20", "25", "30", "45", "60"]
        current_fps = str(self.settings_manager.get_setting("fps"))
        if current_fps not in fps_options:
            fps_options.append(current_fps)

        self.widgets["fps_var"] = tk.StringVar(value=current_fps)
        fps_dropdown = ttk.Combobox(
            res_frame,
            textvariable=self.widgets["fps_var"],
            values=fps_options,
            state="readonly",
            width=8,
        )
        fps_dropdown.grid(row=1, column=1, padx=2, sticky=tk.W)

        # Apply button
        apply_btn = ttk.Button(
            res_frame, text="Apply Settings", command=self._on_apply_stream_settings
        )
        apply_btn.grid(row=2, column=0, columnspan=3, pady=5)

    def _show_custom_resolution_dialog(self):
        """Show dialog for custom resolution input"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Custom Resolution")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make it modal

        # Center the dialog
        dialog.transient(self.parent.winfo_toplevel())

        ttk.Label(dialog, text="Enter custom resolution:").pack(pady=10)

        frame = ttk.Frame(dialog)
        frame.pack(pady=5)

        ttk.Label(frame, text="Width:").grid(row=0, column=0, padx=5)
        width_var = tk.IntVar(
            value=self.settings_manager.get_setting("resolution_width")
        )
        width_entry = ttk.Entry(frame, textvariable=width_var, width=8)
        width_entry.grid(row=0, column=1, padx=5)

        ttk.Label(frame, text="Height:").grid(row=0, column=2, padx=5)
        height_var = tk.IntVar(
            value=self.settings_manager.get_setting("resolution_height")
        )
        height_entry = ttk.Entry(frame, textvariable=height_var, width=8)
        height_entry.grid(row=0, column=3, padx=5)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        def apply_custom():
            width = width_var.get()
            height = height_var.get()
            if width > 0 and height > 0:
                custom_res = f"{width}x{height}"
                if custom_res not in self.resolution_options:
                    self.resolution_options.append(custom_res)

                self.widgets["resolution_var"].set(custom_res)
                dialog.destroy()
            else:
                messagebox.showerror(
                    "Invalid Resolution", "Please enter valid width and height values"
                )

        ttk.Button(button_frame, text="Apply", command=apply_custom).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

    def _setup_auto_controls(self):
        """Setup camera settings in tabbed interface"""
        settings_frame = ttk.LabelFrame(self.parent, text="Camera Settings", padding=5)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Create notebook for camera settings tabs
        self.settings_notebook = ttk.Notebook(settings_frame)
        self.settings_notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Auto/Manual Controls
        auto_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(auto_frame, text="Auto/Manual")
        self._setup_auto_manual_tab(auto_frame)

        # Tab 2: Image Quality
        quality_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(quality_frame, text="Image Quality")
        self._setup_image_quality_tab(quality_frame)

        # Tab 3: Advanced Settings
        advanced_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(advanced_frame, text="Advanced")
        self._setup_advanced_tab(advanced_frame)

    def _setup_auto_manual_tab(self, parent):
        """Setup auto/manual controls tab"""
        # Auto Controls Section
        auto_section = ttk.LabelFrame(parent, text="Automatic Controls", padding=5)
        auto_section.pack(fill=tk.X, pady=(0, 10))

        # Auto Exposure
        self.widgets["auto_exposure"] = tk.BooleanVar(
            value=self.settings_manager.get_auto_mode("auto_exposure")
        )
        auto_exp_check = ttk.Checkbutton(
            auto_section,
            text="Auto Exposure",
            variable=self.widgets["auto_exposure"],
            command=self._on_auto_exposure_changed,
        )
        auto_exp_check.pack(anchor=tk.W, pady=2)

        # Auto Focus
        self.widgets["auto_focus"] = tk.BooleanVar(
            value=self.settings_manager.get_auto_mode("auto_focus")
        )
        auto_focus_check = ttk.Checkbutton(
            auto_section,
            text="Auto Focus",
            variable=self.widgets["auto_focus"],
            command=self._on_auto_focus_changed,
        )
        auto_focus_check.pack(anchor=tk.W, pady=2)

        # Auto White Balance
        self.widgets["auto_wb"] = tk.BooleanVar(
            value=self.settings_manager.get_auto_mode("auto_white_balance")
        )
        auto_wb_check = ttk.Checkbutton(
            auto_section,
            text="Auto White Balance",
            variable=self.widgets["auto_wb"],
            command=self._on_auto_wb_changed,
        )
        auto_wb_check.pack(anchor=tk.W, pady=2)

        # Lock Controls Section
        lock_section = ttk.LabelFrame(parent, text="Lock Controls", padding=5)
        lock_section.pack(fill=tk.X, pady=(0, 10))

        lock_frame = ttk.Frame(lock_section)
        lock_frame.pack(fill=tk.X)

        self.widgets["ae_lock"] = tk.BooleanVar()
        ttk.Checkbutton(
            lock_frame,
            text="Auto Exposure Lock",
            variable=self.widgets["ae_lock"],
            command=self._on_ae_lock_changed,
        ).pack(anchor=tk.W, pady=2)

        self.widgets["awb_lock"] = tk.BooleanVar()
        ttk.Checkbutton(
            lock_frame,
            text="Auto White Balance Lock",
            variable=self.widgets["awb_lock"],
            command=self._on_awb_lock_changed,
        ).pack(anchor=tk.W, pady=2)

        # Manual Controls Section
        manual_section = ttk.LabelFrame(parent, text="Manual Controls", padding=5)
        manual_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create scrollable frame for manual controls
        self._setup_manual_controls_in_frame(
            manual_section,
            [
                (
                    "Exposure (μs):",
                    "exposure",
                    self.settings_manager.EXPOSURE_MIN,
                    self.settings_manager.EXPOSURE_MAX,
                    self._on_exposure_changed,
                ),
                (
                    "ISO:",
                    "iso",
                    self.settings_manager.ISO_MIN,
                    self.settings_manager.ISO_MAX,
                    self._on_iso_changed,
                ),
                (
                    "Focus:",
                    "focus",
                    self.settings_manager.FOCUS_MIN,
                    self.settings_manager.FOCUS_MAX,
                    self._on_focus_changed,
                ),
            ],
        )

        # Trigger Controls Section
        trigger_section = ttk.LabelFrame(parent, text="Trigger Controls", padding=5)
        trigger_section.pack(fill=tk.X)

        trigger_frame = ttk.Frame(trigger_section)
        trigger_frame.pack()

        ttk.Button(
            trigger_frame, text="Trigger AutoFocus", command=self._on_trigger_autofocus
        ).pack(side=tk.LEFT, padx=5)

    def _setup_image_quality_tab(self, parent):
        """Setup image quality controls tab"""
        # Color Controls Section
        color_section = ttk.LabelFrame(parent, text="Color Adjustments", padding=5)
        color_section.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self._setup_manual_controls_in_frame(
            color_section,
            [
                (
                    "Brightness:",
                    "brightness",
                    self.settings_manager.BRIGHTNESS_MIN,
                    self.settings_manager.BRIGHTNESS_MAX,
                    self._on_brightness_changed,
                ),
                (
                    "Contrast:",
                    "contrast",
                    self.settings_manager.CONTRAST_MIN,
                    self.settings_manager.CONTRAST_MAX,
                    self._on_contrast_changed,
                ),
                (
                    "Saturation:",
                    "saturation",
                    self.settings_manager.SATURATION_MIN,
                    self.settings_manager.SATURATION_MAX,
                    self._on_saturation_changed,
                ),
                (
                    "White Balance (K):",
                    "white_balance",
                    self.settings_manager.WB_MIN,
                    self.settings_manager.WB_MAX,
                    self._on_white_balance_changed,
                ),
            ],
        )

        # Image Enhancement Section
        enhancement_section = ttk.LabelFrame(
            parent, text="Image Enhancement", padding=5
        )
        enhancement_section.pack(fill=tk.BOTH, expand=True)

        self._setup_manual_controls_in_frame(
            enhancement_section,
            [
                (
                    "Sharpness:",
                    "sharpness",
                    self.settings_manager.SHARPNESS_MIN,
                    self.settings_manager.SHARPNESS_MAX,
                    self._on_sharpness_changed,
                ),
            ],
        )

    def _setup_advanced_tab(self, parent):
        """Setup advanced settings tab"""
        # Noise Reduction Section
        denoise_section = ttk.LabelFrame(parent, text="Noise Reduction", padding=5)
        denoise_section.pack(fill=tk.X, pady=(0, 10))

        self._setup_manual_controls_in_frame(
            denoise_section,
            [
                (
                    "Luma Denoise:",
                    "luma_denoise",
                    0,
                    4,
                    lambda v: self.settings_manager.set_luma_denoise(v),
                ),
                (
                    "Chroma Denoise:",
                    "chroma_denoise",
                    0,
                    4,
                    lambda v: self.settings_manager.set_chroma_denoise(v),
                ),
            ],
        )

        # Other Advanced Settings
        other_section = ttk.LabelFrame(parent, text="Other Settings", padding=5)
        other_section.pack(fill=tk.X, pady=(0, 10))

        # Anti-banding dropdown
        anti_band_frame = ttk.Frame(other_section)
        anti_band_frame.pack(fill=tk.X, pady=2)

        ttk.Label(anti_band_frame, text="Anti-banding:").pack(side=tk.LEFT)
        anti_banding_options = ["OFF", "50Hz", "60Hz", "AUTO"]
        self.widgets["anti_banding_var"] = tk.StringVar(value="AUTO")
        anti_banding_combo = ttk.Combobox(
            anti_band_frame,
            textvariable=self.widgets["anti_banding_var"],
            values=anti_banding_options,
            state="readonly",
            width=10,
        )
        anti_banding_combo.pack(side=tk.LEFT, padx=10)

        # Effect mode dropdown
        effect_frame = ttk.Frame(other_section)
        effect_frame.pack(fill=tk.X, pady=2)

        ttk.Label(effect_frame, text="Effect Mode:").pack(side=tk.LEFT)
        effect_options = [
            "OFF",
            "MONO",
            "NEGATIVE",
            "SOLARIZE",
            "SKETCH",
            "WHITEBOARD",
            "BLACKBOARD",
        ]
        self.widgets["effect_mode_var"] = tk.StringVar(value="OFF")
        effect_combo = ttk.Combobox(
            effect_frame,
            textvariable=self.widgets["effect_mode_var"],
            values=effect_options,
            state="readonly",
            width=12,
        )
        effect_combo.pack(side=tk.LEFT, padx=10)

        # Reset Section
        reset_section = ttk.LabelFrame(parent, text="Reset", padding=5)
        reset_section.pack(fill=tk.X)

        ttk.Button(
            reset_section,
            text="Reset All Settings to Defaults",
            command=self._on_reset_settings,
        ).pack()

    def _setup_manual_controls_in_frame(self, parent, controls):
        """Setup manual controls with sliders in a given frame"""
        # Create canvas and scrollbar for scrollable content
        canvas = tk.Canvas(parent, height=120)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for i, (label, key, min_val, max_val, callback) in enumerate(controls):
            # Control frame
            control_frame = ttk.Frame(scrollable_frame)
            control_frame.pack(fill=tk.X, pady=2)

            # Label
            ttk.Label(control_frame, text=label, width=15).pack(side=tk.LEFT)

            # Variable
            var = tk.IntVar(value=self.settings_manager.get_setting(key))
            self.widgets[f"{key}_var"] = var

            # Scale
            scale = ttk.Scale(
                control_frame,
                from_=min_val,
                to=max_val,
                variable=var,
                orient=tk.HORIZONTAL,
                length=200,
                command=lambda v, cb=callback, va=var: cb(int(va.get())),
            )
            scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

            # Value label
            value_label = ttk.Label(control_frame, textvariable=var, width=6)
            value_label.pack(side=tk.RIGHT)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _setup_manual_controls(self):
        """Manual controls are now handled in tabs - this method kept for compatibility"""
        pass

    def _setup_advanced_controls(self):
        """Advanced controls are now handled in tabs - this method kept for compatibility"""
        pass

    def _setup_action_controls(self):
        """Setup action buttons and save directory"""
        action_frame = ttk.LabelFrame(self.parent, text="Actions", padding=10)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        # Capture button
        self.capture_btn = ttk.Button(
            action_frame, text="📷 Capture Images", command=self._on_capture_clicked
        )
        self.capture_btn.pack(fill=tk.X, pady=2)

        # Record button
        self.record_btn = ttk.Button(
            action_frame, text="🎥 Start Recording", command=self._on_record_clicked
        )
        self.record_btn.pack(fill=tk.X, pady=2)

        # Recording status
        self.recording_status_label = ttk.Label(
            action_frame, text="", foreground="green"
        )
        self.recording_status_label.pack(pady=2)

        # Save directory controls
        save_frame = ttk.Frame(action_frame)
        save_frame.pack(fill=tk.X, pady=(10, 0))

        self.save_dir_btn = ttk.Button(
            save_frame, text="📁 Set Save Directory", command=self._on_save_dir_clicked
        )
        self.save_dir_btn.pack(fill=tk.X, pady=2)

        self.save_dir_label = ttk.Label(
            save_frame, text="Save to: ./captures", wraplength=200, font=("Arial", 8)
        )
        self.save_dir_label.pack(pady=2)

        # Disk space info
        self.disk_space_label = ttk.Label(save_frame, text="", font=("Arial", 8))
        self.disk_space_label.pack()

    # Event handlers (internal)
    def _on_connect_clicked(self):
        if self.on_connect:
            self.on_connect()

    def _on_disconnect_clicked(self):
        if self.on_disconnect:
            self.on_disconnect()

    def _on_capture_clicked(self):
        if self.on_capture:
            self.on_capture()

    def _on_record_clicked(self):
        if self.on_record_toggle:
            self.on_record_toggle()

    def _on_save_dir_clicked(self):
        if self.on_save_dir_change:
            self.on_save_dir_change()

    def _on_apply_stream_settings(self):
        """Apply stream settings"""
        if self.on_settings_change:
            # Parse resolution from dropdown
            resolution_str = self.widgets["resolution_var"].get()
            if "x" in resolution_str:
                width_str, height_str = resolution_str.split("x")
                try:
                    width = int(width_str.strip())
                    height = int(height_str.strip())
                except ValueError:
                    tk.messagebox.showerror(
                        "Invalid Resolution", "Please select a valid resolution"
                    )
                    return
            else:
                tk.messagebox.showerror(
                    "Invalid Resolution", "Please select a valid resolution"
                )
                return

            # Parse FPS
            try:
                fps = int(self.widgets["fps_var"].get())
            except ValueError:
                tk.messagebox.showerror(
                    "Invalid FPS", "Please select a valid FPS value"
                )
                return

    def _on_apply_stream_settings(self):
        """Apply stream settings"""
        if self.on_settings_change:
            # Parse resolution from dropdown
            resolution_str = self.widgets["resolution_var"].get()
            if "x" in resolution_str:
                width_str, height_str = resolution_str.split("x")
                try:
                    width = int(width_str.strip())
                    height = int(height_str.strip())
                except ValueError:
                    tk.messagebox.showerror(
                        "Invalid Resolution", "Please select a valid resolution"
                    )
                    return
            else:
                tk.messagebox.showerror(
                    "Invalid Resolution", "Please select a valid resolution"
                )
                return

            # Parse FPS
            try:
                fps = int(self.widgets["fps_var"].get())
            except ValueError:
                tk.messagebox.showerror(
                    "Invalid FPS", "Please select a valid FPS value"
                )
                return

            settings = {"width": width, "height": height, "fps": fps}
            self.on_settings_change(settings)

    def _on_reset_settings(self):
        """Reset all settings to defaults"""
        self.settings_manager.reset_to_defaults()
        self._update_all_widgets()

    # Auto control event handlers
    def _on_auto_exposure_changed(self):
        self.settings_manager.set_auto_exposure(self.widgets["auto_exposure"].get())

    def _on_auto_focus_changed(self):
        self.settings_manager.set_auto_focus(self.widgets["auto_focus"].get())

    def _on_auto_wb_changed(self):
        self.settings_manager.set_auto_white_balance(self.widgets["auto_wb"].get())

    def _on_ae_lock_changed(self):
        self.settings_manager.set_auto_exposure_lock(self.widgets["ae_lock"].get())

    def _on_awb_lock_changed(self):
        self.settings_manager.set_auto_white_balance_lock(
            self.widgets["awb_lock"].get()
        )

    def _on_trigger_autofocus(self):
        self.settings_manager.trigger_autofocus()

    # Manual control event handlers
    def _on_exposure_changed(self, value: int):
        self.settings_manager.set_exposure(value)

    def _on_iso_changed(self, value: int):
        self.settings_manager.set_iso(value)

    def _on_focus_changed(self, value: int):
        self.settings_manager.set_focus(value)

    def _on_brightness_changed(self, value: int):
        self.settings_manager.set_brightness(value)

    def _on_contrast_changed(self, value: int):
        self.settings_manager.set_contrast(value)

    def _on_saturation_changed(self, value: int):
        self.settings_manager.set_saturation(value)

    def _on_sharpness_changed(self, value: int):
        self.settings_manager.set_sharpness(value)

    def _on_white_balance_changed(self, value: int):
        self.settings_manager.set_white_balance(value)

    # Public interface methods
    def set_callbacks(self, **callbacks):
        """Set callback functions for various events"""
        for name, callback in callbacks.items():
            if hasattr(self, f"on_{name}"):
                setattr(self, f"on_{name}", callback)

    def update_connection_status(self, connected: bool, device_info: Dict = None):
        """Update connection status display"""
        if connected:
            self.status_label.config(text="Connected", foreground="green")
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")

            if device_info:
                info_text = f"Platform: {device_info.get('platform', 'Unknown')}\n"
                info_text += f"Cameras: {device_info.get('connected_cameras', 0)}"
                self.device_info_label.config(text=info_text)
        else:
            self.status_label.config(text="Disconnected", foreground="red")
            self.connect_btn.config(state="normal")
            self.disconnect_btn.config(state="disabled")
            self.device_info_label.config(text="No device connected")

    def update_save_directory_display(self, directory: Path):
        """Update save directory display"""
        self.save_dir_label.config(text=f"Save to: {directory}")

    def update_disk_space_display(self, free_gb: float, total_gb: float):
        """Update disk space display"""
        percentage = (free_gb / total_gb) * 100 if total_gb > 0 else 0
        self.disk_space_label.config(
            text=f"Free space: {free_gb:.1f}GB ({percentage:.1f}%)"
        )

    def update_record_button(self, recording: bool, duration: float = 0.0):
        """Update record button text and status"""
        if recording:
            self.record_btn.config(text="⏹️ Stop Recording")
            status_text = f"Recording... {duration:.1f}s"
            self.recording_status_label.config(text=status_text, foreground="red")
        else:
            self.record_btn.config(text="🎥 Start Recording")
            self.recording_status_label.config(text="", foreground="green")

    def _update_all_widgets(self):
        """Update all widget values from settings manager"""
        # Update auto mode checkboxes
        self.widgets["auto_exposure"].set(
            self.settings_manager.get_auto_mode("auto_exposure")
        )
        self.widgets["auto_focus"].set(
            self.settings_manager.get_auto_mode("auto_focus")
        )
        self.widgets["auto_wb"].set(
            self.settings_manager.get_auto_mode("auto_white_balance")
        )
        self.widgets["ae_lock"].set(
            self.settings_manager.get_auto_mode("auto_exposure_lock")
        )
        self.widgets["awb_lock"].set(
            self.settings_manager.get_auto_mode("auto_white_balance_lock")
        )

        # Update manual control values
        manual_controls = [
            "exposure",
            "iso",
            "focus",
            "brightness",
            "contrast",
            "saturation",
            "sharpness",
            "white_balance",
            "luma_denoise",
            "chroma_denoise",
        ]

        for control in manual_controls:
            var_key = f"{control}_var"
            if var_key in self.widgets:
                self.widgets[var_key].set(self.settings_manager.get_setting(control))

        # Update resolution settings
        width = self.settings_manager.get_setting("resolution_width")
        height = self.settings_manager.get_setting("resolution_height")
        resolution_str = f"{width}x{height}"

        if "resolution_var" in self.widgets:
            # Add current resolution to options if not present
            if resolution_str not in self.resolution_options:
                self.resolution_options.append(resolution_str)
            self.widgets["resolution_var"].set(resolution_str)

        # Update FPS
        if "fps_var" in self.widgets:
            self.widgets["fps_var"].set(str(self.settings_manager.get_setting("fps")))

    def enable_controls(self, enabled: bool):
        """Enable or disable all camera controls"""
        state = "normal" if enabled else "disabled"

        # Disable/enable specific widgets that should only work when connected
        widgets_to_toggle = [
            "auto_exposure",
            "auto_focus",
            "auto_wb",
            "ae_lock",
            "awb_lock",
        ]

        for widget_name in widgets_to_toggle:
            if widget_name in self.widgets:
                try:
                    # For checkbuttons, we need to access the widget differently
                    # This is a simplified approach - in practice you'd store widget references
                    pass
                except:
                    pass

    def get_current_values(self) -> Dict[str, Any]:
        """Get current values from all widgets"""
        values = {}
        for key, widget in self.widgets.items():
            if hasattr(widget, "get"):
                values[key] = widget.get()
        return values

    def show_status_message(self, message: str, message_type: str = "info"):
        """Show a temporary status message"""
        # This could be expanded to show temporary status messages
        # For now, we'll just print to console
        print(f"{message_type.upper()}: {message}")

    def update_recording_duration(self, duration: float):
        """Update recording duration display"""
        if duration > 0:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            status_text = f"Recording... {minutes:02d}:{seconds:02d}"
            self.recording_status_label.config(text=status_text, foreground="red")

    def set_widget_value(self, widget_name: str, value: Any):
        """Set value for a specific widget"""
        if widget_name in self.widgets and hasattr(self.widgets[widget_name], "set"):
            self.widgets[widget_name].set(value)
