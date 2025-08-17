# Models Directory

This directory contains neural network models for the OAK camera viewer application.

## Ultra-Fast Lane Detection Model

### Download Instructions

1. **Visit the Luxonis Model Zoo**: Go to [Luxonis Model Zoo](https://zoo.luxonis.com/)

2. **Search for Ultra-Fast Lane Detection**: Look for the ultra-fast-lane-detection model

3. **Download the .blob file**: Download the compiled model file for OAK cameras

4. **Place in this directory**: Save the file as `ultra_fast_lane_detection.blob`

### Alternative: Convert from ONNX

If you have the ONNX model:

1. **Install DepthAI Model Converter**:
   ```bash
   pip install depthai-model-converter
   ```

2. **Convert the model**:
   ```bash
   depthai-model-converter -m path/to/ultra_fast_lane_detection.onnx -o models/
   ```

### Model Requirements

- **Input Size**: 800x288 pixels
- **Input Format**: BGR888
- **Output**: Lane detection probabilities
- **Supported Cameras**: CAM_A (primary)

### File Structure

```
models/
├── README.md
├── ultra_fast_lane_detection.blob  # Download this file
└── (other models...)
```

### Testing the Model

Use the test script to verify the model works:

```bash
python test_lane_detection.py
```
