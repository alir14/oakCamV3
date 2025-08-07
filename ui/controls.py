import tkinter as tk
from tkinter import ttk
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
        self._setup_auto_controls()
        self._setup_manual_controls()
        self._setup_advanced_controls()
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
        """Setup resolution and FPS controls"""
        res_frame = ttk.LabelFrame(self.parent, text="Stream Settings", padding=5)
        res_frame.pack(fill=tk.X, pady=(0, 10))

        # Width
        ttk.Label(res_frame, text="Width:").grid(row=0, column=0, sticky=tk.W, padx=2)
        self.widgets["width_var"] = tk.IntVar(
            value=self.settings_manager.get_setting("resolution_width")
        )
        width_spinbox = ttk.Spinbox(
            res_frame,
            from_=320,
            to=4096,
            width=8,
            textvariable=self.widgets["width_var"],
        )
        width_spinbox.grid(row=0, column=1, padx=2)

        # Height
        ttk.Label(res_frame, text="Height:").grid(row=1, column=0, sticky=tk.W, padx=2)
        self.widgets["height_var"] = tk.IntVar(
            value=self.settings_manager.get_setting("resolution_height")
        )
        height_spinbox = ttk.Spinbox(
            res_frame,
            from_=240,
            to=3072,
            width=8,
            textvariable=self.widgets["height_var"],
        )
        height_spinbox.grid(row=1, column=1, padx=2)

        # FPS
        ttk.Label(res_frame, text="FPS:").grid(row=2, column=0, sticky=tk.W, padx=2)
        self.widgets["fps_var"] = tk.IntVar(
            value=self.settings_manager.get_setting("fps")
        )
        fps_spinbox = ttk.Spinbox(
            res_frame, from_=1, to=60, width=8, textvariable=self.widgets["fps_var"]
        )
        fps_spinbox.grid(row=2, column=1, padx=2)

        # Apply button
        apply_btn = ttk.Button(
            res_frame, text="Apply Settings", command=self._on_apply_stream_settings
        )
        apply_btn.grid(row=3, column=0, columnspan=2, pady=5)

    def _setup_auto_controls(self):
        """Setup auto mode controls"""
        auto_frame = ttk.LabelFrame(self.parent, text="Auto Controls", padding=5)
        auto_frame.pack(fill=tk.X, pady=(0, 10))

        # Auto Exposure
        self.widgets["auto_exposure"] = tk.BooleanVar(
            value=self.settings_manager.get_auto_mode("auto_exposure")
        )
        auto_exp_check = ttk.Checkbutton(
            auto_frame,
            text="Auto Exposure",
            variable=self.widgets["auto_exposure"],
            command=self._on_auto_exposure_changed,
        )
        auto_exp_check.pack(anchor=tk.W)

        # Auto Focus
        self.widgets["auto_focus"] = tk.BooleanVar(
            value=self.settings_manager.get_auto_mode("auto_focus")
        )
        auto_focus_check = ttk.Checkbutton(
            auto_frame,
            text="Auto Focus",
            variable=self.widgets["auto_focus"],
            command=self._on_auto_focus_changed,
        )
        auto_focus_check.pack(anchor=tk.W)

        # Auto White Balance
        self.widgets["auto_wb"] = tk.BooleanVar(
            value=self.settings_manager.get_auto_mode("auto_white_balance")
        )
        auto_wb_check = ttk.Checkbutton(
            auto_frame,
            text="Auto White Balance",
            variable=self.widgets["auto_wb"],
            command=self._on_auto_wb_changed,
        )
        auto_wb_check.pack(anchor=tk.W)

        # Auto mode locks
        lock_frame = ttk.Frame(auto_frame)
        lock_frame.pack(fill=tk.X, pady=(5, 0))

        self.widgets["ae_lock"] = tk.BooleanVar()
        ttk.Checkbutton(
            lock_frame,
            text="AE Lock",
            variable=self.widgets["ae_lock"],
            command=self._on_ae_lock_changed,
        ).pack(side=tk.LEFT)

        self.widgets["awb_lock"] = tk.BooleanVar()
        ttk.Checkbutton(
            lock_frame,
            text="AWB Lock",
            variable=self.widgets["awb_lock"],
            command=self._on_awb_lock_changed,
        ).pack(side=tk.LEFT)

        # Trigger buttons
        trigger_frame = ttk.Frame(auto_frame)
        trigger_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(
            trigger_frame, text="Trigger AF", command=self._on_trigger_autofocus
        ).pack(side=tk.LEFT, padx=2)

    def _setup_manual_controls(self):
        """Setup manual control sliders"""
        manual_frame = ttk.LabelFrame(self.parent, text="Manual Controls", padding=5)
        manual_frame.pack(fill=tk.X, pady=(0, 10))

        # Create scrollable frame for controls
        canvas = tk.Canvas(manual_frame, height=200)
        scrollbar = ttk.Scrollbar(manual_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        controls = [
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
                "Sharpness:",
                "sharpness",
                self.settings_manager.SHARPNESS_MIN,
                self.settings_manager.SHARPNESS_MAX,
                self._on_sharpness_changed,
            ),
            (
                "White Balance (K):",
                "white_balance",
                self.settings_manager.WB_MIN,
                self.settings_manager.WB_MAX,
                self._on_white_balance_changed,
            ),
        ]

        for i, (label, key, min_val, max_val, callback) in enumerate(controls):
            # Label
            ttk.Label(scrollable_frame, text=label).grid(
                row=i, column=0, sticky=tk.W, padx=2
            )

            # Variable
            var = tk.IntVar(value=self.settings_manager.get_setting(key))
            self.widgets[f"{key}_var"] = var

            # Scale
            scale = ttk.Scale(
                scrollable_frame,
                from_=min_val,
                to=max_val,
                variable=var,
                orient=tk.HORIZONTAL,
                length=150,
                command=lambda v, cb=callback, va=var: cb(int(va.get())),
            )
            scale.grid(row=i, column=1, sticky=tk.EW, padx=2)

            # Value label
            value_label = ttk.Label(scrollable_frame, textvariable=var, width=6)
            value_label.grid(row=i, column=2, padx=2)

        scrollable_frame.columnconfigure(1, weight=1)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _setup_advanced_controls(self):
        """Setup advanced camera controls"""
        advanced_frame = ttk.LabelFrame(self.parent, text="Advanced", padding=5)
        advanced_frame.pack(fill=tk.X, pady=(0, 10))

        # Denoise controls
        denoise_frame = ttk.Frame(advanced_frame)
        denoise_frame.pack(fill=tk.X)

        # Luma denoise
        ttk.Label(denoise_frame, text="Luma Denoise:").grid(
            row=0, column=0, sticky=tk.W
        )
        self.widgets["luma_denoise_var"] = tk.IntVar(
            value=self.settings_manager.get_setting("luma_denoise")
        )
        luma_scale = ttk.Scale(
            denoise_frame,
            from_=0,
            to=4,
            variable=self.widgets["luma_denoise_var"],
            orient=tk.HORIZONTAL,
            length=100,
            command=lambda v: self.settings_manager.set_luma_denoise(
                int(self.widgets["luma_denoise_var"].get())
            ),
        )
        luma_scale.grid(row=0, column=1, sticky=tk.EW)

        # Chroma denoise
        ttk.Label(denoise_frame, text="Chroma Denoise:").grid(
            row=1, column=0, sticky=tk.W
        )
        self.widgets["chroma_denoise_var"] = tk.IntVar(
            value=self.settings_manager.get_setting("chroma_denoise")
        )
        chroma_scale = ttk.Scale(
            denoise_frame,
            from_=0,
            to=4,
            variable=self.widgets["chroma_denoise_var"],
            orient=tk.HORIZONTAL,
            length=100,
            command=lambda v: self.settings_manager.set_chroma_denoise(
                int(self.widgets["chroma_denoise_var"].get())
            ),
        )
        chroma_scale.grid(row=1, column=1, sticky=tk.EW)

        denoise_frame.columnconfigure(1, weight=1)

        # Reset button
        ttk.Button(
            advanced_frame, text="Reset to Defaults", command=self._on_reset_settings
        ).pack(pady=5)

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
            settings = {
                "width": self.widgets["width_var"].get(),
                "height": self.widgets["height_var"].get(),
                "fps": self.widgets["fps_var"].get(),
            }
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
        self.widgets["width_var"].set(
            self.settings_manager.get_setting("resolution_width")
        )
        self.widgets["height_var"].set(
            self.settings_manager.get_setting("resolution_height")
        )
        self.widgets["fps_var"].set(self.settings_manager.get_setting("fps"))

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
