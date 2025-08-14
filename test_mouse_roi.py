#!/usr/bin/env python3
"""
Test script for Mouse ROI functionality
"""

import sys
import tkinter as tk
from camera.controller import CameraController
from camera.roi_manager import ROIManager, ROISettings
from ui.roi_controls import ROIControlPanel
from ui.display import DisplayManager
import ttk

def test_mouse_roi_functionality():
    """Test mouse ROI functionality"""
    print("Testing Mouse ROI functionality...")
    
    # Create root window
    root = tk.Tk()
    root.title("Mouse ROI Test")
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
        
        # Test mouse ROI functionality
        print("\nTesting Mouse ROI functionality...")
        print("1. Enable 'Mouse ROI Selection' in the ROI controls")
        print("2. Click and drag on the CAM_A display to select ROI region")
        print("3. Release mouse to apply the ROI")
        print("4. Check that ROI settings are updated in the controls")
        
        # Start ROI processing
        roi_manager.start_roi_processing()
        
        # Start display loop if camera is connected
        if success:
            display_manager.start_display_loop(camera_controller, None, roi_manager)
        
        # Test mouse ROI enable/disable
        print("\nTesting mouse ROI enable/disable...")
        roi_manager.enable_mouse_roi(True)
        print(f"Mouse ROI enabled: {roi_manager.is_mouse_roi_enabled()}")
        
        roi_manager.enable_mouse_roi(False)
        print(f"Mouse ROI enabled: {roi_manager.is_mouse_roi_enabled()}")
        
        # Test manual ROI settings
        print("\nTesting manual ROI settings...")
        if "CAM_A" in roi_manager.roi_settings:
            roi_manager.set_roi_position("CAM_A", 0.3, 0.4)
            roi_manager.set_roi_size("CAM_A", 0.4, 0.5)
            roi_manager.set_exposure_compensation("CAM_A", 2)
            roi_manager.enable_roi("CAM_A", True)
            
            settings = roi_manager.get_roi_settings("CAM_A")
            print(f"CAM_A ROI settings: {settings}")
        
        print("\nMouse ROI test setup complete!")
        print("Use the UI to test mouse ROI selection functionality.")
        
        # Start main loop
        root.mainloop()
        
    except Exception as e:
        print(f"Error during mouse ROI test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if 'roi_manager' in locals():
            roi_manager.stop_roi_processing()
        if 'camera_controller' in locals():
            camera_controller.disconnect()

if __name__ == "__main__":
    test_mouse_roi_functionality()
