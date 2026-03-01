#!/usr/bin/env python3
"""Build v3 dataset from curated labels + v2 bounding boxes.

For BIRD images: use existing v2 label if available, else run v2 model inference.
For EMPTY images: empty label file (no detections).
Excluded/UNCLEAR images are skipped.
"""
import os
import shutil
import random

CURATION = os.path.expanduser("~/vogelhaus/training/curation_results.txt")
IMAGES_DIR = os.path.expanduser("~/vogelhaus/training/images_v2")
LABELS_V2 = os.path.expanduser("~/vogelhaus/training/labels_v2")
V2_MODEL = os.path.expanduser("~/vogelhaus/training/blaumeise_v2/weights/best.pt")

OUT_BASE = os.path.expanduser("~/vogelhaus/training/dataset_v3")
OUT_TRAIN_IMG = os.path.join(OUT_BASE, "train", "images")
OUT_TRAIN_LBL = os.path.join(OUT_BASE, "train", "labels")
OUT_VAL_IMG = os.path.join(OUT_BASE, "val", "images")
OUT_VAL_LBL = os.path.join(OUT_BASE, "val", "labels")

VAL_RATIO = 0.15  # ~15% for validation
CONF_THRESHOLD = 0.25

def parse_curation(path):
    """Parse curation_results.txt → dict of filename → verdict"""
    results = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|')
            if len(parts) >= 2:
                fname = parts[0].strip()
                verdict = parts[1].strip()
                results[fname] = verdict
    return results

def get_v2_label(fname):
    """Get existing v2 label content if available."""
    label_name = fname.replace('.jpg', '.txt')
    label_path = os.path.join(LABELS_V2, label_name)
    if os.path.exists(label_path):
        with open(label_path) as f:
            content = f.read().strip()
        if content:  # non-empty = has detection
            return content
    return None

def run_v2_inference(image_path):
    """Run v2 model on a single image to get bounding box."""
    from ultralytics import YOLO
    model = YOLO(V2_MODEL)
    results = model(image_path, conf=CONF_THRESHOLD, verbose=False)
    lines = []
    for r in results:
        for box in r.boxes:
            x, y, w, h = box.xywhn[0].tolist()
            lines.append(f"0 {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
    return '\n'.join(lines) if lines else None

def main():
    # Clean output
    for d in [OUT_TRAIN_IMG, OUT_TRAIN_LBL, OUT_VAL_IMG, OUT_VAL_LBL]:
        os.makedirs(d, exist_ok=True)

    curation = parse_curation(CURATION)
    print(f"Loaded {len(curation)} curation entries")

    birds = []
    empties = []
    skipped = 0
    need_inference = []

    for fname, verdict in curation.items():
        img_path = os.path.join(IMAGES_DIR, fname)
        if not os.path.exists(img_path):
            print(f"  SKIP (missing): {fname}")
            skipped += 1
            continue

        if verdict == "BIRD":
            label = get_v2_label(fname)
            if label:
                birds.append((fname, label))
            else:
                need_inference.append(fname)
        elif verdict == "EMPTY":
            empties.append((fname, ""))  # empty label
        else:
            skipped += 1

    print(f"BIRD with existing labels: {len(birds)}")
    print(f"BIRD needing inference: {len(need_inference)}")
    print(f"EMPTY: {len(empties)}")
    print(f"Skipped: {skipped}")

    # Run inference for bird images without labels
    if need_inference:
        print(f"\nRunning v2 inference on {len(need_inference)} images...")
        from ultralytics import YOLO
        model = YOLO(V2_MODEL)
        for fname in need_inference:
            img_path = os.path.join(IMAGES_DIR, fname)
            results = model(img_path, conf=CONF_THRESHOLD, verbose=False)
            lines = []
            for r in results:
                for box in r.boxes:
                    x, y, w, h = box.xywhn[0].tolist()
                    lines.append(f"0 {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
            if lines:
                birds.append((fname, '\n'.join(lines)))
            else:
                # v2 didn't detect anything — use center crop fallback
                birds.append((fname, "0 0.500000 0.500000 0.600000 0.600000"))
                print(f"  Fallback center-crop: {fname}")

    # Combine and split
    all_data = birds + empties
    random.seed(42)
    random.shuffle(all_data)

    n_val = max(1, int(len(all_data) * VAL_RATIO))
    val_data = all_data[:n_val]
    train_data = all_data[n_val:]

    print(f"\nDataset split: {len(train_data)} train / {len(val_data)} val")

    # Write files
    for fname, label in train_data:
        shutil.copy2(os.path.join(IMAGES_DIR, fname), os.path.join(OUT_TRAIN_IMG, fname))
        label_name = fname.replace('.jpg', '.txt')
        with open(os.path.join(OUT_TRAIN_LBL, label_name), 'w') as f:
            f.write(label)

    for fname, label in val_data:
        shutil.copy2(os.path.join(IMAGES_DIR, fname), os.path.join(OUT_VAL_IMG, fname))
        label_name = fname.replace('.jpg', '.txt')
        with open(os.path.join(OUT_VAL_LBL, label_name), 'w') as f:
            f.write(label)

    # Write dataset.yaml
    yaml_path = os.path.join(OUT_BASE, "dataset_v3.yaml")
    with open(yaml_path, 'w') as f:
        f.write(f"path: {OUT_BASE}\n")
        f.write("train: train/images\n")
        f.write("val: val/images\n")
        f.write("nc: 1\n")
        f.write("names: ['blaumeise']\n")
    print(f"Config: {yaml_path}")

    # Stats
    bird_train = sum(1 for _, l in train_data if l.strip())
    empty_train = sum(1 for _, l in train_data if not l.strip())
    bird_val = sum(1 for _, l in val_data if l.strip())
    empty_val = sum(1 for _, l in val_data if not l.strip())
    print(f"\nTrain: {bird_train} bird + {empty_train} empty = {len(train_data)}")
    print(f"Val:   {bird_val} bird + {empty_val} empty = {len(val_data)}")
    print("\nDone! Ready for training.")

if __name__ == "__main__":
    main()
