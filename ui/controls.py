import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from camera.settings import CameraSettingsManager


class QuickActionsMenu:
    """Handles the horizontal quick actions menu at the top"""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.widgets: Dict[str, Any] = {}

        # Callback functions
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_capture: Optional[Callable] = None
        self.on_record_toggle: Optional[Callable] = None
        self.on_capture_gps: Optional[Callable] = None
        self.on_toggle_gps_interval: Optional[Callable] = None
        self.on_save_dir_change: Optional[Callable] = None
        self.on_update_settings: Optional[Callable] = None
        self.on_reset_settings: Optional[Callable] = None

        self.setup_quick_actions()

    def setup_quick_actions(self):
        """Setup the horizontal quick actions menu"""
        # Main action frame with better styling
        action_frame = ttk.LabelFrame(self.parent, text="Quick Actions", padding=10)
        action_frame.pack(fill=tk.X, pady=(0, 10))

        # Top row - Main action buttons
        button_row = ttk.Frame(action_frame)
        button_row.pack(fill=tk.X, pady=(0, 5))

        # Connection buttons
        connection_frame = ttk.LabelFrame(button_row, text="Connection", padding=5)
        connection_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)

        self.widgets["connect_btn"] = ttk.Button(
            connection_frame,
            text="🔌 Connect",
            command=self._on_connect_clicked,
            width=12,
        )
        self.widgets["connect_btn"].pack(side=tk.LEFT, padx=2)

        self.widgets["disconnect_btn"] = ttk.Button(
            connection_frame,
            text="🔌 Disconnect",
            command=self._on_disconnect_clicked,
            width=12,
        )
        self.widgets["disconnect_btn"].pack(side=tk.LEFT, padx=2)

        # Capture buttons
        capture_frame = ttk.LabelFrame(button_row, text="Capture", padding=5)
        capture_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)

        self.widgets["capture_btn"] = ttk.Button(
            capture_frame,
            text="📷 Capture Images",
            command=self._on_capture_clicked,
            width=15,
        )
        self.widgets["capture_btn"].pack(side=tk.LEFT, padx=2)

        self.widgets["record_btn"] = ttk.Button(
            capture_frame,
            text="🎥 Start Recording",
            command=self._on_record_clicked,
            width=15,
        )
        self.widgets["record_btn"].pack(side=tk.LEFT, padx=2)

        # GPS capture button
        self.widgets["gps_btn"] = ttk.Button(
            capture_frame,
            text="📍 Capture GPS",
            command=self._on_capture_gps_clicked,
            width=15,
        )
        self.widgets["gps_btn"].pack(side=tk.LEFT, padx=2)

        # GPS interval capture toggle button
        self.widgets["gps_interval_btn"] = ttk.Button(
            capture_frame,
            text="▶ Start GPS Capture",
            command=self._on_toggle_gps_interval_clicked,
            width=18,
        )
        self.widgets["gps_interval_btn"].pack(side=tk.LEFT, padx=2)

        # Settings buttons
        settings_frame = ttk.LabelFrame(button_row, text="Settings", padding=5)
        settings_frame.pack(side=tk.LEFT, padx=(0, 10), fill=tk.Y)

        self.widgets["save_dir_btn"] = ttk.Button(
            settings_frame,
            text="📁 Save Directory",
            command=self._on_save_dir_clicked,
            width=15,
        )
        self.widgets["save_dir_btn"].pack(side=tk.LEFT, padx=2)

        self.widgets["update_settings_btn"] = ttk.Button(
            settings_frame,
            text="⚙️ Update Settings",
            command=self._on_update_settings_clicked,
            width=15,
        )
        self.widgets["update_settings_btn"].pack(side=tk.LEFT, padx=2)

        self.widgets["reset_btn"] = ttk.Button(
            settings_frame,
            text="🔄 Reset Settings",
            command=self._on_reset_clicked,
            width=15,
        )
        self.widgets["reset_btn"].pack(side=tk.LEFT, padx=2)

        # Status row - Information display
        status_row = ttk.Frame(action_frame)
        status_row.pack(fill=tk.X, pady=(5, 0))

        # Connection status
        self.widgets["connection_status_label"] = ttk.Label(
            status_row,
            text="● Disconnected",
            foreground="red",
            font=("Arial", 10, "bold"),
        )
        self.widgets["connection_status_label"].pack(side=tk.LEFT)

        # Recording status
        self.widgets["recording_status_label"] = ttk.Label(
            status_row, text="", foreground="green", font=("Arial", 10)
        )
        self.widgets["recording_status_label"].pack(side=tk.LEFT, padx=(20, 0))

        # Save directory display
        self.widgets["save_dir_label"] = ttk.Label(
            status_row, text="📁 ./captures", font=("Arial", 9), foreground="blue"
        )
        self.widgets["save_dir_label"].pack(side=tk.RIGHT)

        # Disk space info
        self.widgets["disk_space_label"] = ttk.Label(
            status_row, text="", font=("Arial", 9), foreground="gray"
        )
        self.widgets["disk_space_label"].pack(side=tk.RIGHT, padx=(0, 20))

    def set_callbacks(self, **callbacks):
        """Set callback functions for various events"""
        for name, callback in callbacks.items():
            if hasattr(self, f"on_{name}"):
                setattr(self, f"on_{name}", callback)

    # Event handlers
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

    def _on_capture_gps_clicked(self):
        if self.on_capture_gps:
            self.on_capture_gps()

    def _on_toggle_gps_interval_clicked(self):
        if self.on_toggle_gps_interval:
            self.on_toggle_gps_interval()

    def update_gps_interval_status(self, running: bool):
        """Update GPS interval capture toggle button text"""
        if running:
            self.widgets["gps_interval_btn"].config(text="⏹ Stop GPS Capture")
        else:
            self.widgets["gps_interval_btn"].config(text="▶ Start GPS Capture")

    def _on_save_dir_clicked(self):
        if self.on_save_dir_change:
            self.on_save_dir_change()

    def _on_update_settings_clicked(self):
        if self.on_update_settings:
            self.on_update_settings()

    def _on_reset_clicked(self):
        if self.on_reset_settings:
            self.on_reset_settings()

    # Status update methods
    def update_connection_status(self, connected: bool):
        """Update connection status display"""
        if connected:
            self.widgets["connection_status_label"].config(
                text="● Connected", foreground="green"
            )
            self.widgets["connect_btn"].config(state="disabled")
            self.widgets["disconnect_btn"].config(state="normal")
        else:
            self.widgets["connection_status_label"].config(
                text="● Disconnected", foreground="red"
            )
            self.widgets["connect_btn"].config(state="normal")
            self.widgets["disconnect_btn"].config(state="disabled")

    def update_recording_status(self, recording: bool, duration: float = 0.0):
        """Update recording status display"""
        if recording:
            self.widgets["record_btn"].config(text="⏹️ Stop Recording")
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            status_text = f"🔴 Recording {minutes:02d}:{seconds:02d}"
            self.widgets["recording_status_label"].config(
                text=status_text, foreground="red"
            )
        else:
            self.widgets["record_btn"].config(text="🎥 Start Recording")
            self.widgets["recording_status_label"].config(text="")

    def update_save_directory_display(self, directory: Path):
        """Update save directory display"""
        dir_str = str(directory)
        if len(dir_str) > 30:
            dir_str = "..." + dir_str[-27:]
        self.widgets["save_dir_label"].config(text=f"📁 {dir_str}")

    def update_disk_space_display(self, free_gb: float, total_gb: float):
        """Update disk space display"""
        percentage = (free_gb / total_gb) * 100 if total_gb > 0 else 0
        self.widgets["disk_space_label"].config(
            text=f"💾 {free_gb:.1f}GB free ({percentage:.0f}%)"
        )


class ControlPanel:
    """Manages the camera control UI panel (without actions - they're now in QuickActionsMenu)"""

    def __init__(self, parent: tk.Widget, settings_manager: "CameraSettingsManager"):
        self.parent = parent
        self.settings_manager = settings_manager
        self.widgets: Dict[str, Any] = {}

        # Callback functions (for settings only)
        self.on_settings_change: Optional[Callable] = None

        self.setup_controls()

    def setup_controls(self):
        """Setup all control widgets (without action buttons)"""
        self._setup_connection_info()
        self._setup_resolution_controls()
        self._setup_camera_settings_tabs()

    def _setup_connection_info(self):
        """Setup device information display"""
        info_frame = ttk.LabelFrame(self.parent, text="Device Info", padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.widgets["device_info_label"] = ttk.Label(
            info_frame, text="No device connected", font=("Arial", 9), justify=tk.LEFT
        )
        self.widgets["device_info_label"].pack(anchor=tk.W)

    def _setup_resolution_controls(self):
        """Setup resolution and FPS controls with compact layout"""
        res_frame = ttk.LabelFrame(self.parent, text="Stream Settings", padding=5)
        res_frame.pack(fill=tk.X, pady=(0, 10))

        # CAM_A Resolution section
        cam_a_section = ttk.Frame(res_frame)
        cam_a_section.pack(fill=tk.X, pady=2)

        ttk.Label(cam_a_section, text="CAM_A Resolution:", width=18).pack(side=tk.LEFT)

        # Allowed CAM_A resolutions
        self.cam_a_resolution_options = [
            "1024x768",
            "2048x1536",
            "4000x3000",
        ]

        # Default CAM_A resolution
        cam_a_default = "1024x768"
        if cam_a_default not in self.cam_a_resolution_options:
            self.cam_a_resolution_options.append(cam_a_default)

        self.widgets["cam_a_resolution_var"] = tk.StringVar(value=cam_a_default)
        cam_a_dropdown = ttk.Combobox(
            cam_a_section,
            textvariable=self.widgets["cam_a_resolution_var"],
            values=self.cam_a_resolution_options,
            state="readonly",
            width=14,
        )
        cam_a_dropdown.pack(side=tk.LEFT, padx=5)

        # CAM_B/C Resolution display (fixed)
        cam_bc_section = ttk.Frame(res_frame)
        cam_bc_section.pack(fill=tk.X, pady=2)
        ttk.Label(cam_bc_section, text="CAM_B/C Resolution:", width=18).pack(side=tk.LEFT)
        ttk.Label(cam_bc_section, text="1280x800 (fixed)").pack(side=tk.LEFT, padx=5)

        # FPS section
        fps_section = ttk.Frame(res_frame)
        fps_section.pack(fill=tk.X, pady=2)

        ttk.Label(fps_section, text="FPS:", width=12).pack(side=tk.LEFT)

        fps_options = ["5", "10", "15", "20", "25", "30", "45", "60"]
        current_fps = str(self.settings_manager.get_setting("fps"))
        if current_fps not in fps_options:
            fps_options.append(current_fps)

        self.widgets["fps_var"] = tk.StringVar(value=current_fps)
        fps_dropdown = ttk.Combobox(
            fps_section,
            textvariable=self.widgets["fps_var"],
            values=fps_options,
            state="readonly",
            width=8,
        )
        fps_dropdown.pack(side=tk.LEFT, padx=5)

        # Apply button
        apply_btn = ttk.Button(
            fps_section,
            text="Apply Settings",
            command=self._on_apply_stream_settings,
            width=15,
        )
        apply_btn.pack(side=tk.RIGHT)

    def _show_custom_resolution_dialog(self):
        """Show dialog for custom resolution input"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Custom Resolution")
        dialog.geometry("300x150")
        dialog.resizable(False, False)
        dialog.grab_set()

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

    def _setup_camera_settings_tabs(self):
        """Setup camera settings in tabbed interface"""
        settings_frame = ttk.LabelFrame(self.parent, text="Camera Settings", padding=5)
        settings_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

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
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Auto Controls Section
        auto_section = ttk.LabelFrame(
            scrollable_frame, text="Automatic Controls", padding=5
        )
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
        lock_section = ttk.LabelFrame(scrollable_frame, text="Lock Controls", padding=5)
        lock_section.pack(fill=tk.X, pady=(0, 10))

        self.widgets["ae_lock"] = tk.BooleanVar()
        ttk.Checkbutton(
            lock_section,
            text="Auto Exposure Lock",
            variable=self.widgets["ae_lock"],
            command=self._on_ae_lock_changed,
        ).pack(anchor=tk.W, pady=2)

        self.widgets["awb_lock"] = tk.BooleanVar()
        ttk.Checkbutton(
            lock_section,
            text="Auto White Balance Lock",
            variable=self.widgets["awb_lock"],
            command=self._on_awb_lock_changed,
        ).pack(anchor=tk.W, pady=2)

        # Manual Controls Section
        manual_section = ttk.LabelFrame(
            scrollable_frame, text="Manual Controls", padding=5
        )
        manual_section.pack(fill=tk.X, pady=(0, 10))

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
        trigger_section = ttk.LabelFrame(
            scrollable_frame, text="Trigger Controls", padding=5
        )
        trigger_section.pack(fill=tk.X)

        ttk.Button(
            trigger_section,
            text="Trigger AutoFocus",
            command=self._on_trigger_autofocus,
        ).pack(pady=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _setup_image_quality_tab(self, parent):
        """Setup image quality controls tab"""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Color Controls Section
        color_section = ttk.LabelFrame(
            scrollable_frame, text="Color Adjustments", padding=5
        )
        color_section.pack(fill=tk.X, pady=(0, 10))

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
            scrollable_frame, text="Image Enhancement", padding=5
        )
        enhancement_section.pack(fill=tk.X)

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

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _setup_advanced_tab(self, parent):
        """Setup advanced settings tab"""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Noise Reduction Section
        denoise_section = ttk.LabelFrame(
            scrollable_frame, text="Noise Reduction", padding=5
        )
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
        other_section = ttk.LabelFrame(
            scrollable_frame, text="Other Settings", padding=5
        )
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

        # GPS interval control (meters)
        gps_interval_frame = ttk.Frame(other_section)
        gps_interval_frame.pack(fill=tk.X, pady=2)
        ttk.Label(gps_interval_frame, text="GPS Interval (m):").pack(side=tk.LEFT)
        self.widgets["gps_interval_var"] = tk.DoubleVar(
            value=float(self.settings_manager.get_setting("gps_interval_m"))
        )
        gps_spin = ttk.Spinbox(
            gps_interval_frame,
            from_=0.1,
            to=100.0,
            increment=0.1,
            textvariable=self.widgets["gps_interval_var"],
            width=8,
            command=lambda: self._on_gps_interval_changed(),
        )
        gps_spin.pack(side=tk.LEFT, padx=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _setup_manual_controls_in_frame(self, parent, controls):
        """Setup manual controls with sliders in a given frame"""
        for i, (label, key, min_val, max_val, callback) in enumerate(controls):
            # Control frame
            control_frame = ttk.Frame(parent)
            control_frame.pack(fill=tk.X, pady=2)

            # Label
            ttk.Label(control_frame, text=label, width=15).pack(side=tk.LEFT)

            # Variable - ensure integer value
            setting_value = self.settings_manager.get_setting(key)
            var = tk.IntVar(value=int(setting_value) if setting_value is not None else 0)
            self.widgets[f"{key}_var"] = var

            # Scale
            scale = ttk.Scale(
                control_frame,
                from_=min_val,
                to=max_val,
                variable=var,
                orient=tk.HORIZONTAL,
                length=150,
                command=lambda v, k=key, va=var: self._on_manual_control_changed(k, int(va.get())),
            )
            scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

            # Value label
            value_label = ttk.Label(control_frame, textvariable=var, width=6)
            value_label.pack(side=tk.RIGHT)

    def _on_apply_stream_settings(self):
        """Apply stream settings"""
        if self.on_settings_change:
            # Parse CAM_A resolution
            cam_a_res = self.widgets["cam_a_resolution_var"].get()
            if "x" not in cam_a_res:
                tk.messagebox.showerror(
                    "Invalid Resolution", "Please select a valid CAM_A resolution"
                )
                return
            cam_a_w_str, cam_a_h_str = cam_a_res.split("x")
            try:
                cam_a_w = int(cam_a_w_str.strip())
                cam_a_h = int(cam_a_h_str.strip())
            except ValueError:
                tk.messagebox.showerror(
                    "Invalid Resolution", "Please select a valid CAM_A resolution"
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

            settings = {
                "fps": fps,
                # For backward compatibility
                "width": cam_a_w,
                "height": cam_a_h,
                # Per-camera resolutions
                "per_camera_resolutions": {
                    "CAM_A": (cam_a_w, cam_a_h),
                    "CAM_B": (1280, 800),
                    "CAM_C": (1280, 800),
                },
            }
            self.on_settings_change(settings)

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

    def _on_manual_control_changed(self, key: str, value: int):
        """Handle manual control changes - only update settings, don't apply to camera"""
        self.settings_manager.update_setting(key, value)

    def _on_gps_interval_changed(self):
        try:
            val = float(self.widgets["gps_interval_var"].get())
            if val <= 0:
                val = 1.0
            self.settings_manager.update_setting("gps_interval_m", val)
        except Exception:
            pass

    # Public interface methods
    def set_callbacks(self, **callbacks):
        """Set callback functions for various events"""
        for name, callback in callbacks.items():
            if hasattr(self, f"on_{name}"):
                setattr(self, f"on_{name}", callback)

    def update_device_info(self, device_info: Optional[Dict] = None):
        """Update device information display"""
        if device_info:
            info_text = f"Platform: {device_info.get('platform', 'Unknown')}\n"
            info_text += f"Cameras: {device_info.get('connected_cameras', 0)}"
            self.widgets["device_info_label"].config(text=info_text)
        else:
            self.widgets["device_info_label"].config(text="No device connected")

    def update_all_widgets(self):
        """Update all widget values from settings manager"""
        # Update auto mode checkboxes
        if "auto_exposure" in self.widgets:
            self.widgets["auto_exposure"].set(
                self.settings_manager.get_auto_mode("auto_exposure")
            )
        if "auto_focus" in self.widgets:
            self.widgets["auto_focus"].set(
                self.settings_manager.get_auto_mode("auto_focus")
            )
        if "auto_wb" in self.widgets:
            self.widgets["auto_wb"].set(
                self.settings_manager.get_auto_mode("auto_white_balance")
            )
        if "ae_lock" in self.widgets:
            self.widgets["ae_lock"].set(
                self.settings_manager.get_auto_mode("auto_exposure_lock")
            )
        if "awb_lock" in self.widgets:
            self.widgets["awb_lock"].set(
                self.settings_manager.get_auto_mode("auto_white_balance_lock")
            )

        # Update manual control values - ensure integer values
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
                setting_value = self.settings_manager.get_setting(control)
                self.widgets[var_key].set(int(setting_value) if setting_value is not None else 0)

        # Update CAM_A resolution (keep default if not set yet)
        if "cam_a_resolution_var" in self.widgets:
            # Try to infer from settings manager, else keep current
            width = self.settings_manager.get_setting("resolution_width")
            height = self.settings_manager.get_setting("resolution_height")
            res_str = f"{width}x{height}"
            if res_str in getattr(self, "cam_a_resolution_options", []):
                self.widgets["cam_a_resolution_var"].set(res_str)

        # Update FPS
        if "fps_var" in self.widgets:
            self.widgets["fps_var"].set(str(self.settings_manager.get_setting("fps")))

    def get_current_settings(self) -> Dict[str, Any]:
        """Get current resolution and FPS settings"""
        settings = {}
        # CAM_A resolution
        cam_a_res = self.widgets.get("cam_a_resolution_var")
        if cam_a_res:
            res_str = cam_a_res.get()
            if "x" in res_str:
                w_str, h_str = res_str.split("x")
                try:
                    cam_a_w = int(w_str.strip())
                    cam_a_h = int(h_str.strip())
                except ValueError:
                    cam_a_w, cam_a_h = 1024, 768
            else:
                cam_a_w, cam_a_h = 1024, 768
        else:
            cam_a_w, cam_a_h = 1024, 768

        # Backward compatible top-level size (use CAM_A)
        settings["width"], settings["height"] = cam_a_w, cam_a_h

        # Per-camera mapping
        settings["per_camera_resolutions"] = {
            "CAM_A": (cam_a_w, cam_a_h),
            "CAM_B": (1280, 800),
            "CAM_C": (1280, 800),
        }

        if "fps_var" in self.widgets:
            try:
                settings["fps"] = int(self.widgets["fps_var"].get())
            except ValueError:
                settings["fps"] = 30
        else:
            settings["fps"] = 30

        return settings
