# Video Analysis — Motion Detection

> Last updated: 2026-03

## Overview

Two analysis variants for processing Vogelhaus video material:

| Variant | Hardware | Speed | Script |
|---------|----------|-------|---------|
| Pi4 (CPU) | Raspberry Pi 4 | ~2.4× realtime | `scripts/motion-detect-fast.py` |
| GPU (NVDEC) | NVIDIA GPU + WSL2 | ~25× realtime | `scripts/motion-detect-gpu.py` |

## GPU Variant (Recommended for Backlog)

### Prerequisites

- NVIDIA GPU with NVDEC support (e.g., RTX 3050+)
- ffmpeg with CUDA/NVDEC (`h264_cuvid`)
- Python 3 + numpy
- WSL2 (Windows) or native Linux

### Usage

```bash
# Standard: 1 fps sampling, GPU decoding
python3 scripts/motion-detect-gpu.py video.mp4

# Higher sampling rate
python3 scripts/motion-detect-gpu.py video.mp4 --fps 2

# Without GPU (CPU fallback)
python3 scripts/motion-detect-gpu.py video.mp4 --no-gpu

# Manual threshold
python3 scripts/motion-detect-gpu.py video.mp4 --threshold 0.03
```

### Output

- **Console**: Progress + Top-N peaks with timestamps
- **CSV**: `<video>_motion.csv` with motion score per second

### How It Works

1. ffmpeg decodes video via GPU (h264_cuvid) and scales to 640×360
2. One grayscale frame extracted per second
3. Pixel difference to previous frame = motion score
4. Scores above threshold (mean + 2×std) = potential bird activity

### Typical Scores

| Event | Score |
|-------|-------|
| Calm scene | 0.005–0.015 |
| Light change | 0.02–0.04 |
| Bird visit | 0.05–0.25 |

### Performance Benchmarks

| Hardware | Video | Duration | Speed |
|----------|-------|----------|-------|
| Pi4 (CPU) | 1h | ~25 min | 2.4× |
| RTX 3050 (GPU) | 1h | ~2:20 | 25.8× |

## Pi4 Variant (Live Monitoring)

See `scripts/motion-detect-fast.py` — uses MOG2 background subtraction,
runs directly on Pi4 against RTSP stream.

### Implementation

```python
import cv2
import numpy as np

# Connect to RTSP stream
cap = cv2.VideoCapture('rtsp://127.0.0.1:8554/vogl-noir')

# Background subtractor
backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Apply background subtraction
    fgMask = backSub.apply(frame)
    
    # Calculate motion percentage
    motion_pixels = cv2.countNonZero(fgMask)
    total_pixels = fgMask.shape[0] * fgMask.shape[1]
    motion_percentage = motion_pixels / total_pixels
    
    # Trigger on significant motion
    if motion_percentage > 0.02:  # 2% of frame changed
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f'Motion detected at {timestamp}: {motion_percentage:.3f}')
```

## Advanced Analysis Pipeline

### Stage 1: Motion Detection

Fast screening to identify time periods with activity:

```bash
# Process entire video archive
for video in /srv/ssd/recordings/*.mp4; do
    python3 scripts/motion-detect-gpu.py "$video"
done

# Merge results
cat /srv/ssd/recordings/*_motion.csv > motion_summary.csv
```

### Stage 2: Bird Classification

Apply YOLOv8-nano to detected motion segments:

```bash
# Install YOLOv8
pip install ultralytics

# Run classification on high-motion segments
python3 scripts/bird-classify.py motion_summary.csv
```

### Stage 3: Highlight Generation

Create summary videos of detected bird activity:

```bash
# Generate highlight reel
python3 scripts/create-highlights.py motion_summary.csv --min-score 0.05
```

## Real-time Analysis

### Live Stream Processing

Monitor RTSP streams in real-time:

```bash
# Monitor Pi Zero camera
python3 scripts/motion-detect-fast.py rtsp://127.0.0.1:8554/vogl-noir

# Monitor Pi4 camera
python3 scripts/motion-detect-fast.py rtsp://127.0.0.1:8554/vogl-cam
```

### Alert System

Trigger notifications on bird detection:

```python
# Integration with motion detection
def on_motion_detected(score, timestamp):
    if score > 0.08:  # High confidence bird activity
        # Save snapshot
        save_snapshot(timestamp)
        
        # Send notification
        send_alert(f"Bird detected at {timestamp}, score: {score:.3f}")
        
        # Log to database
        log_detection(timestamp, score)
```

## GPU Acceleration Setup

### NVIDIA Setup (WSL2)

See [WSL GPU Analysis Setup](../setup/wsl-gpu-analysis.md) for detailed instructions.

Quick verification:
```bash
# Test GPU acceleration
ffmpeg -f lavfi -i testsrc -t 10 -c:v h264_nvenc test_gpu.mp4

# Test decoding
ffmpeg -c:v h264_cuvid -i test_gpu.mp4 -f null -
```

### CPU-Only Fallback

For systems without GPU acceleration:

```bash
# Use software decoding
python3 scripts/motion-detect-gpu.py video.mp4 --no-gpu

# Adjust processing to match available resources
python3 scripts/motion-detect-gpu.py video.mp4 --fps 0.5 --resolution 320x180
```

## Analysis Results

### Motion Score Interpretation

| Score Range | Interpretation | Typical Cause |
|-------------|---------------|---------------|
| 0.000–0.010 | No activity | Static scene |
| 0.010–0.030 | Minimal motion | Wind, lighting changes |
| 0.030–0.060 | Moderate motion | Small animals, insects |
| 0.060–0.150 | Significant motion | Bird entry/exit |
| 0.150+ | High motion | Multiple birds, activity |

### Common False Positives

- **Lighting changes**: Clouds, sunrise/sunset
- **Camera movement**: Wind affecting mounting
- **Insects**: Close to camera, appear large
- **Shadows**: Moving shadows from nearby objects

### Filtering Strategies

```python
# Temporal filtering
def filter_motion_events(scores, min_duration=2.0):
    """Filter out brief motion events"""
    filtered = []
    for start, end, score in scores:
        if end - start >= min_duration:
            filtered.append((start, end, score))
    return filtered

# Consistency filtering
def require_consistent_motion(scores, window=5):
    """Require motion in multiple consecutive frames"""
    consistent = []
    for i in range(len(scores) - window + 1):
        window_scores = scores[i:i+window]
        if all(s > threshold for s in window_scores):
            consistent.append(scores[i])
    return consistent
```

## Integration with Vogelhaus System

### Automated Analysis

Set up cron job for regular analysis:

```bash
# /etc/crontab entry
0 6 * * * vogl python3 /home/vogl/scripts/daily-analysis.py
```

### Storage Management

Archive analyzed videos to NAS:

```bash
# Move processed videos
rsync -av /srv/ssd/recordings/ /mnt/nas/archive/

# Clean up local storage
find /srv/ssd/recordings/ -name "*.mp4" -mtime +7 -delete
```

### Dashboard Integration

Display analysis results in web dashboard:

```javascript
// Fetch latest detections
fetch('/api/detections/today')
  .then(response => response.json())
  .then(data => updateChart(data));
```

## Future Enhancements

### Machine Learning Integration

- **Species identification**: Train model on local bird species
- **Behavior analysis**: Feeding, nesting, territorial behaviors  
- **Activity patterns**: Seasonal and daily patterns

### Advanced Features

- **Multi-camera correlation**: Analyze multiple streams simultaneously
- **Weather integration**: Correlate activity with weather data
- **Sound analysis**: Combine video with audio detection

### Performance Optimization

- **Incremental processing**: Only analyze new recordings
- **Adaptive thresholds**: Adjust based on lighting conditions
- **Distributed processing**: Use multiple GPUs or cloud processing