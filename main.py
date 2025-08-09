import sys
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import time
from pathlib import Path
from typing import Dict, Optional
import subprocess
import platform

# Import our custom modules
from camera.controller import CameraController
from camera.settings import CameraSettingsManager
from utils.file_manager import FileManager
from ui.display import UIManager, MenuBarManager, StatusBarManager, DisplayManager
from ui.controls import QuickActionsMenu, ControlPanel
from GPS.gps_integration import GPSIntegration


class OAKCameraViewer:
    """Main application class with proper separation of UI components"""

    def __init__(self, root: tk.Tk):
        self.root = root

        # Initialize backend components
        self.camera_controller = CameraController()
        self.settings_manager = CameraSettingsManager(self.camera_controller)
        self.file_manager = FileManager()
        self.gps = GPSIntegration()

        # Initialize UI components
        self.ui_manager = UIManager(root)
        self.quick_actions: Optional[QuickActionsMenu] = None
        self.control_panel: Optional[ControlPanel] = None

        # Application state
        self.connected = False
        self.status_thread: Optional[threading.Thread] = None
        self.status_running = False

        # Setup application
        self.setup_application()

    def setup_application(self):
        """Setup the complete application"""
        # Setup main UI structure
        self.ui_manager.setup_main_ui()
        self.ui_manager.set_window_properties(
            title="OAK PoE Camera Viewer - DepthAI V3",
            geometry="1600x1000",
            min_size=(1400, 900),
        )

        # Setup UI components
        self.setup_ui_components()

        # Setup event handlers and callbacks
        self.setup_callbacks()

        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()

        # Start background monitoring
        self.start_status_monitoring()

        # Center window
        self.ui_manager.center_window()

    def setup_ui_components(self):
        """Setup all UI components with proper separation"""
        # Setup quick actions menu in top frame
        self.quick_actions = QuickActionsMenu(self.ui_manager.get_top_frame())

        # Setup control panel in left frame
        self.control_panel = ControlPanel(
            self.ui_manager.get_control_frame(), self.settings_manager
        )

    def setup_callbacks(self):
        """Setup all callback functions"""
        # Quick actions callbacks
        if self.quick_actions:
            self.quick_actions.set_callbacks(
                connect=self.connect_camera,
                disconnect=self.disconnect_camera,
                capture=self.capture_images,
                record_toggle=self.toggle_recording,
                capture_gps=self.capture_gps_data,
                save_dir_change=self.set_save_directory,
                reset_settings=self.reset_camera_settings,
            )

        # Control panel callbacks
        if self.control_panel:
            self.control_panel.set_callbacks(settings_change=self.apply_stream_settings)

        # Menu bar callbacks
        if self.ui_manager.get_menu_bar():
            self.ui_manager.get_menu_bar().set_callbacks(
                open_save_dir=self.open_save_directory,
                connect=self.connect_camera,
                disconnect=self.disconnect_camera,
                capture=self.capture_images,
                record_toggle=self.toggle_recording,
                reset_settings=self.reset_camera_settings,
                refresh_displays=self.refresh_displays,
                show_shortcuts=self.show_shortcuts,
                show_about=self.show_about,
                exit=self.on_closing,
            )

        # Window close handler
        self.ui_manager.set_close_handler(self.on_closing)

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            "<Control-c>": self.capture_images,
            "<Control-r>": self.toggle_recording,
            "<Control-d>": self.disconnect_camera,
            "<Control-n>": self.connect_camera,
            "<Control-q>": self.on_closing,
            "<F5>": self.refresh_displays,
        }
        self.ui_manager.setup_keyboard_shortcuts(shortcuts)

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
                free_gb, total_gb = self.file_manager.get_available_space()
                if self.quick_actions:
                    self.root.after(
                        0,
                        lambda: self.quick_actions.update_disk_space_display(
                            free_gb, total_gb
                        ),
                    )

                # Update recording duration
                if self.file_manager.is_recording():
                    duration = self.file_manager.get_recording_duration()
                    if self.quick_actions:
                        self.root.after(
                            0,
                            lambda: self.quick_actions.update_recording_status(
                                True, duration
                            ),
                        )
                    if self.ui_manager.get_status_bar():
                        self.root.after(
                            0,
                            lambda: self.ui_manager.get_status_bar().update_status(
                                f"Recording... {duration:.1f}s"
                            ),
                        )

                # Update FPS if connected
                if self.connected and self.ui_manager.get_display_manager():
                    fps = self.ui_manager.get_display_manager().get_current_fps()
                    if self.ui_manager.get_status_bar():
                        self.root.after(
                            0, lambda: self.ui_manager.get_status_bar().update_fps(fps)
                        )

                time.sleep(1.0)

            except Exception as e:
                print(f"Status monitoring error: {e}")
                time.sleep(5.0)

    def connect_camera(self):
        """Connect to the camera"""
        if self.connected:
            self.update_status("Already connected")
            return

        self.update_status("Connecting to camera...")
        if self.quick_actions:
            self.quick_actions.widgets["connection_status_label"].config(
                text="● Connecting...", foreground="orange"
            )

        # Run connection in separate thread
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
                self.root.after(
                    0,
                    lambda: (
                        self.quick_actions.update_connection_status(False)
                        if self.quick_actions
                        else None
                    ),
                )
                return

            print(f"Connection successful: {message}")

            # Attempt GPS connection in background (non-blocking)
            def start_gps():
                try:
                    if self.gps.connect_gps():
                        self.gps.start_gps_monitoring()
                        self.update_status("GPS connected")
                    else:
                        self.update_status("GPS not found")
                except Exception as e:
                    print(f"GPS init error: {e}")
            threading.Thread(target=start_gps, daemon=True).start()

            # Get current settings for pipeline setup
            current_settings = {"width": 1280, "height": 720, "fps": 30}
            if self.control_panel:
                current_settings = self.control_panel.get_current_settings()

            print(
                f"Setting up pipeline: {current_settings['width']}x{current_settings['height']}@{current_settings['fps']}fps"
            )

            # Pass per-camera desired resolutions to controller
            if "per_camera_resolutions" in current_settings:
                self.camera_controller.set_desired_resolutions(
                    current_settings["per_camera_resolutions"]
                )

            if not self.camera_controller.setup_pipeline(
                current_settings["width"],
                current_settings["height"],
                current_settings["fps"],
            ):
                error_msg = "Failed to setup camera pipeline."
                print("Pipeline setup failed")
                self.root.after(
                    0, lambda: messagebox.showerror("Pipeline Error", error_msg)
                )
                self.root.after(0, lambda: self.update_status("Pipeline setup failed"))
                self.root.after(
                    0,
                    lambda: (
                        self.quick_actions.update_connection_status(False)
                        if self.quick_actions
                        else None
                    ),
                )
                return

            # Setup display tabs
            def setup_displays():
                connected_cameras = self.camera_controller.get_connected_cameras()
                print(f"Setting up display tabs for: {connected_cameras}")
                display_manager = self.ui_manager.get_display_manager()
                if display_manager:
                    for camera_name in connected_cameras:
                        display_manager.setup_camera_tab(camera_name)

            self.root.after(0, setup_displays)

            # Start streaming
            if not self.camera_controller.start_streaming():
                error_msg = "Failed to start camera streaming."
                print("Streaming failed to start")
                self.root.after(
                    0, lambda: messagebox.showerror("Streaming Error", error_msg)
                )
                self.root.after(0, lambda: self.update_status("Streaming failed"))
                return

            # Start display updates
            display_manager = self.ui_manager.get_display_manager()
            if display_manager:
                # Ensure display loop targets the selected FPS
                display_manager.target_fps = current_settings.get("fps", 30)
                display_manager.start_display_loop(
                    self.camera_controller, self.file_manager
                )

            # Update UI state
            self.connected = True
            device_info = self.camera_controller.get_device_info()

            def update_ui():
                if self.quick_actions:
                    self.quick_actions.update_connection_status(True)
                if self.control_panel:
                    self.control_panel.update_device_info(device_info)
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
            self.root.after(
                0,
                lambda: (
                    self.quick_actions.update_connection_status(False)
                    if self.quick_actions
                    else None
                ),
            )

    def disconnect_camera(self):
        """Disconnect from camera"""
        if not self.connected:
            self.update_status("Not connected")
            return

        self.update_status("Disconnecting...")

        # Stop recording if active
        if self.file_manager.is_recording():
            success, message, _ = self.file_manager.stop_video_recording()
            if self.quick_actions:
                self.quick_actions.update_recording_status(False)

        # Stop display updates
        display_manager = self.ui_manager.get_display_manager()
        if display_manager:
            display_manager.stop_display_loop()

        # Disconnect camera
        self.camera_controller.disconnect()
        # Disconnect GPS
        try:
            self.gps.disconnect_gps()
        except Exception:
            pass

        # Clear displays
        if display_manager:
            display_manager.clear_displays()

        # Update UI state
        self.connected = False
        if self.quick_actions:
            self.quick_actions.update_connection_status(False)
        if self.control_panel:
            self.control_panel.update_device_info(None)
        self.update_status("Disconnected")

    def capture_images(self):
        """Capture images from all cameras"""
        if not self.connected:
            self.update_status("No cameras connected")
            return

        self.update_status("Capturing images...")

        # Collect frames from all cameras
        images = {}
        for camera_name in self.camera_controller.get_connected_cameras():
            frame = self.camera_controller.get_frame(camera_name)
            if frame is not None:
                images[camera_name] = frame

        if not images:
            self.update_status("Capture failed - no frames")
            return

        # Capture batch
        success_count, filepaths = self.file_manager.capture_images_batch(images)

        if success_count > 0:
            self.update_status(f"Captured {success_count} images")
            # Save GPS data JSON alongside captures if available
            try:
                gps_data = self.gps.get_current_gps_data()
                if gps_data:
                    for path in filepaths:
                        self.gps.save_gps_data_with_image(path, gps_data)
                    self.update_status(f"Captured {success_count} images + GPS")
            except Exception as e:
                print(f"GPS save error: {e}")
        else:
            self.update_status("Capture failed")

    def toggle_recording(self):
        """Toggle video recording"""
        if not self.connected:
            self.update_status("No cameras connected")
            return

        if self.file_manager.is_recording():
            # Stop recording
            success, message, filepaths = self.file_manager.stop_video_recording()
            if self.quick_actions:
                self.quick_actions.update_recording_status(False)

            if success:
                self.update_status("Recording stopped")
            else:
                self.update_status(f"Error stopping recording: {message}")
        else:
            # Start recording
            camera_names = self.camera_controller.get_connected_cameras()
            if not camera_names:
                self.update_status("No cameras available")
                return

            # Get current resolution and fps settings
            current_settings = {"width": 1280, "height": 720, "fps": 30}
            if self.control_panel:
                current_settings = self.control_panel.get_current_settings()

            success, message = self.file_manager.start_video_recording(
                camera_names,
                current_settings["width"],
                current_settings["height"],
                current_settings["fps"],
                per_camera_resolutions=current_settings.get("per_camera_resolutions"),
            )

            if success:
                if self.quick_actions:
                    self.quick_actions.update_recording_status(True, 0.0)
                self.update_status("Recording started")
                # Note: For live GPS logging during recording, we could append per frame
                # but for now we keep on-demand capture via button
            else:
                self.update_status(f"Failed to start recording: {message}")

    def capture_gps_data(self):
        """Capture current GPS data to a standalone JSON file"""
        try:
            data = self.gps.get_current_gps_data()
            if not data:
                self.update_status("No GPS fix yet")
                return
            # Save a timestamped JSON even without image association
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Reuse save directory
            json_path = self.file_manager.save_directory / f"gps_only_{ts}.json"
            import json
            payload = {"gps_data": data, "captured_at": datetime.now().isoformat()}
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            self.update_status("GPS captured")
        except Exception as e:
            print(f"GPS capture error: {e}")
            self.update_status("GPS capture failed")

    def set_save_directory(self):
        """Set the save directory for captures"""
        directory = filedialog.askdirectory(
            title="Select Save Directory", initialdir=self.file_manager.save_directory
        )

        if directory:
            success = self.file_manager.set_save_directory(Path(directory))
            if success:
                if self.quick_actions:
                    self.quick_actions.update_save_directory_display(Path(directory))
                self.update_status("Save directory updated")
            else:
                messagebox.showerror("Error", "Failed to set save directory")

    def apply_stream_settings(self, settings: Dict):
        """Apply new stream settings (requires reconnection)"""
        if self.connected:
            # No popup; reconnect automatically
            self.disconnect_camera()
            time.sleep(1)
            self.connect_camera()

    def reset_camera_settings(self):
        """Reset all camera settings to defaults"""
        if messagebox.askyesno(
            "Reset Settings", "Reset all camera settings to defaults?"
        ):
            self.settings_manager.reset_to_defaults()
            if self.control_panel:
                self.control_panel.update_all_widgets()
            self.update_status("Settings reset to defaults")

    def refresh_displays(self):
        """Refresh camera displays"""
        if self.connected:
            display_manager = self.ui_manager.get_display_manager()
            if display_manager:
                display_manager.clear_displays()
                for camera_name in self.camera_controller.get_connected_cameras():
                    display_manager.setup_camera_tab(camera_name)
            self.update_status("Displays refreshed")

    def open_save_directory(self):
        """Open the save directory in file explorer"""
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", str(self.file_manager.save_directory)])
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(self.file_manager.save_directory)])
            else:
                subprocess.run(["xdg-open", str(self.file_manager.save_directory)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open directory: {e}")

    def show_shortcuts(self):
        """Show keyboard shortcuts - handled by MenuBarManager"""
        pass  # MenuBarManager handles this with its default implementation

    def show_about(self):
        """Show about dialog - handled by MenuBarManager"""
        pass  # MenuBarManager handles this with its default implementation

    def update_status(self, message: str):
        """Update status bar message"""
        status_bar = self.ui_manager.get_status_bar()
        if status_bar:
            status_bar.update_status(message)

    def on_closing(self):
        """Handle application closing"""
        if self.file_manager.is_recording():
            result = messagebox.askyesnocancel(
                "Recording Active",
                "Video recording is active. Stop recording before closing?",
            )
            if result is None:
                return
            elif result:
                self.file_manager.stop_video_recording()

        # Stop all operations
        self.status_running = False
        self.disconnect_camera()

        # Cleanup
        if self.file_manager:
            self.file_manager.cleanup()

        self.root.quit()
        self.root.destroy()


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
    if not check_dependencies():
        sys.exit(1)

    # Create and configure root window
    root = tk.Tk()

    try:
        app = OAKCameraViewer(root)

        # Start main loop
        root.mainloop()

    except Exception as e:
        messagebox.showerror(
            "Application Error", f"Failed to start application: {str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
