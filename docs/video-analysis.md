# Video-Analyse — Bewegungserkennung

## Übersicht

Zwei Analyse-Varianten für das Vogelhaus-Videomaterial:

| Variante | Hardware | Geschwindigkeit | Script |
|----------|----------|----------------|--------|
| Pi4 (CPU) | Raspberry Pi 4 | ~2.4× Echtzeit | `scripts/motion-detect-fast.py` |
| GPU (NVDEC) | NVIDIA GPU + WSL2 | ~25× Echtzeit | `scripts/motion-detect-gpu.py` |

## GPU-Variante (empfohlen für Backlog)

### Voraussetzungen

- NVIDIA GPU mit NVDEC-Support (z.B. RTX 3050+)
- ffmpeg mit CUDA/NVDEC (`h264_cuvid`)
- Python 3 + numpy
- WSL2 (Windows) oder native Linux

### Verwendung

```bash
# Standard: 1 fps Sampling, GPU-Decoding
python3 scripts/motion-detect-gpu.py video.mp4

# Höhere Abtastrate
python3 scripts/motion-detect-gpu.py video.mp4 --fps 2

# Ohne GPU (CPU-Fallback)
python3 scripts/motion-detect-gpu.py video.mp4 --no-gpu

# Manueller Schwellwert
python3 scripts/motion-detect-gpu.py video.mp4 --threshold 0.03
```

### Ausgabe

- **Konsole:** Fortschritt + Top-N Peaks mit Zeitstempeln
- **CSV:** `<video>_motion.csv` mit Bewegungs-Score pro Sekunde

### Wie es funktioniert

1. ffmpeg dekodiert das Video per GPU (h264_cuvid) und skaliert auf 640×360
2. Pro Sekunde wird ein Graustufenframe extrahiert
3. Pixel-Differenz zum Vorgängerframe = Bewegungs-Score
4. Scores über Schwellwert (mean + 2×std) = potenzielle Vogelaktivität

### Typische Scores

| Ereignis | Score |
|----------|-------|
| Ruhiges Bild | 0.005–0.015 |
| Lichtwechsel | 0.02–0.04 |
| Vogelbesuch | 0.05–0.25 |

### Performance-Benchmarks

| Hardware | Video | Dauer | Speed |
|----------|-------|-------|-------|
| Pi4 (CPU) | 1h | ~25 min | 2.4× |
| RTX 3050 (GPU) | 1h | ~2:20 | 25.8× |

### Nächste Schritte

- **Stufe 2:** YOLOv8-nano auf erkannte Stellen für Vogelklassifikation
- **Batch-Pipeline:** Ganzen Backlog automatisch durchlaufen
- **Highlight-Viewer:** Gefundene Stellen automatisch abspielen (mpv)

## Pi4-Variante (für Live-Monitoring)

Siehe `scripts/motion-detect-fast.py` — verwendet MOG2 Background-Subtraction,
läuft direkt auf dem Pi4 gegen den RTSP-Stream.
