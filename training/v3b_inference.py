#!/usr/bin/env python3
"""V3b: Subsample 1000 frames, run v3 inference, prepare merged dataset."""
import os, sys, random, shutil, json
from pathlib import Path

random.seed(42)

WORK = Path.home() / "vogelhaus" / "v3b_work"
FRAMES = WORK / "motion_frames"
IMAGES = WORK / "images_sampled"
LABELS = WORK / "labels"
V3_MODEL = Path.home() / "vogelhaus" / "training" / "blaumeise_v3" / "weights" / "best.pt"

# Collect all frames
all_frames = []
for vid_dir in sorted(FRAMES.iterdir()):
    if vid_dir.is_dir():
        frames = sorted(vid_dir.glob("*.jpg"))
        all_frames.extend(frames)
        print(f"  {vid_dir.name}: {len(frames)} frames")

print(f"\nTotal frames: {len(all_frames)}")

# Subsample: balanced across videos
MAX = 1000
IMAGES.mkdir(parents=True, exist_ok=True)
LABELS.mkdir(parents=True, exist_ok=True)

# Proportional sampling per video
vid_frames = {}
for f in all_frames:
    vid = f.parent.name
    vid_frames.setdefault(vid, []).append(f)

sampled = []
for vid, frames in vid_frames.items():
    n = max(50, int(MAX * len(frames) / len(all_frames)))  # min 50 per video
    n = min(n, len(frames))
    s = random.sample(frames, n) if len(frames) > n else frames
    sampled.extend(s)
    print(f"  Sampled {len(s)}/{len(frames)} from {vid}")

# Trim to MAX if over
if len(sampled) > MAX:
    sampled = random.sample(sampled, MAX)
print(f"\nFinal sample: {len(sampled)} frames")

# Copy to flat dir with unique names
for f in sampled:
    vid_prefix = f.parent.name[:10]  # date prefix
    dest = IMAGES / f"{vid_prefix}_{f.name}"
    if not dest.exists():
        shutil.copy2(f, dest)

imgs = sorted(IMAGES.glob("*.jpg"))
print(f"Images copied: {len(imgs)}")

# ===== V3 INFERENCE =====
print("\n=== Running v3 inference ===")
sys.path.insert(0, str(Path.home() / "vogelhaus"))
os.chdir(str(Path.home() / "vogelhaus"))

# Activate venv
venv = Path.home() / "vogelhaus" / "venv" / "lib" / "python3.12" / "site-packages"
sys.path.insert(0, str(venv))

from ultralytics import YOLO
model = YOLO(str(V3_MODEL))

results = model.predict(
    source=str(IMAGES),
    conf=0.25,
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
        bird_count += 1
        label_path = LABELS / f"{img_name}.txt"
        with open(label_path, 'w') as f:
            for box in boxes:
                cls = int(box.cls[0])
                x, y, w, h = box.xywhn[0].tolist()
                f.write(f"{cls} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n")
    else:
        empty_count += 1
        label_path = LABELS / f"{img_name}.txt"
        label_path.touch()

print(f"\n=== RESULTS ===")
print(f"Bird:  {bird_count}")
print(f"Empty: {empty_count}")
print(f"Total: {bird_count + empty_count}")
print(f"Bird ratio: {bird_count/(bird_count+empty_count)*100:.1f}%")

summary = {"bird": bird_count, "empty": empty_count, "total": bird_count + empty_count}
with open(WORK / "inference_summary.json", 'w') as f:
    json.dump(summary, f)

print("\nDone! Ready for dataset merge.")
