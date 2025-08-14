import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime
from pathlib import Path
import cv2
from typing import Dict, Optional
import subprocess
import platform

# Import our custom modules
from camera.controller import CameraController
from camera.settings import CameraSettingsManager
from camera.roi_manager import ROIManager
from utils.file_manager import FileManager
from ui.display import UIManager, MenuBarManager, StatusBarManager, DisplayManager
from ui.controls import QuickActionsMenu, ControlPanel
from ui.roi_controls import ROIControlPanel
from GPS.gps_integration import GPSIntegration


class OAKCameraViewer:
    """Main application class with proper separation of UI components"""

    def __init__(self, root: tk.Tk):
        self.root = root

        # Initialize backend components
        self.camera_controller = CameraController()
        self.settings_manager = CameraSettingsManager(self.camera_controller)
        self.roi_manager = ROIManager(self.camera_controller)
        self.file_manager = FileManager()
        self.gps = GPSIntegration()

        # Initialize UI components
        self.ui_manager = UIManager(root)
        self.quick_actions: Optional[QuickActionsMenu] = None
        self.control_panel: Optional[ControlPanel] = None
        self.roi_control_panel: Optional[ROIControlPanel] = None

        # Application state
        self.connected = False
        self.status_thread: Optional[threading.Thread] = None
        self.status_running = False
        # GPS movement-based capture state
        self.gps_capture_running = False
        self.gps_capture_thread: Optional[threading.Thread] = None
        self.last_gps_position: Optional[Dict] = None

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

        # Setup control notebook
        control_notebook = self.ui_manager.get_control_notebook()
        
        # Setup camera settings control panel
        camera_frame = ttk.Frame(control_notebook)
        control_notebook.add(camera_frame, text="Camera Settings")
        self.control_panel = ControlPanel(camera_frame, self.settings_manager)
        
        # Setup ROI control panel
        roi_frame = ttk.Frame(control_notebook)
        control_notebook.add(roi_frame, text="ROI")
        self.roi_control_panel = ROIControlPanel(roi_frame, self.roi_manager)

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
                toggle_gps_interval=self.toggle_gps_interval_capture,
                save_dir_change=self.set_save_directory,
                update_settings=self.update_camera_settings,
                reset_settings=self.reset_camera_settings,
            )

        # Control panel callbacks
        if self.control_panel:
            self.control_panel.set_callbacks(settings_change=self.apply_stream_settings)

        # ROI control panel callbacks
        if self.roi_control_panel:
            self.roi_control_panel.set_roi_changed_callback(self.on_roi_changed)

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

            # Initialize and start ROI processing
            self.roi_manager.initialize_for_cameras()
            self.roi_manager.start_roi_processing()
            
            # Start display updates
            display_manager = self.ui_manager.get_display_manager()
            if display_manager:
                # Ensure display loop targets the selected FPS
                display_manager.target_fps = current_settings.get("fps", 30)
                display_manager.start_display_loop(
                    self.camera_controller, self.file_manager, self.roi_manager
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

        # Stop ROI processing
        self.roi_manager.stop_roi_processing()
        
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
        # Stop GPS interval capture
        self.stop_gps_interval_capture()

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
            # Save GPS data JSON alongside captures if available (same folder, same base)
            gps_data = self.gps.get_current_gps_data()
            if gps_data:
                for path in filepaths:
                    # Overwrite gps_integration default directory: save next to image
                    try:
                        import json, os
                        base, _ = os.path.splitext(path)
                        json_path = base + ".json"
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump({
                                "image_filename": path,
                                "gps_data": gps_data,
                                "captured_at": datetime.now().isoformat(),
                            }, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        print(f"GPS save error: {e}")
                self.update_status(f"Captured {success_count} images + GPS")
        else:
            self.update_status("Capture failed")

    def _gps_distance_m(self, a: Dict, b: Dict) -> float:
        import math
        lat1, lon1 = a.get("latitude", 0.0), a.get("longitude", 0.0)
        lat2, lon2 = b.get("latitude", 0.0), b.get("longitude", 0.0)
        r = 6371000.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dl = math.radians(lon2 - lon1)
        x = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2.0) ** 2
        return 2.0 * r * math.asin(min(1.0, math.sqrt(x)))

    def start_gps_interval_capture(self):
        """Start background GPS-interval-based capture"""
        if self.gps_capture_running:
            self.update_status("GPS interval capture already running")
            return
        if not self.connected:
            self.update_status("Connect camera first")
            return
        self.gps_capture_running = True
        self.last_gps_position = None

        def _loop():
            self.update_status("GPS interval capture started")
            while self.gps_capture_running:
                try:
                    gps_data = self.gps.get_current_gps_data()
                    if gps_data:
                        if self.last_gps_position is None:
                            self.last_gps_position = gps_data
                            # Capture immediately on first valid fix
                            self._capture_images_with_gps(gps_data)
                        else:
                            dist = self._gps_distance_m(self.last_gps_position, gps_data)
                            threshold_m = float(self.settings_manager.get_setting("gps_interval_m") or 1.0)
                            if dist >= threshold_m:
                                self._capture_images_with_gps(gps_data)
                                self.last_gps_position = gps_data
                    # Sleep a short interval to avoid busy loop
                    time.sleep(0.2)
                except Exception as e:
                    print(f"GPS interval loop error: {e}")
                    time.sleep(0.5)
            self.update_status("GPS interval capture stopped")

        self.gps_capture_thread = threading.Thread(target=_loop, daemon=True)
        self.gps_capture_thread.start()

    def stop_gps_interval_capture(self):
        self.gps_capture_running = False
        if self.gps_capture_thread and self.gps_capture_thread.is_alive():
            self.gps_capture_thread.join(timeout=1.0)

    def _capture_images_with_gps(self, gps_data: Dict):
        """Capture images and save paired GPS JSON in date folder with same base name"""
        try:
            images = {}
            for camera_name in self.camera_controller.get_connected_cameras():
                frame = self.camera_controller.get_frame(camera_name)
                if frame is not None:
                    images[camera_name] = frame
            if not images:
                return
            # Ensure date dir
            now = datetime.now()
            date_dir = self.file_manager.ensure_date_directory(now)
            ts = now.strftime("%Y%m%d_%H%M%S_%f")[:-3]
            saved_paths = []
            for camera_name, img in images.items():
                img_path = date_dir / f"{camera_name}_{ts}.jpg"
                cv2.imwrite(str(img_path), img)
                saved_paths.append(str(img_path))
            # Save GPS JSONs with same base
            for img_path in saved_paths:
                self.gps.save_gps_data_with_image(img_path, gps_data)
            self.update_status("GPS interval capture saved")
        except Exception as e:
            print(f"GPS capture save error: {e}")

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

    def update_camera_settings(self):
        """Apply all pending camera settings"""
        if self.connected:
            self.settings_manager.apply_all_settings()
            self.update_status("Camera settings updated successfully")
        else:
            messagebox.showwarning("Not Connected", "Please connect to camera first to apply settings")

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

    def toggle_gps_interval_capture(self):
        if not self.gps_capture_running:
            self.start_gps_interval_capture()
            if self.quick_actions:
                self.quick_actions.update_gps_interval_status(True)
        else:
            self.stop_gps_interval_capture()
            if self.quick_actions:
                self.quick_actions.update_gps_interval_status(False)

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

    def on_roi_changed(self, camera_name: str):
        """Handle ROI settings changes"""
        if camera_name == "all":
            self.update_status("ROI settings reset for all cameras")
            # Update UI controls for all cameras
            if self.roi_control_panel:
                for cam in self.roi_control_panel.camera_tabs:
                    self.roi_control_panel._update_controls_from_settings(cam)
        elif camera_name == "mouse_roi":
            self.update_status("Mouse ROI selection toggled")
            # Update mouse ROI status in UI
            if self.roi_control_panel:
                self.roi_control_panel.update_mouse_roi_status()
        else:
            roi_info = self.roi_manager.get_roi_info(camera_name)
            if roi_info.get("enabled", False):
                self.update_status(f"ROI updated for {camera_name}")
                # Update UI controls for this camera
                if self.roi_control_panel and camera_name in self.roi_control_panel.camera_tabs:
                    self.roi_control_panel._update_controls_from_settings(camera_name)
            else:
                self.update_status(f"ROI disabled for {camera_name}")
                # Update UI controls for this camera
                if self.roi_control_panel and camera_name in self.roi_control_panel.camera_tabs:
                    self.roi_control_panel._update_controls_from_settings(camera_name)

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
