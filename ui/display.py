import cv2
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import numpy as np
from PIL import Image, ImageTk
from typing import Dict, Optional, TYPE_CHECKING, Callable
from pathlib import Path

if TYPE_CHECKING:
    from camera.controller import CameraController
    from utils.file_manager import FileManager


class MenuBarManager:
    """Manages the application menu bar"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.menubar = tk.Menu(root)
        root.config(menu=self.menubar)

        # Callback functions
        self.on_open_save_dir: Optional[Callable] = None
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_capture: Optional[Callable] = None
        self.on_record_toggle: Optional[Callable] = None
        self.on_reset_settings: Optional[Callable] = None
        self.on_refresh_displays: Optional[Callable] = None
        self.on_show_shortcuts: Optional[Callable] = None
        self.on_show_about: Optional[Callable] = None
        self.on_exit: Optional[Callable] = None

        self.setup_menus()

    def setup_menus(self):
        """Setup all menu items"""
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="Open Save Directory", command=self._on_open_save_dir
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit)

        # Camera menu
        camera_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Camera", menu=camera_menu)
        camera_menu.add_command(label="Connect", command=self._on_connect)
        camera_menu.add_command(label="Disconnect", command=self._on_disconnect)
        camera_menu.add_separator()
        camera_menu.add_command(label="Capture Images", command=self._on_capture)
        camera_menu.add_command(
            label="Toggle Recording", command=self._on_record_toggle
        )
        camera_menu.add_separator()
        camera_menu.add_command(label="Reset Settings", command=self._on_reset_settings)

        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(
            label="Refresh Displays", command=self._on_refresh_displays
        )

        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(
            label="Keyboard Shortcuts", command=self._on_show_shortcuts
        )
        help_menu.add_command(label="About", command=self._on_show_about)

    def set_callbacks(self, **callbacks):
        """Set callback functions for menu actions"""
        for name, callback in callbacks.items():
            if hasattr(self, f"on_{name}"):
                setattr(self, f"on_{name}", callback)

    # Menu event handlers
    def _on_open_save_dir(self):
        if self.on_open_save_dir:
            self.on_open_save_dir()

    def _on_connect(self):
        if self.on_connect:
            self.on_connect()

    def _on_disconnect(self):
        if self.on_disconnect:
            self.on_disconnect()

    def _on_capture(self):
        if self.on_capture:
            self.on_capture()

    def _on_record_toggle(self):
        if self.on_record_toggle:
            self.on_record_toggle()

    def _on_reset_settings(self):
        if self.on_reset_settings:
            self.on_reset_settings()

    def _on_refresh_displays(self):
        if self.on_refresh_displays:
            self.on_refresh_displays()

    def _on_show_shortcuts(self):
        if self.on_show_shortcuts:
            self.on_show_shortcuts()
        else:
            self._default_show_shortcuts()

    def _on_show_about(self):
        if self.on_show_about:
            self.on_show_about()
        else:
            self._default_show_about()

    def _on_exit(self):
        if self.on_exit:
            self.on_exit()
        else:
            self.root.quit()

    def _default_show_shortcuts(self):
        """Default keyboard shortcuts dialog"""
        shortcuts_text = """Keyboard Shortcuts:
        
Ctrl+C - Capture Images
Ctrl+R - Toggle Recording
Ctrl+N - Connect Camera
Ctrl+D - Disconnect Camera
Ctrl+Q - Quit Application
F5 - Refresh Displays

Mouse Controls:
- Click tabs to switch between cameras
- Adjust sliders for camera settings
- Use dropdown menus for resolution/FPS"""

        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)

    def _default_show_about(self):
        """Default about dialog"""
        about_text = """OAK PoE Camera Viewer
        
Version: 1.0.0
Built with DepthAI V3

A comprehensive camera viewer for Luxonis OAK PoE devices.

Features:
• Multi-camera display (CAM_A, CAM_B, CAM_C)
• Complete camera controls with tabbed interface
• Image capture and video recording
• Real-time settings adjustment
• Horizontal quick action menu
• Keyboard shortcuts

© 2024 - Built with Python and DepthAI"""

        messagebox.showinfo("About", about_text)


class StatusBarManager:
    """Manages the application status bar"""

    def __init__(self, parent: tk.Widget):
        self.parent = parent
        self.status_bar = ttk.Frame(parent)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        self.status_text = ttk.Label(self.status_bar, text="Ready", relief=tk.SUNKEN)
        self.status_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # FPS display
        self.fps_label = ttk.Label(self.status_bar, text="FPS: 0.0", relief=tk.SUNKEN)
        self.fps_label.pack(side=tk.RIGHT, padx=5)

    def update_status(self, message: str):
        """Update status bar message"""
        timestamp = time.strftime("%H:%M:%S")
        self.status_text.config(text=f"[{timestamp}] {message}")

    def update_fps(self, fps: float):
        """Update FPS display"""
        self.fps_label.config(text=f"FPS: {fps:.1f}")


class DisplayManager:
    """Manages camera display and UI updates"""

    def __init__(self, notebook: ttk.Notebook):
        self.notebook = notebook
        self.camera_frames: Dict[str, ttk.Label] = {}
        self.camera_info_labels: Dict[str, ttk.Label] = {}
        self.display_thread: Optional[threading.Thread] = None
        self.running = False

        # Display settings
        self.display_width = 640
        self.target_fps = 30
        # Per-camera FPS tracking
        self._camera_frame_counts: Dict[str, int] = {}
        self._camera_last_update: Dict[str, float] = {}
        self._camera_current_fps: Dict[str, float] = {}

    def setup_camera_tab(self, camera_name: str):
        """Setup display tab for a camera"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=camera_name)

        # Main container for camera content
        content_frame = ttk.Frame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Info panel at top
        info_frame = ttk.Frame(content_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # Camera info label
        info_label = ttk.Label(
            info_frame, text=f"Camera {camera_name} - No Image", font=("Arial", 10)
        )
        info_label.pack(side=tk.LEFT)
        self.camera_info_labels[camera_name] = info_label

        # FPS display
        fps_label = ttk.Label(info_frame, text="FPS: 0.0", font=("Arial", 10))
        fps_label.pack(side=tk.RIGHT)

        # Image display area
        image_frame = ttk.Frame(content_frame, relief=tk.SUNKEN, borderwidth=2)
        image_frame.pack(fill=tk.BOTH, expand=True)

        # Create label for image display
        image_label = ttk.Label(
            image_frame,
            text=f"Camera {camera_name}\nWaiting for frames...",
            anchor=tk.CENTER,
            justify=tk.CENTER,
        )
        image_label.pack(expand=True)

        self.camera_frames[camera_name] = image_label

        # Store fps label reference for updates
        self.camera_frames[f"{camera_name}_fps"] = fps_label

    def update_camera_display(
        self, camera_name: str, image: np.ndarray, frame_info: Optional[Dict] = None
    ):
        """Update camera display with new image and info"""
        try:
            # Convert BGR to RGB
            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Calculate display size maintaining aspect ratio
            original_height, original_width = img_rgb.shape[:2]
            display_height = int(original_height * self.display_width / original_width)

            # Resize for display
            img_display = cv2.resize(img_rgb, (self.display_width, display_height))

            # Convert to PhotoImage
            pil_image = Image.fromarray(img_display)
            photo = ImageTk.PhotoImage(pil_image)

            # Update display
            if camera_name in self.camera_frames:
                self.camera_frames[camera_name].config(image=photo, text="")
                self.camera_frames[camera_name].image = photo  # Keep reference

                # Update info label
                info_text = f"Camera {camera_name} - {original_width}x{original_height}"
                if frame_info:
                    if "exposure" in frame_info:
                        info_text += f" | Exp: {frame_info['exposure']}μs"
                    if "sequence" in frame_info:
                        info_text += f" | Frame: {frame_info['sequence']}"

                if camera_name in self.camera_info_labels:
                    self.camera_info_labels[camera_name].config(text=info_text)

                # Update FPS
                self._update_fps_display(camera_name)

        except Exception as e:
            print(f"Display update error for {camera_name}: {e}")

    def _update_fps_display(self, camera_name: str):
        """Update FPS display for camera (per-camera measurement)"""
        try:
            current_time = time.time()
            # Initialize counters for this camera if needed
            if camera_name not in self._camera_frame_counts:
                self._camera_frame_counts[camera_name] = 0
                self._camera_last_update[camera_name] = current_time
                self._camera_current_fps[camera_name] = 0.0

            self._camera_frame_counts[camera_name] += 1

            # Update per-camera FPS every second
            elapsed = current_time - self._camera_last_update[camera_name]
            if elapsed >= 1.0:
                fps = self._camera_frame_counts[camera_name] / max(elapsed, 1e-6)
                self._camera_current_fps[camera_name] = fps
                self._camera_frame_counts[camera_name] = 0
                self._camera_last_update[camera_name] = current_time

                # Update FPS label for this camera
                fps_label_key = f"{camera_name}_fps"
                if fps_label_key in self.camera_frames:
                    self.camera_frames[fps_label_key].config(
                        text=f"FPS: {fps:.1f}"
                    )
        except Exception as e:
            print(f"FPS update error: {e}")

    def clear_displays(self):
        """Clear all camera displays"""
        for child in self.notebook.tabs():
            self.notebook.forget(child)
        self.camera_frames.clear()
        self.camera_info_labels.clear()

    def start_display_loop(
        self, camera_controller: "CameraController", file_manager: "FileManager", roi_manager=None
    ):
        """Start the display update loop"""
        if self.running:
            return

        self.running = True
        self.display_thread = threading.Thread(
            target=self._display_loop,
            args=(camera_controller, file_manager, roi_manager),
            daemon=True,
        )
        self.display_thread.start()

    def stop_display_loop(self):
        """Stop the display update loop"""
        self.running = False
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=1.0)

    def _display_loop(
        self, camera_controller: "CameraController", file_manager: "FileManager", roi_manager=None
    ):
        """Main display loop"""
        frame_interval = 1.0 / self.target_fps

        while self.running:
            loop_start = time.time()

            try:
                for camera_name in camera_controller.get_connected_cameras():
                    frame = camera_controller.get_frame(camera_name)
                    if frame is not None:
                        # Apply ROI overlay if available
                        if roi_manager:
                            frame = roi_manager.draw_roi_overlay(frame, camera_name)
                        
                        # Get frame info if available
                        frame_info = {
                            "width": frame.shape[1],
                            "height": frame.shape[0],
                            "channels": frame.shape[2] if len(frame.shape) > 2 else 1,
                        }

                        # Update display
                        self.update_camera_display(camera_name, frame, frame_info)

                        # Write to video if recording
                        if file_manager.is_recording():
                            file_manager.write_video_frame(camera_name, frame)

                # Maintain target FPS
                elapsed = time.time() - loop_start
                sleep_time = max(0, frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except Exception as e:
                print(f"Display loop error: {e}")
                time.sleep(0.1)

    def set_display_width(self, width: int):
        """Set display width for all cameras"""
        self.display_width = max(
            320, min(width, 1920)
        )  # Clamp between reasonable values

    def get_current_fps(self) -> float:
        """Get average display FPS across cameras"""
        if not self._camera_current_fps:
            return 0.0
        try:
            return sum(self._camera_current_fps.values()) / len(
                self._camera_current_fps
            )
        except Exception:
            return 0.0

    def take_screenshot(self, camera_name: str) -> Optional[np.ndarray]:
        """Take a screenshot of currently displayed frame"""
        if camera_name in self.camera_frames:
            try:
                # This would require getting the actual frame data
                # For now, we'll return None and handle screenshots differently
                return None
            except Exception as e:
                print(f"Screenshot error: {e}")
        return None

    def show_error_on_camera(self, camera_name: str, error_message: str):
        """Show error message on camera display"""
        if camera_name in self.camera_frames:
            self.camera_frames[camera_name].config(
                text=f"Camera {camera_name}\nError: {error_message}", image=""
            )
            self.camera_frames[camera_name].image = None

    def show_no_signal(self, camera_name: str):
        """Show no signal message on camera display"""
        if camera_name in self.camera_frames:
            self.camera_frames[camera_name].config(
                text=f"Camera {camera_name}\nNo Signal", image=""
            )
            self.camera_frames[camera_name].image = None


class UIManager:
    """Main UI Manager that coordinates all UI components"""

    def __init__(self, root: tk.Tk):
        self.root = root

        # UI Components
        self.menu_bar: Optional[MenuBarManager] = None
        self.status_bar: Optional[StatusBarManager] = None
        self.display_manager: Optional[DisplayManager] = None

        # Main UI containers
        self.main_frame: Optional[ttk.Frame] = None
        self.top_frame: Optional[ttk.Frame] = None
        self.paned_window: Optional[ttk.PanedWindow] = None
        self.control_frame: Optional[ttk.LabelFrame] = None
        self.control_notebook: Optional[ttk.Notebook] = None
        self.display_frame: Optional[ttk.Frame] = None
        self.notebook: Optional[ttk.Notebook] = None

    def setup_main_ui(self):
        """Setup the main UI structure"""
        # Configure style
        style = ttk.Style()
        style.theme_use("clam")

        # Setup menu bar
        self.menu_bar = MenuBarManager(self.root)

        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top section for quick actions
        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=(0, 10))

        # Create paned window for resizable panels
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel for controls with notebook
        self.control_frame = ttk.LabelFrame(
            self.paned_window, text="Camera Controls", padding=10
        )
        self.control_frame.configure(width=350)
        self.paned_window.add(self.control_frame, weight=0)
        
        # Create notebook for control panels
        self.control_notebook = ttk.Notebook(self.control_frame)
        self.control_notebook.pack(fill=tk.BOTH, expand=True)

        # Right panel for camera displays
        self.display_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.display_frame, weight=1)

        # Setup display area
        self.notebook = ttk.Notebook(self.display_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.display_manager = DisplayManager(self.notebook)

        # Setup status bar
        self.status_bar = StatusBarManager(self.root)

    def get_top_frame(self) -> ttk.Frame:
        """Get the top frame for quick actions menu"""
        return self.top_frame

    def get_control_frame(self) -> ttk.LabelFrame:
        """Get the control frame for camera controls"""
        return self.control_frame

    def get_control_notebook(self) -> ttk.Notebook:
        """Get the control notebook for multiple control panels"""
        return self.control_notebook

    def get_display_manager(self) -> DisplayManager:
        """Get the display manager"""
        return self.display_manager

    def get_menu_bar(self) -> MenuBarManager:
        """Get the menu bar manager"""
        return self.menu_bar

    def get_status_bar(self) -> StatusBarManager:
        """Get the status bar manager"""
        return self.status_bar

    def setup_keyboard_shortcuts(self, shortcuts: Dict[str, Callable]):
        """Setup keyboard shortcuts"""
        for key_combo, callback in shortcuts.items():
            self.root.bind(key_combo, lambda e, cb=callback: cb())

    def set_window_properties(self, title: str, geometry: str, min_size: tuple = None):
        """Set window properties"""
        self.root.title(title)
        self.root.geometry(geometry)
        if min_size:
            self.root.minsize(*min_size)

    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")

    def set_close_handler(self, handler: Callable):
        """Set window close handler"""
        self.root.protocol("WM_DELETE_WINDOW", handler)
