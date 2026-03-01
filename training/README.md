# Training Pipeline — Blaumeise Detection

Complete training pipeline for fine-tuning YOLOv8n on nest box camera footage.

## Dataset Evolution

### v1 → v2 → v3 → v3b

1. **v1 (43 images):** Motion detection on sample video → manual curation → auto-label with center-crop fallback
2. **v2 (211 images):** v1 as auto-labeler on 5x more data → semi-supervised bootstrapping
3. **v3 (267 images):** ALL images manually reviewed by humans (VHW + Martin). 14.5% of auto-labels were wrong!
4. **v3b (1267 images):** v3-clean + 1000 auto-labeled frames from 5 diverse NAS videos → massive mAP50-95 improvement

### Key Insight

v2 achieved 0.99 mAP50 — but this was **circular validation** (validation set was also auto-labeled). v3 with clean human labels dropped to 0.936, confirming overfitting concerns. v3b recovered to 0.961 with honest bootstrapping.

## Directory Structure

```
training/
├── dataset_v3/          # Clean human-curated dataset (267 images)
│   ├── train/images/    # 227 training images
│   ├── train/labels/    # YOLO format labels
│   ├── val/images/      # 40 validation images
│   └── val/labels/
├── dataset_v3b/         # Bootstrapped dataset (1267 images)
│   ├── train/images/    # 1077 training images
│   ├── train/labels/
│   ├── val/images/      # 190 validation images
│   └── val/labels/
├── images_v2/           # All 341 source images (v2 pool)
├── labels_v2/           # Original v2 auto-labels
├── curation_results.txt # Human review verdicts for all 269 images
├── corrections_list.txt # Specific label corrections
├── build_v3_dataset.py  # Builds v3 dataset from curation results
├── v3b_pipeline.py      # Frame extraction + motion detection
├── v3b_inference.py     # v3 model inference for auto-labeling
├── v3b_build_and_train.py # Builds merged dataset + trains v3b
├── review_korrekturen/  # Contact sheet montages used for review
└── *.yaml               # Dataset configuration files
```

## Reproducing Training

### Prerequisites

```bash
# Python 3.12+ with venv
python3 -m venv venv
source venv/bin/activate

# IMPORTANT: Install PyTorch CUDA first (separately!) to avoid OOM
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install ultralytics opencv-python
```

### Train v3 (clean labels)

```bash
yolo detect train data=training/dataset_v3.yaml model=yolov8n.pt \
  epochs=100 patience=15 batch=16 imgsz=640
```

### Train v3b (bootstrapped)

```bash
yolo detect train data=training/dataset_v3b.yaml model=yolov8n.pt \
  epochs=100 patience=15 batch=16 imgsz=640
```

## Label Format

YOLO format: `class x_center y_center width height` (normalized 0-1).
Single class: `0` = blaumeise (blue tit).
Empty label files = negative samples (no bird present).

## License

- **Code/Scripts:** AGPL-3.0 (Ultralytics derivative)
- **Images/Dataset:** CC-BY-SA 4.0
- **Models:** AGPL-3.0
