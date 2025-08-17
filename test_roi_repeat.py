#!/usr/bin/env python3
"""
Test script to verify ROI functionality works every time
"""

import sys
import tkinter as tk
from camera.controller import CameraController
from camera.roi_manager import ROIManager, ROISettings
from ui.roi_controls import ROIControlPanel
from ui.display import DisplayManager
import ttk
import time

def test_roi_repeat_functionality():
    """Test that ROI functionality works every time it's applied"""
    print("Testing ROI repeat functionality...")
    
    # Create root window
    root = tk.Tk()
    root.title("ROI Repeat Test")
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
        
        # Test multiple ROI applications
        print("\n=== Testing Multiple ROI Applications ===")
        
        # Test 1: Enable mouse ROI and apply first ROI
        print("\n--- Test 1: First ROI Application ---")
        roi_manager.enable_mouse_roi(True)
        time.sleep(0.5)
        
        # Simulate mouse ROI selection (top-left region)
        roi_manager.handle_mouse_event("CAM_A", "mousedown", 100, 100, 640, 480)
        roi_manager.handle_mouse_event("CAM_A", "mouseup", 200, 200, 640, 480)
        time.sleep(1.0)
        
        # Test 2: Apply second ROI (center region)
        print("\n--- Test 2: Second ROI Application ---")
        roi_manager.handle_mouse_event("CAM_A", "mousedown", 250, 200, 640, 480)
        roi_manager.handle_mouse_event("CAM_A", "mouseup", 350, 300, 640, 480)
        time.sleep(1.0)
        
        # Test 3: Apply third ROI (bottom-right region)
        print("\n--- Test 3: Third ROI Application ---")
        roi_manager.handle_mouse_event("CAM_A", "mousedown", 400, 300, 640, 480)
        roi_manager.handle_mouse_event("CAM_A", "mouseup", 500, 400, 640, 480)
        time.sleep(1.0)
        
        # Test 4: Change exposure compensation
        print("\n--- Test 4: Exposure Compensation Change ---")
        roi_manager.set_exposure_compensation("CAM_A", 3)
        time.sleep(1.0)
        
        # Test 5: Enable focus region
        print("\n--- Test 5: Enable Focus Region ---")
        roi_manager.set_focus_region("CAM_A", True)
        time.sleep(1.0)
        
        # Test 6: Disable and re-enable ROI
        print("\n--- Test 6: Disable and Re-enable ROI ---")
        roi_manager.enable_roi("CAM_A", False)
        time.sleep(1.0)
        roi_manager.enable_roi("CAM_A", True)
        time.sleep(1.0)
        
        # Test 7: Reset ROI settings
        print("\n--- Test 7: Reset ROI Settings ---")
        roi_manager.reset_roi_settings("CAM_A")
        time.sleep(1.0)
        
        print("\n=== ROI Repeat Test Complete ===")
        print("Check the console output above to verify that:")
        print("1. Each ROI application shows 'ROI settings changed, applying new settings...'")
        print("2. Each application shows the new ROI parameters")
        print("3. Settings are properly tracked and reapplied")
        
        # Start main loop
        root.mainloop()
        
    except Exception as e:
        print(f"Error during ROI repeat test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if 'roi_manager' in locals():
            roi_manager.stop_roi_processing()
        if 'camera_controller' in locals():
            camera_controller.disconnect()

if __name__ == "__main__":
    test_roi_repeat_functionality()
