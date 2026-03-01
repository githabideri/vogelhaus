#!/usr/bin/env python3
"""Build v3b merged dataset and train."""
import os, sys, random, shutil, yaml
from pathlib import Path

random.seed(42)

HOME = Path.home() / "vogelhaus"
TRAINING = HOME / "training"

# Sources
V3_DATASET = TRAINING / "dataset_v3"
V3B_IMAGES = HOME / "v3b_work" / "images_sampled"
V3B_LABELS = HOME / "v3b_work" / "labels"

# Output
MERGED = TRAINING / "dataset_v3b"
MERGED_TRAIN_IMG = MERGED / "train" / "images"
MERGED_TRAIN_LBL = MERGED / "train" / "labels"
MERGED_VAL_IMG = MERGED / "val" / "images"
MERGED_VAL_LBL = MERGED / "val" / "labels"

for d in [MERGED_TRAIN_IMG, MERGED_TRAIN_LBL, MERGED_VAL_IMG, MERGED_VAL_LBL]:
    d.mkdir(parents=True, exist_ok=True)

# === 1. Copy v3 clean dataset (ALL goes to train+val as-is) ===
print("=== Copying v3 clean dataset ===")
for split in ["train", "val"]:
    src_imgs = V3_DATASET / split / "images"
    src_lbls = V3_DATASET / split / "labels"
    dst_imgs = MERGED / split / "images"
    dst_lbls = MERGED / split / "labels"
    count = 0
    for img in sorted(src_imgs.glob("*.jpg")):
        shutil.copy2(img, dst_imgs / img.name)
        lbl = src_lbls / f"{img.stem}.txt"
        if lbl.exists():
            shutil.copy2(lbl, dst_lbls / lbl.name)
        count += 1
    print(f"  v3 {split}: {count} images")

# === 2. Add v3b auto-labeled (85% train, 15% val) ===
print("\n=== Adding v3b auto-labeled frames ===")
v3b_imgs = sorted(V3B_IMAGES.glob("*.jpg"))
random.shuffle(v3b_imgs)
split_idx = int(len(v3b_imgs) * 0.85)
train_imgs = v3b_imgs[:split_idx]
val_imgs = v3b_imgs[split_idx:]

for img in train_imgs:
    shutil.copy2(img, MERGED_TRAIN_IMG / img.name)
    lbl = V3B_LABELS / f"{img.stem}.txt"
    if lbl.exists():
        shutil.copy2(lbl, MERGED_TRAIN_LBL / lbl.name)

for img in val_imgs:
    shutil.copy2(img, MERGED_VAL_IMG / img.name)
    lbl = V3B_LABELS / f"{img.stem}.txt"
    if lbl.exists():
        shutil.copy2(lbl, MERGED_VAL_LBL / lbl.name)

print(f"  v3b train: {len(train_imgs)}")
print(f"  v3b val:   {len(val_imgs)}")

# Count totals
total_train = len(list(MERGED_TRAIN_IMG.glob("*.jpg")))
total_val = len(list(MERGED_VAL_IMG.glob("*.jpg")))
print(f"\n=== Merged dataset ===")
print(f"  Train: {total_train}")
print(f"  Val:   {total_val}")
print(f"  Total: {total_train + total_val}")

# === 3. Write dataset YAML ===
yaml_path = TRAINING / "dataset_v3b.yaml"
config = {
    'path': str(MERGED),
    'train': 'train/images',
    'val': 'val/images',
    'names': {0: 'blaumeise'}
}
with open(yaml_path, 'w') as f:
    yaml.dump(config, f)
print(f"\nYAML: {yaml_path}")

# === 4. Train ===
print("\n=== Starting v3b training ===")
venv = Path.home() / "vogelhaus" / "venv" / "lib" / "python3.12" / "site-packages"
sys.path.insert(0, str(venv))

from ultralytics import YOLO
model = YOLO("yolov8n.pt")

results = model.train(
    data=str(yaml_path),
    epochs=100,
    patience=15,
    batch=16,
    imgsz=640,
    project=str(HOME / "runs" / "detect" / "training"),
    name="blaumeise_v3b",
    exist_ok=True,
    verbose=True,
    device=0,
)

print("\n=== Training complete! ===")
