#!/usr/bin/env python3
"""
YOLO v3b Peak Classification Pipeline
Extracts frames at motion-peak timestamps, runs YOLO bird detection.

Usage:
    python classify_peaks.py <video_path> [--peaks-csv all_peaks.csv] [--model best.pt]
    
Env vars (fallback):
    VOGELHAUS_ANALYSE_DIR  - base dir for analyse results (default: ~/vogelhaus/analyse)
    VOGELHAUS_MODEL        - path to YOLO model (default: ~/vogelhaus/models/blaumeise_v3b/weights/best.pt)

Output: CSV to stdout with columns: video,second,timestamp,motion_score,yolo_conf,yolo_class,bbox
"""

import argparse
import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

def find_peaks(peaks_csv, video_basename):
    """Extract peaks for a specific video from all_peaks.csv"""
    peaks = []
    with open(peaks_csv, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 4:
                continue
            unit_id = row[0]
            if video_basename in unit_id:
                second = int(row[1])
                timestamp = row[2]
                score = float(row[3])
                threshold = float(row[4]) if len(row) > 4 else 0.0
                peaks.append((second, timestamp, score, threshold))
    return peaks

def extract_frames(video_path, seconds, output_dir):
    """Extract frames at given seconds using ffmpeg with fast seeking"""
    frame_paths = []
    for sec in seconds:
        out_path = os.path.join(output_dir, f"frame_{sec:06d}.jpg")
        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", str(sec),
            "-i", str(video_path),
            "-frames:v", "1",
            "-q:v", "2",
            out_path
        ]
        subprocess.run(cmd, check=True, timeout=30)
        frame_paths.append((sec, out_path))
    return frame_paths

def run_yolo(model_path, frame_paths, conf_threshold=0.25, imgsz=640):
    """Run YOLO inference on extracted frames, return detections per frame"""
    from ultralytics import YOLO
    
    model = YOLO(str(model_path))
    
    # Collect all image paths
    images = [fp for _, fp in frame_paths]
    sec_map = {fp: sec for sec, fp in frame_paths}
    
    # Batch inference
    results = model.predict(
        source=images,
        conf=conf_threshold,
        imgsz=imgsz,
        half=True,
        verbose=False,
        device=0
    )
    
    detections = {}
    for i, result in enumerate(results):
        sec = frame_paths[i][0]  # use index, not path (YOLO renames files)
        dets = []
        if result.boxes is not None and len(result.boxes) > 0:
            for box in result.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = result.names[cls_id]
                bbox = box.xyxy[0].tolist()
                bbox_str = f"{bbox[0]:.0f},{bbox[1]:.0f},{bbox[2]:.0f},{bbox[3]:.0f}"
                dets.append((conf, cls_name, bbox_str))
        detections[sec] = dets
    
    return detections

def main():
    parser = argparse.ArgumentParser(description="Classify motion peaks with YOLO")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--peaks-csv", default=None, help="Path to all_peaks.csv")
    parser.add_argument("--model", default=None, help="Path to YOLO model")
    parser.add_argument("--conf", type=float, default=0.25, help="YOLO confidence threshold")
    parser.add_argument("--imgsz", type=int, default=640, help="YOLO input size")
    parser.add_argument("--output", default=None, help="Output CSV path (default: stdout)")
    args = parser.parse_args()
    
    # Resolve paths
    analyse_dir = Path(os.environ.get("VOGELHAUS_ANALYSE_DIR", 
                                       os.path.expanduser("~/vogelhaus/analyse")))
    
    video_path = Path(args.video).resolve()
    if not video_path.exists():
        print(f"ERROR: Video not found: {video_path}", file=sys.stderr)
        sys.exit(1)
    
    peaks_csv = Path(args.peaks_csv) if args.peaks_csv else analyse_dir / "results" / "all_peaks.csv"
    if not peaks_csv.exists():
        print(f"ERROR: Peaks CSV not found: {peaks_csv}", file=sys.stderr)
        sys.exit(1)
    
    model_path = Path(args.model) if args.model else Path(
        os.environ.get("VOGELHAUS_MODEL",
                       os.path.expanduser("~/vogelhaus/models/blaumeise_v3b/weights/best.pt")))
    if not model_path.exists():
        print(f"ERROR: Model not found: {model_path}", file=sys.stderr)
        sys.exit(1)
    
    video_basename = video_path.stem
    
    # 1. Find peaks
    peaks = find_peaks(peaks_csv, video_basename)
    print(f"Found {len(peaks)} peaks for {video_basename}", file=sys.stderr)
    
    if not peaks:
        print("No peaks found, exiting.", file=sys.stderr)
        sys.exit(0)
    
    # 2. Extract frames
    with tempfile.TemporaryDirectory(prefix="yolo_peaks_") as tmpdir:
        seconds = [p[0] for p in peaks]
        print(f"Extracting {len(seconds)} frames...", file=sys.stderr)
        frame_paths = extract_frames(video_path, seconds, tmpdir)
        
        # 3. Run YOLO
        print(f"Running YOLO v3b inference...", file=sys.stderr)
        detections = run_yolo(model_path, frame_paths, args.conf, args.imgsz)
        
        # 4. Output results
        out_file = open(args.output, 'w', newline='') if args.output else sys.stdout
        writer = csv.writer(out_file)
        writer.writerow(["video", "second", "timestamp", "motion_score", "motion_threshold",
                         "bird_detected", "yolo_conf", "yolo_class", "bbox"])
        
        for sec, ts, mscore, mthresh in peaks:
            dets = detections.get(sec, [])
            if dets:
                for conf, cls_name, bbox in dets:
                    writer.writerow([video_basename, sec, ts, f"{mscore:.6f}", 
                                   f"{mthresh:.6f}", "YES", f"{conf:.4f}", cls_name, bbox])
            else:
                writer.writerow([video_basename, sec, ts, f"{mscore:.6f}",
                                f"{mthresh:.6f}", "NO", "", "", ""])
        
        if args.output:
            out_file.close()
            print(f"Results written to {args.output}", file=sys.stderr)
        
        # Summary
        bird_peaks = sum(1 for s in seconds if detections.get(s))
        total = len(seconds)
        print(f"\n=== Summary ===", file=sys.stderr)
        print(f"Total peaks: {total}", file=sys.stderr)
        print(f"Bird detected: {bird_peaks}/{total} ({100*bird_peaks/total:.0f}%)", file=sys.stderr)
        print(f"No bird: {total - bird_peaks}/{total}", file=sys.stderr)

if __name__ == "__main__":
    main()
