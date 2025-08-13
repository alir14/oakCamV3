#!/usr/bin/env python3
"""
Test script for ROI functionality
"""

import sys
import tkinter as tk
from camera.controller import CameraController
from camera.roi_manager import ROIManager, ROISettings
from ui.roi_controls import ROIControlPanel

def test_roi_functionality():
    """Test ROI functionality"""
    print("Testing ROI functionality...")
    
    # Create root window
    root = tk.Tk()
    root.title("ROI Test")
    root.geometry("800x600")
    
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
        
        # Test ROI settings
        print("\nTesting ROI settings...")
        for camera_name in roi_manager.camera_controller.get_connected_cameras():
            # Set some test ROI settings
            roi_manager.set_roi_position(camera_name, 0.3, 0.4)
            roi_manager.set_roi_size(camera_name, 0.4, 0.5)
            roi_manager.set_exposure_compensation(camera_name, 2)
            roi_manager.enable_roi(camera_name, True)
            
            # Get and display settings
            settings = roi_manager.get_roi_settings(camera_name)
            print(f"{camera_name}: {settings}")
        
        # Create ROI control panel
        roi_panel = ROIControlPanel(root, roi_manager)
        
        # Set callback
        def on_roi_changed(camera_name):
            print(f"ROI changed for {camera_name}")
        
        roi_panel.set_roi_changed_callback(on_roi_changed)
        
        print("\nROI test setup complete. GUI should be visible.")
        print("Try adjusting the ROI controls to test functionality.")
        
        # Start main loop
        root.mainloop()
        
    except Exception as e:
        print(f"Error during ROI test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        root.destroy()

if __name__ == "__main__":
    test_roi_functionality()
