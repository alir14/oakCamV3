#!/usr/bin/env python3
"""
Debug test script to verify ROI functionality
"""

import sys
import tkinter as tk
from camera.controller import CameraController
from camera.roi_manager import ROIManager, ROISettings
from ui.roi_controls import ROIControlPanel
from ui.display import DisplayManager
import ttk
import time

def test_roi_debug():
    """Debug ROI functionality"""
    print("=== ROI Debug Test ===")
    
    # Create root window
    root = tk.Tk()
    root.title("ROI Debug Test")
    root.geometry("1200x800")
    
    try:
        # Initialize camera controller
        camera_controller = CameraController()
        
        # Test connection
        success, message = camera_controller.connect()
        print(f"Camera connection: {success} - {message}")
        
        if not success:
            print("No camera connected, testing with mock data...")
            # Create mock camera data for testing
            camera_controller.cameras = {"CAM_A": None, "CAM_B": None, "CAM_C": None}
        
        # Initialize ROI manager
        roi_manager = ROIManager(camera_controller)
        
        # Initialize ROI settings
        roi_manager.initialize_for_cameras()
        
        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create left panel for ROI controls
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Create ROI control panel
        roi_panel = ROIControlPanel(left_panel, roi_manager)
        
        # Create right panel for display
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create display notebook
        display_notebook = ttk.Notebook(right_panel)
        display_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create display manager
        display_manager = DisplayManager(display_notebook)
        
        # Setup display tabs
        connected_cameras = camera_controller.get_connected_cameras()
        for camera_name in connected_cameras:
            display_manager.setup_camera_tab(camera_name)
        
        # Set callbacks
        def on_roi_changed(camera_name):
            print(f"ROI changed for {camera_name}")
            # Update UI controls
            if camera_name in roi_panel.camera_tabs:
                roi_panel._update_controls_from_settings(camera_name)
        
        roi_panel.set_roi_changed_callback(on_roi_changed)
        
        # Start ROI processing
        roi_manager.start_roi_processing()
        
        # Start display loop if camera is connected
        if success:
            display_manager.start_display_loop(camera_controller, None, roi_manager)
        
        # Debug test sequence
        print("\n=== Debug Test Sequence ===")
        
        # Test 1: Check initial state
        print("\n--- Test 1: Initial State ---")
        roi_settings = roi_manager.get_roi_settings("CAM_A")
        if roi_settings:
            print(f"Initial ROI settings: enabled={roi_settings.enabled}, pos=({roi_settings.x:.3f},{roi_settings.y:.3f}), size=({roi_settings.width:.3f}x{roi_settings.height:.3f})")
        else:
            print("No ROI settings found for CAM_A")
        
        # Test 2: Enable mouse ROI
        print("\n--- Test 2: Enable Mouse ROI ---")
        roi_manager.enable_mouse_roi(True)
        time.sleep(0.5)
        
        # Test 3: Simulate mouse ROI selection
        print("\n--- Test 3: Simulate Mouse ROI Selection ---")
        print("Simulating mouse selection: (100,100) to (200,200) on 640x480 frame")
        roi_manager.handle_mouse_event("CAM_A", "mousedown", 100, 100, 640, 480)
        roi_manager.handle_mouse_event("CAM_A", "mouseup", 200, 200, 640, 480)
        time.sleep(1.0)
        
        # Test 4: Check ROI settings after selection
        print("\n--- Test 4: Check ROI Settings After Selection ---")
        roi_settings = roi_manager.get_roi_settings("CAM_A")
        if roi_settings:
            print(f"ROI settings after selection: enabled={roi_settings.enabled}, pos=({roi_settings.x:.3f},{roi_settings.y:.3f}), size=({roi_settings.width:.3f}x{roi_settings.height:.3f})")
        else:
            print("No ROI settings found after selection")
        
        # Test 5: Check if settings were applied
        print("\n--- Test 5: Check Settings Application ---")
        print("Check console output above for 'ROI applied to CAM_A' messages")
        
        # Test 6: Test exposure compensation
        print("\n--- Test 6: Test Exposure Compensation ---")
        roi_manager.set_exposure_compensation("CAM_A", 3)
        time.sleep(1.0)
        
        # Test 7: Test focus region
        print("\n--- Test 7: Test Focus Region ---")
        roi_manager.set_focus_region("CAM_A", True)
        time.sleep(1.0)
        
        print("\n=== Debug Test Complete ===")
        print("Check the console output above for:")
        print("1. ROI settings initialization")
        print("2. Mouse ROI selection processing")
        print("3. ROI application messages")
        print("4. Any error messages")
        
        # Start main loop
        root.mainloop()
        
    except Exception as e:
        print(f"Error during ROI debug test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if 'roi_manager' in locals():
            roi_manager.stop_roi_processing()
        if 'camera_controller' in locals():
            camera_controller.disconnect()

if __name__ == "__main__":
    test_roi_debug()
