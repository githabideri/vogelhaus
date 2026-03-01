#!/usr/bin/env python3
"""
V3b Bootstrapping Pipeline:
1. Motion Detection (GPU) on 5 source videos
2. v3 model inference on motion frames -> auto-label
3. Export labeled dataset for merge with v3
"""
import subprocess
import sys
import os
import json
import glob
from pathlib import Path

# Paths
SOURCE_DIR = Path.home() / "vogelhaus" / "v3b_source"
WORK_DIR = Path.home() / "vogelhaus" / "v3b_work"
FRAMES_DIR = WORK_DIR / "motion_frames"
LABELS_DIR = WORK_DIR / "labels"
IMAGES_DIR = WORK_DIR / "images"
V3_MODEL = Path.home() / "vogelhaus" / "training" / "blaumeise_v3" / "weights" / "best.pt"
VENV_PYTHON = Path.home() / "vogelhaus" / "venv" / "bin" / "python"

# Create dirs
for d in [WORK_DIR, FRAMES_DIR, LABELS_DIR, IMAGES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ============ STEP 1: Motion Detection ============
print("=" * 60)
print("STEP 1: GPU Motion Detection on 5 videos")
print("=" * 60)

videos = sorted(SOURCE_DIR.glob("*.mp4"))
print(f"Found {len(videos)} videos")

total_motion_frames = 0
for vid in videos:
    vid_name = vid.stem
    vid_frames_dir = FRAMES_DIR / vid_name
    vid_frames_dir.mkdir(exist_ok=True)
    
    # Check if already processed
    existing = list(vid_frames_dir.glob("*.jpg"))
    if existing:
        print(f"  {vid.name}: {len(existing)} frames already extracted, skipping")
        total_motion_frames += len(existing)
        continue
    
    print(f"  Processing {vid.name}...")
    
    # GPU motion detection using ffmpeg + scene detection
    # Extract frames where significant scene change occurs (motion)
    cmd = [
        "ffmpeg", "-hwaccel", "cuda", "-i", str(vid),
        "-vf", "select='gt(scene,0.008)',showinfo",
        "-vsync", "vfr",
        "-q:v", "2",
        "-frame_pts", "1",
        str(vid_frames_dir / f"{vid_name}_%06d.jpg"),
        "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    extracted = list(vid_frames_dir.glob("*.jpg"))
    total_motion_frames += len(extracted)
    print(f"    -> {len(extracted)} motion frames extracted")

print(f"\nTotal motion frames: {total_motion_frames}")

# ============ STEP 2: Deduplicate / Sample ============
print("\n" + "=" * 60)
print("STEP 2: Collect & deduplicate frames")
print("=" * 60)

all_frames = []
for vid_dir in sorted(FRAMES_DIR.iterdir()):
    if vid_dir.is_dir():
        frames = sorted(vid_dir.glob("*.jpg"))
        all_frames.extend(frames)

print(f"Total motion frames across all videos: {len(all_frames)}")

# If too many, subsample (we want ~500-1000)
import random
random.seed(42)
MAX_FRAMES = 1000
if len(all_frames) > MAX_FRAMES:
    sampled = random.sample(all_frames, MAX_FRAMES)
    print(f"Subsampled to {MAX_FRAMES} frames")
else:
    sampled = all_frames
    print(f"Using all {len(sampled)} frames")

# Copy to flat images dir with unique names
print("Copying to flat structure...")
for f in sampled:
    # Name: video_framenum.jpg
    dest = IMAGES_DIR / f.name
    if not dest.exists():
        import shutil
        shutil.copy2(f, dest)

final_images = list(IMAGES_DIR.glob("*.jpg"))
print(f"Images ready for inference: {len(final_images)}")

# ============ STEP 3: V3 Auto-Label ============
print("\n" + "=" * 60)
print("STEP 3: v3 model inference (auto-labeling)")
print("=" * 60)

# Run YOLO inference
inference_script = f"""
import sys
sys.path.insert(0, '')
from ultralytics import YOLO
from pathlib import Path
import json

model = YOLO('{V3_MODEL}')
images_dir = Path('{IMAGES_DIR}')
labels_dir = Path('{LABELS_DIR}')
labels_dir.mkdir(exist_ok=True)

images = sorted(images_dir.glob('*.jpg'))
print(f'Running v3 inference on {{len(images)}} images...')

results = model.predict(
    source=str(images_dir),
    conf=0.3,
    save=False,
    verbose=False,
    batch=32,
    imgsz=640
)

bird_count = 0
empty_count = 0

for r in results:
    img_name = Path(r.path).stem
    boxes = r.boxes
    
    if len(boxes) > 0:
        # Has detection(s) -> BIRD
        bird_count += 1
        # Save YOLO format label (class x_center y_center width height)
        label_path = labels_dir / f'{{img_name}}.txt'
        with open(label_path, 'w') as f:
            for box in boxes:
                cls = int(box.cls[0])
                x, y, w, h = box.xywhn[0].tolist()
                conf = float(box.conf[0])
                f.write(f'{{cls}} {{x:.6f}} {{y:.6f}} {{w:.6f}} {{h:.6f}}\\n')
    else:
        # No detection -> EMPTY (empty label file = negative sample)
        empty_count += 1
        label_path = labels_dir / f'{{img_name}}.txt'
        label_path.touch()  # Empty file = no objects

print(f'Results: {{bird_count}} bird, {{empty_count}} empty')
print(f'Labels saved to {{labels_dir}}')

# Save summary
summary = {{'bird': bird_count, 'empty': empty_count, 'total': bird_count + empty_count}}
with open(str(labels_dir.parent / 'inference_summary.json'), 'w') as f:
    json.dump(summary, f)
"""

# Write and run inference script
inf_script_path = WORK_DIR / "run_inference.py"
inf_script_path.write_text(inference_script)

result = subprocess.run(
    [str(VENV_PYTHON), str(inf_script_path)],
    capture_output=True, text=True, timeout=600
)
print(result.stdout)
if result.returncode != 0:
    print(f"STDERR: {result.stderr[-500:]}")
    sys.exit(1)

# Load summary
summary_path = WORK_DIR / "inference_summary.json"
if summary_path.exists():
    with open(summary_path) as f:
        summary = json.load(f)
    print(f"\nAuto-label summary: {summary['bird']} bird, {summary['empty']} empty, {summary['total']} total")

print("\n" + "=" * 60)
print("Pipeline complete! Ready for dataset merge + training.")
print("=" * 60)
