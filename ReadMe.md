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
- **Interactive Controls**: Slider-based position and size adjustment

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

## Project Structure

```
oak_camera_viewer/
├── main.py                    # Main application entry point
├── requirements.txt           # Project dependencies
├── README.md                 # This file
├── camera/
│   ├── __init__.py           # Camera module init
│   ├── controller.py         # CameraController class
│   ├── settings.py           # CameraSettingsManager class
│   └── roi_manager.py        # ROIManager class
├── ui/
│   ├── __init__.py           # UI module init
│   ├── display.py            # DisplayManager class
│   ├── controls.py           # ControlPanel class
│   └── roi_controls.py       # ROIControlPanel class
├── utils/
│