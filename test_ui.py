#!/usr/bin/env python3
"""
UI Testing Script
Test the new tabbed camera controls interface
"""

import tkinter as tk
from tkinter import ttk


# Mock classes for testing
class MockCameraController:
    def __init__(self):
        pass

    def send_control_to_all_cameras(self, ctrl):
        print(f"Mock: Sending control command")


class MockCameraSettingsManager:
    def __init__(self, controller):
        self.controller = controller
        self.settings = {
            "exposure": 20000,
            "iso": 800,
            "focus": 130,
            "brightness": 0,
            "contrast": 0,
            "saturation": 0,
            "sharpness": 1,
            "white_balance": 4000,
            "fps": 30,
            "resolution_width": 1280,
            "resolution_height": 720,
            "luma_denoise": 1,
            "chroma_denoise": 1,
        }

        self.auto_modes = {
            "auto_exposure": True,
            "auto_focus": True,
            "auto_white_balance": True,
            "auto_exposure_lock": False,
            "auto_white_balance_lock": False,
        }

    # Constants
    EXPOSURE_MIN = 1
    EXPOSURE_MAX = 33000
    ISO_MIN = 100
    ISO_MAX = 1600
    FOCUS_MIN = 0
    FOCUS_MAX = 255
    BRIGHTNESS_MIN = -10
    BRIGHTNESS_MAX = 10
    CONTRAST_MIN = -10
    CONTRAST_MAX = 10
    SATURATION_MIN = -10
    SATURATION_MAX = 10
    SHARPNESS_MIN = 0
    SHARPNESS_MAX = 4
    WB_MIN = 1000
    WB_MAX = 12000

    def get_setting(self, key):
        value = self.settings.get(key, 0)
        # Ensure integer values for camera controls
        if key in ["exposure", "iso", "focus", "brightness", "contrast", "saturation", "sharpness", "white_balance", "luma_denoise", "chroma_denoise"]:
            return int(value) if value is not None else 0
        return value

    def get_auto_mode(self, key):
        return self.auto_modes.get(key, False)

    def set_auto_exposure(self, enabled):
        print(f"Mock: Set auto exposure = {enabled}")

    def set_auto_focus(self, enabled):
        print(f"Mock: Set auto focus = {enabled}")

    def set_auto_white_balance(self, enabled):
        print(f"Mock: Set auto white balance = {enabled}")

    def set_auto_exposure_lock(self, locked):
        print(f"Mock: Set AE lock = {locked}")

    def set_auto_white_balance_lock(self, locked):
        print(f"Mock: Set AWB lock = {locked}")

    def trigger_autofocus(self):
        print("Mock: Trigger autofocus")

    def set_exposure(self, value):
        print(f"Mock: Set exposure = {value}")

    def set_iso(self, value):
        print(f"Mock: Set ISO = {value}")

    def set_focus(self, value):
        print(f"Mock: Set focus = {value}")

    def set_brightness(self, value):
        print(f"Mock: Set brightness = {value}")

    def set_contrast(self, value):
        print(f"Mock: Set contrast = {value}")

    def set_saturation(self, value):
        print(f"Mock: Set saturation = {value}")

    def set_sharpness(self, value):
        print(f"Mock: Set sharpness = {value}")

    def set_white_balance(self, value):
        print(f"Mock: Set white balance = {value}")

    def set_luma_denoise(self, value):
        print(f"Mock: Set luma denoise = {value}")

    def set_chroma_denoise(self, value):
        print(f"Mock: Set chroma denoise = {value}")

    def update_setting(self, key, value):
        if key in self.settings:
            self.settings[key] = value

    def apply_all_settings(self):
        print("Mock: Applying all camera settings...")
        print("Mock: Camera settings applied successfully!")
        print("Mock: Current camera settings:")
        for key, value in self.settings.items():
            if key in ["exposure", "iso", "focus", "brightness", "contrast", "saturation", "sharpness", "white_balance", "luma_denoise", "chroma_denoise"]:
                print(f"  {key}: {value}")
        print("Mock: Auto modes:")
        for key, value in self.auto_modes.items():
            print(f"  {key}: {value}")


# Import the actual ControlPanel
try:
    from ui.controls import ControlPanel

    def test_ui():
        """Test the new tabbed UI"""
        root = tk.Tk()
        root.title("Camera Controls UI Test")
        root.geometry("400x800")

        # Create mock components
        controller = MockCameraController()
        settings_manager = MockCameraSettingsManager(controller)

        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create control panel
        control_panel = ControlPanel(main_frame, settings_manager)

        # Set up callbacks
        def on_connect():
            print("Mock: Connect clicked")

        def on_disconnect():
            print("Mock: Disconnect clicked")

        def on_capture():
            print("Mock: Capture clicked")

        def on_record():
            print("Mock: Record clicked")

        def on_save_dir():
            print("Mock: Save directory clicked")

        def on_settings_change(settings):
            print(f"Mock: Settings changed: {settings}")

        control_panel.set_callbacks(
            connect=on_connect,
            disconnect=on_disconnect,
            capture=on_capture,
            record_toggle=on_record,
            save_dir_change=on_save_dir,
            settings_change=on_settings_change,
        )

        # Update connection status for testing
        control_panel.update_connection_status(False)

        print("UI Test Started")
        print("Features to test:")
        print("1. Resolution dropdown with preset values")
        print("2. Custom resolution dialog")
        print("3. Three camera settings tabs:")
        print("   - Auto/Manual controls")
        print("   - Image Quality settings")
        print("   - Advanced settings")
        print("4. All sliders and controls should work")

        root.mainloop()

    if __name__ == "__main__":
        test_ui()

except ImportError as e:
    print(f"Could not import ControlPanel: {e}")
    print("Make sure the ui/controls.py file is properly set up")
    print("Run this test from the main project directory")
