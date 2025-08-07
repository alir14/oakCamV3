#!/usr/bin/env python3
"""
Camera Diagnostic Tool
This script helps diagnose camera connection issues with OAK devices
"""

import sys
import time


def test_basic_import():
    """Test if DepthAI can be imported"""
    print("Testing DepthAI import...")
    try:
        import depthai as dai

        print(f"✓ DepthAI imported successfully - Version: {dai.__version__}")
        return True, dai
    except ImportError as e:
        print(f"✗ Failed to import DepthAI: {e}")
        return False, None


def test_device_connection():
    """Test device connection"""
    print("\nTesting device connection...")
    try:
        import depthai as dai

        # Try to create device
        device = dai.Device()
        print("✓ Device object created successfully")

        # Get device info
        try:
            platform = device.getPlatform()
            print(f"✓ Device platform: {platform.name}")
        except Exception as e:
            print(f"⚠ Could not get platform info: {e}")

        # Get connected cameras
        try:
            cameras = device.getConnectedCameras()
            if cameras:
                print(f"✓ Found {len(cameras)} cameras:")
                for i, cam in enumerate(cameras):
                    print(f"  - Camera {i+1}: {cam.name} on socket {cam}")
            else:
                print("✗ No cameras found")
                return False, None
        except Exception as e:
            print(f"✗ Failed to get cameras: {e}")
            return False, None

        return True, device

    except Exception as e:
        print(f"✗ Device connection failed: {e}")
        return False, None


def test_simple_pipeline(device):
    """Test a simple pipeline setup"""
    print("\nTesting pipeline setup...")
    try:
        import depthai as dai

        # Create pipeline exactly like camera_all.py
        pipeline = dai.Pipeline(device)
        print("✓ Pipeline created with device context")

        # Get cameras and create nodes
        cameras = device.getConnectedCameras()
        camera_nodes = {}

        for socket in cameras:
            socket_name = socket.name
            print(f"  Setting up {socket_name}...")

            # Create camera node exactly like camera_all.py
            cam = pipeline.create(dai.node.Camera).build(socket)
            camera_nodes[socket_name] = cam

            # Use full resolution output like camera_all.py
            output_queue = cam.requestFullResolutionOutput().createOutputQueue()
            print(f"  ✓ {socket_name} configured with full resolution")

        print("✓ Pipeline setup successful")

        # Try to start pipeline
        print("  Testing pipeline start...")
        pipeline.start()
        print("  ✓ Pipeline started")

        # Brief test run
        print("  Running brief test (3 seconds)...")
        time.sleep(3)

        pipeline.stop()
        print("  ✓ Pipeline stopped")

        return True

    except RuntimeError as e:
        if "in use" in str(e):
            print(f"✗ Device is in use by another application")
            print("  Please close all other camera applications and try again")
        else:
            print(f"✗ Pipeline test failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Pipeline test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_frame_capture(device):
    """Test actual frame capture"""
    print("\nTesting frame capture...")
    try:
        import depthai as dai
        import cv2

        # Simple pipeline exactly like camera_all.py
        pipeline = dai.Pipeline(device)
        cameras = device.getConnectedCameras()
        output_queues = {}

        for socket in cameras:
            cam = pipeline.create(dai.node.Camera).build(socket)
            output_queues[socket.name] = (
                cam.requestFullResolutionOutput().createOutputQueue()
            )

        print(f"  Created queues for {len(output_queues)} cameras")

        pipeline.start()
        print("  Pipeline started, capturing frames...")

        frame_count = 0
        start_time = time.time()

        # Try to get frames for 5 seconds
        while time.time() - start_time < 5.0 and frame_count < 10:
            for name, queue in output_queues.items():
                if queue.has():
                    frame = queue.get()
                    img = frame.getCvFrame()
                    print(f"  ✓ Got frame from {name}: {img.shape}")
                    frame_count += 1
            time.sleep(0.1)

        pipeline.stop()

        if frame_count > 0:
            print(f"✓ Successfully captured {frame_count} frames")
            return True
        else:
            print("✗ No frames captured")
            return False

    except Exception as e:
        print(f"✗ Frame capture failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_diagnostics():
    """Run all diagnostic tests"""
    print("OAK Camera Diagnostic Tool")
    print("=" * 50)

    # Test 1: Import
    success, dai_module = test_basic_import()
    if not success:
        print("\n❌ CRITICAL: Cannot import DepthAI")
        print("Install with: pip install depthai==3.0.0rc2")
        return

    # Test 2: Device connection
    success, device = test_device_connection()
    if not success:
        print("\n❌ CRITICAL: Cannot connect to device")
        print("Check:")
        print("- OAK camera is connected (USB/PoE)")
        print("- No other applications are using the camera")
        print("- Device drivers are installed")
        return

    # Test 3: Pipeline setup
    success = test_simple_pipeline(device)
    if not success:
        print("\n❌ CRITICAL: Pipeline setup failed")
        print("This may indicate hardware or driver issues")
        return

    # Test 4: Frame capture
    success = test_frame_capture(device)
    if not success:
        print("\n❌ WARNING: Frame capture failed")
        print("Camera may not be streaming properly")
    else:
        print("\n✅ ALL TESTS PASSED")
        print("Your OAK camera should work with the application")

    print("\n" + "=" * 50)
    print("Diagnostic complete")


if __name__ == "__main__":
    try:
        run_diagnostics()
    except KeyboardInterrupt:
        print("\nDiagnostic interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error during diagnostics: {e}")
        import traceback

        traceback.print_exc()

    input("\nPress Enter to exit...")
