# Multi-Camera RealSense Action Dataset Collector

A Python-based tool for collecting and processing multi-camera action datasets using Intel RealSense cameras. This system allows you to record synchronized video streams from two RealSense cameras and process them into video files for action recognition tasks.

## Features

- **Dual Camera Recording**: Synchronous recording from two Intel RealSense cameras
- **Action-based Organization**: Supports 15 predefined actions with automatic file organization
- **Parallel Processing**: Efficient batch processing of recorded .bag files to video format
- **Automatic Take Management**: Intelligent numbering system for multiple recordings of the same action

## Supported Actions

1. Pointing
2. Thumbs Up
3. OK Sign
4. Peace Sign
5. Number 3
6. Waving
7. Circular Motion
8. Grasping Pinch
9. Transport Object
10. Release Object
11. Pushing Object
12. Writing/Drawing
13. Cutting with Scissors
14. Thumbs Down
15. Number 1

## Prerequisites

- Intel RealSense cameras (2 units)
- Python 3.x
- Required Python packages:
  - `pyrealsense2`
  - `opencv-python`
  - `numpy`
  - `tqdm`

## Setup

1. **Configure Camera Serial Numbers**: 
   - Edit both `collect_action.py` and `process.py`
   - Update `SERIAL_NUMBER_1` and `SERIAL_NUMBER_2` with your actual camera serial numbers

2. **Install Dependencies**:
   ```bash
   pip install pyrealsense2 opencv-python numpy tqdm
   ```

## Usage

### 1. Data Collection

Run the collection script to record action sequences:

```bash
python collect_action.py
```

- Select an action from the menu (1-15)
- Each recording is 5 seconds long at 640x480 resolution, 15 FPS
- Files are automatically saved as `.bag` files in the `Dataset/` directory
- Take numbers are automatically incremented for repeated recordings

### 2. Data Processing

Convert recorded `.bag` files to video format:

```bash
python process.py
```

- Processes all `.bag` files in the `Dataset/` directory
- Outputs video files to `Dataset_Extracted/` directory
- Uses parallel processing for efficient batch conversion
- Maintains the same directory structure as the input

## File Structure

```
Motion_dataset/
├── collect_action.py          # Data collection script
├── process.py                 # Video processing script
├── Dataset/                   # Raw .bag files organized by action
│   ├── Pointing/
│   ├── Thumbs_Up/
│   └── ...
├── Dataset_Extracted/         # Processed video files
│   ├── Pointing/
│   ├── Thumbs_Up/
│   └── ...
└── README.md
```

## Configuration

### Recording Settings
- **Resolution**: 640x480
- **Frame Rate**: 15 FPS
- **Duration**: 5 seconds per recording
- **Format**: Intel RealSense .bag format

### Processing Settings
- **Parallel Workers**: Uses all available CPU cores by default
- **Output Format**: Standard video files (processed from depth and color streams)

## Notes

- Ensure both cameras are connected and recognized before starting collection
- The system automatically handles file naming and organization
- Processing can be run multiple times safely - it will process any new .bag files
- Large datasets may require significant processing time and storage space 