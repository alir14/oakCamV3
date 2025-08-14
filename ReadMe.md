# OAK PoE Camera Viewer

A comprehensive Windows application for Luxonis OAK PoE cameras using DepthAI V3.

## Features

### 🎥 **Multi-Camera Support**
- Automatic detection of cameras A, B, and C
- Tabbed interface for easy camera switching
- Real-time preview with FPS monitoring
- Simultaneous capture from all cameras

### ⚙️ **Complete Camera Controls**
- **Auto/Manual modes** for exposure, focus, and white balance
- **Real-time adjustment** of all camera parameters:
  - Exposure time (1-33000 μs)
  - ISO sensitivity (100-1600)
  - Manual focus (0-255)
  - Brightness, contrast, saturation (-10 to 10)
  - Sharpness (0-4)
  - White balance (1000-12000K)
  - Luma/Chroma denoise (0-4)

### 🎯 **ROI (Region of Interest) Controls**
- **ROI-based Exposure**: Set exposure metering region for better exposure control
- **ROI-based Focus**: Use ROI for autofocus targeting
- **Visual Overlay**: Real-time ROI rectangle display on camera feeds
- **Per-Camera Settings**: Independent ROI settings for each camera
- **Exposure Compensation**: Fine-tune exposure within ROI (-9 to +9)
- **🖱️ Mouse ROI Selection**: Click and drag on CAM_A display to select ROI region
  - Enable "Mouse ROI Selection" in ROI controls
  - Click and drag on camera display to define ROI area
  - ROI is automatically applied and enabled
  - Visual feedback during selection process
  - **Repeat Functionality**: ROI works every time you select a new region
  - **Enhanced Logging**: Console output shows all ROI changes and applications

### 📸 **Capture Capabilities**
- **Image Capture**: Synchronized capture from all cameras
- **Video Recording**: Multi-camera video recording
- **Flexible Formats**: Support for JPG, PNG, BMP, TIFF
- **Multiple Codecs**: MJPG, XVID, MP4V, H264
- **Automatic Timestamping**: All files include capture timestamp

### 🖥️ **User Interface**
- **Modern GUI**: Clean, intuitive interface
- **Real-time Feedback**: Live FPS and connection status
- **Keyboard Shortcuts**: Quick access to common functions
- **Status Monitoring**: Disk space and recording duration
- **Error Handling**: Comprehensive error reporting

## Installation

### Prerequisites
- Python 3.8 or higher
- OAK PoE camera connected to network
- Windows 10/11 (primary target)

### Setup

1. **Clone or download the project files**
2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
python main.py
```

4. **Test ROI functionality (optional):**
```bash
python test_roi.py
```

5. **Test Mouse ROI functionality (optional):**
```bash
python test_mouse_roi.py
```

6. **Test ROI repeat functionality (optional):**
```bash
python test_roi_repeat.py
```

## Usage

### ROI (Region of Interest) Controls

The application provides mouse-based ROI selection for intuitive region selection:

#### Mouse Selection Method
1. Go to the "ROI" tab in the control panel
2. Enable "Mouse ROI Selection"
3. Click and drag on the CAM_A camera display to select the ROI region
4. Release the mouse to automatically apply the ROI
5. The ROI will be enabled and applied to the camera immediately
6. Use the exposure compensation slider to fine-tune exposure within the ROI
7. Enable "Use for Focus" if you want the ROI to also control autofocus

**Note**: Mouse ROI selection is only available for CAM_A and provides the most intuitive way to set ROI regions.

## Project Structure

```
oak_camera_viewer/
├── main.py                    # Main application entry point
├── requirements.txt           # Project dependencies
├── README.md                 # This file
├── test_roi.py               # ROI functionality test
├── test_mouse_roi.py         # Mouse ROI functionality test
├── test_roi_repeat.py        # ROI repeat functionality test
├── camera/
│   ├── __init__.py           # Camera module init
│   ├── controller.py         # CameraController class
│   ├── settings.py           # CameraSettingsManager class
│   └── roi_manager.py        # ROIManager class (includes mouse ROI)
├── ui/
│   ├── __init__.py           # UI module init
│   ├── display.py            # DisplayManager class (includes mouse events)
│   ├── controls.py           # ControlPanel class
│   └── roi_controls.py       # ROIControlPanel class (includes mouse toggle)
├── utils/
│   ├── __init__.py           # Utils module init
│   └── file_manager.py       # FileManager class
└── GPS/
    ├── gps_integration.py    # GPS integration
    └── gps_data_capture.py   # GPS data capture
```

## Keyboard Shortcuts

- `Ctrl+C`: Capture images
- `Ctrl+R`: Toggle recording
- `Ctrl+D`: Disconnect camera
- `Ctrl+N`: Connect camera
- `Ctrl+Q`: Quit application
- `F5`: Refresh displays

## Troubleshooting

### ROI Issues
- **ROI not working**: Ensure CAM_A is connected and ROI is enabled
- **Mouse selection not working**: Check that "Mouse ROI Selection" is enabled in ROI controls
- **ROI overlay not visible**: Enable "Show ROI Overlay" in ROI controls
- **ROI only works once**: This issue has been fixed - ROI now works every time you select a new region
- **Check console logs**: Enhanced logging shows all ROI changes and applications in the console output

### Camera Connection Issues
- Check network connection to OAK camera
- Verify camera IP address in settings
- Ensure DepthAI drivers are installed

## Contributing

This project is based on the Luxonis depthai-core examples, particularly the `camera_roi_exposure_focus.py` example. The mouse ROI functionality implements the same logic as the original Luxonis example but integrated into a full GUI application.

## License

This project is provided as-is for educational and development purposes.