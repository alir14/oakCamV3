import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from pathlib import Path
from typing import Dict, Optional

# Import our custom modules
from camera.controller import CameraController
from camera.settings import CameraSettingsManager
from utils.file_manager import FileManager
from ui.display import DisplayManager
from ui.controls import ControlPanel


class OAKCameraViewer:
    """Main application class that orchestrates all components"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("OAK PoE Camera Viewer - DepthAI V3")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # Initialize components
        self.camera_controller = CameraController()
        self.settings_manager = CameraSettingsManager(self.camera_controller)
        self.file_manager = FileManager()

        # UI components (will be initialized in setup_ui)
        self.control_panel: Optional[ControlPanel] = None
        self.display_manager: Optional[DisplayManager] = None
        self.notebook: Optional[ttk.Notebook] = None

        # Application state
        self.connected = False
        self.status_thread: Optional[threading.Thread] = None
        self.status_running = False

        # Setup UI and event handlers
        self.setup_ui()
        self.setup_event_handlers()

        # Start status monitoring
        self.start_status_monitoring()

    def setup_ui(self):
        """Setup the main user interface"""
        # Configure style
        style = ttk.Style()
        style.theme_use("clam")  # Modern looking theme

        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create paned window for resizable panels
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel for controls (fixed width)
        control_frame = ttk.LabelFrame(paned_window, text="Camera Controls", padding=10)
        control_frame.configure(width=300)
        paned_window.add(control_frame, weight=0)

        # Right panel for camera displays (expandable)
        display_frame = ttk.Frame(paned_window)
        paned_window.add(display_frame, weight=1)

        # Setup control panel
        self.control_panel = ControlPanel(control_frame, self.settings_manager)

        # Setup display area
        self.notebook = ttk.Notebook(display_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.display_manager = DisplayManager(self.notebook)

        # Add menu bar
        self.setup_menu_bar()

        # Add status bar
        self.setup_status_bar()

    def setup_menu_bar(self):
        """Setup application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="Open Save Directory", command=self.open_save_directory
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Camera menu
        camera_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Camera", menu=camera_menu)
        camera_menu.add_command(label="Connect", command=self.connect_camera)
        camera_menu.add_command(label="Disconnect", command=self.disconnect_camera)
        camera_menu.add_separator()
        camera_menu.add_command(
            label="Reset Settings", command=self.reset_camera_settings
        )

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Displays", command=self.refresh_displays)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_status_bar(self):
        """Setup status bar at bottom"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        self.status_text = ttk.Label(self.status_bar, text="Ready", relief=tk.SUNKEN)
        self.status_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Recording indicator
        self.recording_indicator = ttk.Label(self.status_bar, text="", relief=tk.SUNKEN)
        self.recording_indicator.pack(side=tk.RIGHT, padx=5)

    def setup_event_handlers(self):
        """Setup event handlers for UI components"""
        if self.control_panel:
            self.control_panel.set_callbacks(
                connect=self.connect_camera,
                disconnect=self.disconnect_camera,
                capture=self.capture_images,
                record_toggle=self.toggle_recording,
                save_dir_change=self.set_save_directory,
                settings_change=self.apply_stream_settings,
            )

        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Keyboard shortcuts
        self.root.bind("<Control-c>", lambda e: self.capture_images())
        self.root.bind("<Control-r>", lambda e: self.toggle_recording())
        self.root.bind("<Control-q>", lambda e: self.on_closing())
        self.root.bind("<F5>", lambda e: self.refresh_displays())

    def start_status_monitoring(self):
        """Start background status monitoring"""
        self.status_running = True
        self.status_thread = threading.Thread(
            target=self._status_monitoring_loop, daemon=True
        )
        self.status_thread.start()

    def _status_monitoring_loop(self):
        """Background loop for status monitoring"""
        while self.status_running:
            try:
                # Update disk space info
                if self.control_panel:
                    free_gb, total_gb = self.file_manager.get_available_space()
                    self.root.after(
                        0,
                        lambda: self.control_panel.update_disk_space_display(
                            free_gb, total_gb
                        ),
                    )

                # Update recording duration
                if self.file_manager.is_recording():
                    duration = self.file_manager.get_recording_duration()
                    self.root.after(
                        0,
                        lambda: self.control_panel.update_recording_duration(duration),
                    )
                    self.root.after(
                        0, lambda: self.update_status(f"Recording... {duration:.1f}s")
                    )

                time.sleep(1.0)  # Update every second

            except Exception as e:
                print(f"Status monitoring error: {e}")
                time.sleep(5.0)

    def connect_camera(self):
        """Connect to the camera"""
        if self.connected:
            self.update_status("Already connected")
            return

        self.update_status("Connecting to camera...")

        # Run connection in separate thread to avoid blocking UI
        threading.Thread(target=self._connect_camera_thread, daemon=True).start()

    def _connect_camera_thread(self):
        """Connection thread to avoid blocking UI"""
        try:
            print("Attempting to connect to OAK camera...")
            success, message = self.camera_controller.connect()
            if not success:
                print(f"Connection failed: {message}")
                self.root.after(
                    0, lambda: messagebox.showerror("Connection Error", message)
                )
                self.root.after(0, lambda: self.update_status("Connection failed"))
                return

            print(f"Connection successful: {message}")

            # Setup pipeline with current settings
            width = self.control_panel.widgets["width_var"].get()
            height = self.control_panel.widgets["height_var"].get()
            fps = self.control_panel.widgets["fps_var"].get()

            print(f"Setting up pipeline: {width}x{height}@{fps}fps")

            if not self.camera_controller.setup_pipeline(width, height, fps):
                error_msg = (
                    "Failed to setup camera pipeline. Check console for details."
                )
                print("Pipeline setup failed")
                self.root.after(
                    0, lambda: messagebox.showerror("Pipeline Error", error_msg)
                )
                self.root.after(0, lambda: self.update_status("Pipeline setup failed"))
                return

            print("Pipeline setup successful")

            # Setup display tabs for connected cameras
            def setup_displays():
                connected_cameras = self.camera_controller.get_connected_cameras()
                print(f"Setting up display tabs for: {connected_cameras}")
                for camera_name in connected_cameras:
                    self.display_manager.setup_camera_tab(camera_name)

            self.root.after(0, setup_displays)

            # Start streaming
            print("Starting camera streaming...")
            if not self.camera_controller.start_streaming():
                error_msg = (
                    "Failed to start camera streaming. Check console for details."
                )
                print("Streaming failed to start")
                self.root.after(
                    0, lambda: messagebox.showerror("Streaming Error", error_msg)
                )
                self.root.after(0, lambda: self.update_status("Streaming failed"))
                return

            print("Streaming started successfully")

            # Start display updates
            self.display_manager.start_display_loop(
                self.camera_controller, self.file_manager
            )

            # Update UI state
            self.connected = True
            device_info = self.camera_controller.get_device_info()
            print(f"Device info: {device_info}")

            def update_ui():
                self.control_panel.update_connection_status(True, device_info)
                self.update_status("Connected successfully")
                messagebox.showinfo("Success", message)

            self.root.after(0, update_ui)

        except Exception as e:
            error_msg = f"Unexpected connection error: {str(e)}"
            print(f"Exception during connection: {e}")
            import traceback

            traceback.print_exc()
            self.root.after(
                0, lambda: messagebox.showerror("Connection Error", error_msg)
            )
            self.root.after(0, lambda: self.update_status("Connection error"))

    def disconnect_camera(self):
        """Disconnect from camera"""
        if not self.connected:
            self.update_status("Not connected")
            return

        self.update_status("Disconnecting...")

        # Stop recording if active
        if self.file_manager.is_recording():
            success, message, _ = self.file_manager.stop_video_recording()
            if self.control_panel:
                self.control_panel.update_record_button(False)

        # Stop display updates
        if self.display_manager:
            self.display_manager.stop_display_loop()

        # Disconnect camera
        self.camera_controller.disconnect()

        # Clear displays
        if self.display_manager:
            self.display_manager.clear_displays()

        # Update UI state
        self.connected = False
        if self.control_panel:
            self.control_panel.update_connection_status(False)

        self.update_status("Disconnected")

    def capture_images(self):
        """Capture images from all cameras"""
        if not self.connected:
            messagebox.showwarning("Warning", "No cameras connected")
            return

        self.update_status("Capturing images...")

        # Collect frames from all cameras
        images = {}
        for camera_name in self.camera_controller.get_connected_cameras():
            frame = self.camera_controller.get_frame(camera_name)
            if frame is not None:
                images[camera_name] = frame

        if not images:
            messagebox.showwarning("Warning", "No frames available for capture")
            self.update_status("Capture failed - no frames")
            return

        # Capture batch
        success_count, filepaths = self.file_manager.capture_images_batch(images)

        if success_count > 0:
            messagebox.showinfo(
                "Success",
                f"Captured {success_count} images\nSaved to: {self.file_manager.save_directory}",
            )
            self.update_status(f"Captured {success_count} images")
        else:
            messagebox.showerror("Error", "Failed to capture any images")
            self.update_status("Capture failed")

    def toggle_recording(self):
        """Toggle video recording"""
        if not self.connected:
            messagebox.showwarning("Warning", "No cameras connected")
            return

        if self.file_manager.is_recording():
            # Stop recording
            success, message, filepaths = self.file_manager.stop_video_recording()
            if self.control_panel:
                self.control_panel.update_record_button(False)

            if success:
                messagebox.showinfo(
                    "Success",
                    f"Recording stopped\n{message}\nSaved to: {self.file_manager.save_directory}",
                )
                self.update_status("Recording stopped")
            else:
                messagebox.showerror("Error", f"Error stopping recording: {message}")
        else:
            # Start recording
            camera_names = self.camera_controller.get_connected_cameras()
            if not camera_names:
                messagebox.showwarning("Warning", "No cameras available")
                return

            width = self.control_panel.widgets["width_var"].get()
            height = self.control_panel.widgets["height_var"].get()
            fps = self.control_panel.widgets["fps_var"].get()

            success, message = self.file_manager.start_video_recording(
                camera_names, width, height, fps
            )

            if success:
                if self.control_panel:
                    self.control_panel.update_record_button(True)
                self.update_status("Recording started")
            else:
                messagebox.showerror("Error", f"Failed to start recording: {message}")
                self.update_status("Recording failed to start")

    def set_save_directory(self):
        """Set the save directory for captures"""
        from tkinter import filedialog

        directory = filedialog.askdirectory(
            title="Select Save Directory", initialdir=self.file_manager.save_directory
        )

        if directory:
            success = self.file_manager.set_save_directory(Path(directory))
            if success and self.control_panel:
                self.control_panel.update_save_directory_display(
                    self.file_manager.save_directory
                )
                self.update_status(f"Save directory updated: {directory}")
            else:
                messagebox.showerror("Error", "Failed to set save directory")

    def apply_stream_settings(self, settings: Dict):
        """Apply new stream settings (requires reconnection)"""
        if self.connected:
            result = messagebox.askyesno(
                "Settings Change",
                "Changing stream settings requires reconnecting the camera. Continue?",
            )
            if result:
                # Update settings
                self.settings_manager.update_setting(
                    "resolution_width", settings["width"]
                )
                self.settings_manager.update_setting(
                    "resolution_height", settings["height"]
                )
                self.settings_manager.update_setting("fps", settings["fps"])

                # Reconnect
                self.disconnect_camera()
                time.sleep(1)  # Brief pause
                self.connect_camera()

    def reset_camera_settings(self):
        """Reset all camera settings to defaults"""
        if messagebox.askyesno(
            "Reset Settings", "Reset all camera settings to defaults?"
        ):
            self.settings_manager.reset_to_defaults()
            if self.control_panel:
                self.control_panel._update_all_widgets()
            self.update_status("Settings reset to defaults")

    def refresh_displays(self):
        """Refresh camera displays"""
        if self.connected and self.display_manager:
            # Clear and recreate displays
            self.display_manager.clear_displays()
            for camera_name in self.camera_controller.get_connected_cameras():
                self.display_manager.setup_camera_tab(camera_name)
            self.update_status("Displays refreshed")

    def open_save_directory(self):
        """Open the save directory in file explorer"""
        import subprocess
        import platform

        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(self.file_manager.save_directory)])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(self.file_manager.save_directory)])
            else:  # Linux
                subprocess.run(["xdg-open", str(self.file_manager.save_directory)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory: {e}")

    def update_status(self, message: str):
        """Update status bar message"""
        if hasattr(self, "status_text"):
            timestamp = time.strftime("%H:%M:%S")
            self.status_text.config(text=f"[{timestamp}] {message}")

    def show_about(self):
        """Show about dialog"""
        about_text = """OAK PoE Camera Viewer
        
Version: 1.0.0
Built with DepthAI V3

A comprehensive camera viewer for Luxonis OAK PoE devices.

Features:
• Multi-camera display (CAM_A, CAM_B, CAM_C)
• Complete camera controls
• Image capture
• Video recording
• Real-time settings adjustment

© 2024 - Built with Python and DepthAI"""

        messagebox.showinfo("About", about_text)

    def on_closing(self):
        """Handle application closing"""
        if self.file_manager.is_recording():
            result = messagebox.askyesnocancel(
                "Recording Active",
                "Video recording is active. Stop recording before closing?",
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes - stop recording
                self.file_manager.stop_video_recording()

        # Stop all operations
        self.status_running = False
        self.disconnect_camera()

        # Cleanup
        if self.file_manager:
            self.file_manager.cleanup()

        self.root.quit()
        self.root.destroy()

    def handle_error(self, error_message: str, title: str = "Error"):
        """Handle application errors"""
        print(f"Error: {error_message}")
        messagebox.showerror(title, error_message)
        self.update_status(f"Error: {error_message}")


def check_dependencies():
    """Check for required dependencies"""
    missing_deps = []

    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")

    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")

    try:
        import depthai as dai
    except ImportError:
        missing_deps.append("depthai")

    if missing_deps:
        deps_str = ", ".join(missing_deps)
        print(f"Missing dependencies: {deps_str}")
        print("Install with: pip install " + " ".join(missing_deps))
        return False

    return True


def main():
    """Main application entry point"""

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Create and configure root window
    root = tk.Tk()

    # Set window icon (if available)
    try:
        # You can add an icon file here
        # root.iconbitmap("icon.ico")
        pass
    except:
        pass

    # Create application
    try:
        app = OAKCameraViewer(root)

        # Center window on screen
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")

        # Start main loop
        root.mainloop()

    except Exception as e:
        messagebox.showerror(
            "Application Error", f"Failed to start application: {str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
