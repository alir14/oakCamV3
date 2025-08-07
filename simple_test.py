#!/usr/bin/env python3
"""
Simple UI Test to identify syntax issues
"""

import sys
import traceback

def test_imports():
    """Test importing modules one by one to find the issue"""
    print("Testing imports...")
    
    try:
        print("1. Testing basic imports...")
        import tkinter as tk
        from tkinter import ttk, messagebox
        print("   ✓ tkinter imports successful")
        
        print("2. Testing typing imports...")
        from typing import Dict, Any, Callable, Optional
        print("   ✓ typing imports successful")
        
        print("3. Testing pathlib...")
        from pathlib import Path
        print("   ✓ pathlib import successful")
        
        print("4. Testing camera module...")
        try:
            from camera.settings import CameraSettingsManager
            print("   ✓ camera.settings import successful")
        except Exception as e:
            print(f"   ⚠ camera.settings import failed: {e}")
        
        print("5. Testing ui.controls module...")
        from ui.controls import ControlPanel
        print("   ✓ ui.controls import successful")
        
        print("\n✅ All imports successful!")
        
    except SyntaxError as e:
        print(f"\n❌ Syntax Error: {e}")
        print(f"File: {e.filename}")
        print(f"Line: {e.lineno}")
        print(f"Text: {e.text}")
        traceback.print_exc()
        
    except Exception as e:
        print(f"\n❌ Import Error: {e}")
        traceback.print_exc()

def test_ui_creation():
    """Test creating the UI"""
    try:
        print("\nTesting UI creation...")
        
        import tkinter as tk
        from tkinter import ttk
        
        # Mock settings manager
        class MockSettings:
            def get_setting(self, key):
                defaults = {
                    'resolution_width': 1280,
                    'resolution_height': 720,
                    'fps': 30,
                    'exposure': 20000,
                    'iso': 800,
                    'focus': 130,
                    'brightness': 0,
                    'contrast': 0,
                    'saturation': 0,
                    'sharpness': 1,
                    'white_balance': 4000,
                    'luma_denoise': 1,
                    'chroma_denoise': 1,
                }
                return defaults.get(key, 0)
            
            def get_auto_mode(self, key):
                return True
            
            # Add constants
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
            
            # Mock methods
            def set_auto_exposure(self, v): pass
            def set_auto_focus(self, v): pass
            def set_auto_white_balance(self, v): pass
            def set_auto_exposure_lock(self, v): pass
            def set_auto_white_balance_lock(self, v): pass
            def trigger_autofocus(self): pass
            def set_exposure(self, v): pass
            def set_iso(self, v): pass
            def set_focus(self, v): pass
            def set_brightness(self, v): pass
            def set_contrast(self, v): pass
            def set_saturation(self, v): pass
            def set_sharpness(self, v): pass
            def set_white_balance(self, v): pass
            def set_luma_denoise(self, v): pass
            def set_chroma_denoise(self, v): pass
        
        # Create window
        root = tk.Tk()
        root.title("Simple UI Test")
        root.geometry("400x600")
        
        # Create frame
        frame = ttk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Test basic widgets
        ttk.Label(frame, text="UI Test - Basic Widgets").pack(pady=5)
        
        # Resolution dropdown test
        ttk.Label(frame, text="Resolution:").pack(anchor=tk.W)
        resolution_var = tk.StringVar(value="1280x720")
        resolution_options = ["640x480", "1280x720", "1920x1080"]
        resolution_combo = ttk.Combobox(frame, textvariable=resolution_var, 
                                       values=resolution_options, state="readonly")
        resolution_combo.pack(fill=tk.X, pady=2)
        
        # FPS dropdown test
        ttk.Label(frame, text="FPS:").pack(anchor=tk.W)
        fps_var = tk.StringVar(value="30")
        fps_options = ["15", "30", "60"]
        fps_combo = ttk.Combobox(frame, textvariable=fps_var, 
                                values=fps_options, state="readonly")
        fps_combo.pack(fill=tk.X, pady=2)
        
        # Tabbed interface test
        notebook = ttk.Notebook(frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Tab 1
        tab1 = ttk.Frame(notebook)
        notebook.add(tab1, text="Auto/Manual")
        ttk.Label(tab1, text="Auto/Manual Controls").pack(pady=10)
        ttk.Checkbutton(tab1, text="Auto Exposure").pack(anchor=tk.W)
        ttk.Checkbutton(tab1, text="Auto Focus").pack(anchor=tk.W)
        
        # Tab 2  
        tab2 = ttk.Frame(notebook)
        notebook.add(tab2, text="Image Quality")
        ttk.Label(tab2, text="Image Quality Controls").pack(pady=10)
        brightness_var = tk.IntVar(value=0)
        ttk.Scale(tab2, from_=-10, to=10, variable=brightness_var, 
                 orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        
        # Tab 3
        tab3 = ttk.Frame(notebook)
        notebook.add(tab3, text="Advanced")
        ttk.Label(tab3, text="Advanced Settings").pack(pady=10)
        ttk.Button(tab3, text="Reset to Defaults").pack()
        
        print("✅ Basic UI creation successful!")
        
        # Show window briefly
        root.after(2000, root.destroy)  # Auto close after 2 seconds
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ UI creation failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Simple UI Test Starting...")
    print("=" * 50)
    
    # Test imports first
    test_imports()
    
    # If imports work, test UI creation
    print("\n" + "=" * 50)
    test_ui_creation()
    
    print("\nTest completed!")