# Blaumeise Detection Models

Pre-trained YOLOv8n models fine-tuned for blue tit (*Cyanistes caeruleus*) detection in nest box cameras.

## Models

| Model | Images | Labels | mAP50 | mAP50-95 | Precision | Recall | Notes |
|-------|--------|--------|-------|----------|-----------|--------|-------|
| **v1** | 43 | Auto-curated | 0.599 | 0.222 | — | — | Proof of concept |
| **v2** | 211 | v1-bootstrapped | 0.990* | 0.816 | 0.982 | 0.933 | *Circular validation |
| **v3** | 267 | Human-curated | 0.936 | 0.750 | 0.874 | 0.898 | Clean, honest metrics |
| **v3b** | 1267 | Clean+bootstrap | **0.961** | **0.906** | 0.900 | 0.893 | Production model |

*v2's 0.990 mAP50 is inflated due to circular validation (validation set was also auto-labeled by v1).

## Recommended Model

**Use `v3b/best.pt`** for production — best balance of accuracy and generalization.

## Training Details

- **Architecture:** YOLOv8n (nano, 3M params)
- **Base weights:** COCO pretrained (yolov8n.pt)
- **Hardware:** NVIDIA RTX 3050 8GB
- **Framework:** Ultralytics 8.4.19, PyTorch 2.6.0+cu124
- **Training:** batch=16, imgsz=640, patience=15 (early stopping)
- **Camera:** Raspberry Pi Camera Module 3 (IMX708 Wide), top-down into nest box

## Usage

```python
from ultralytics import YOLO

model = YOLO("models/v3b/best.pt")
results = model.predict("your_image.jpg", conf=0.25)

for r in results:
    if len(r.boxes) > 0:
        print("Blue tit detected!")
    else:
        print("Empty nest box")
```

## License

Models are derivative works of Ultralytics YOLOv8 — **AGPL-3.0**.
Training images are our own material — **CC-BY-SA 4.0**.
