#!/usr/bin/env python3
"""
batch_motion_v2.py — Multi-Format Motion Detection
Supports three NAS video formats:
  1. Clip collections: YYYY-MM-DD/HH/vogl_cam/*.mp4 (1.9 MB clips)
  2. Transition: YYYY-MM-DD/*.mp4 (mixed)
  3. Hourly videos: YYYY-MM-DD/YYYY-MM-DD_HH-43-*.mp4 (2.6 GB)
"""

import cv2
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
import sys
import argparse

# ============================================================
# CONFIG
# ============================================================

NAS_BASE = Path("/mnt/nas/Voglberry Videos")
RESULTS_DIR = Path.home() / "vogelhaus" / "analyse" / "results"
STATUS_FILE = Path.home() / "vogelhaus" / "analyse" / "batch_status.json"
COMPLETED_FILE = Path.home() / "vogelhaus" / "analyse" / "completed.txt"
ALL_PEAKS_CSV = RESULTS_DIR / "all_peaks.csv"

MOTION_THRESHOLD = 0.001
MIN_AREA = 100
SAMPLE_RATE = 1  # Process every Nth frame

# ============================================================
# INVENTORY BUILDER
# ============================================================

def build_inventory():
    """Build inventory for all three video formats"""
    units = []
    print(f"🔍 Scanning {NAS_BASE}...", file=sys.stderr)
    
    for day_dir in sorted(NAS_BASE.glob("2025-*")):
        day = day_dir.name
        
        # Format 3: Hourly videos (Apr 22+)
        # Pattern: 2025-04-22/2025-04-22_HH-43-MM-*.mp4
        hourly_videos = {}
        for vid in day_dir.glob(f"{day}_*-43-*.mp4"):
            try:
                # Extract hour from filename: 2025-04-22_05-43-02-695894.mp4
                hour_str = vid.stem.split('_')[1].split('-')[0]
                hour = int(hour_str)
                hourly_videos[hour] = vid
            except (IndexError, ValueError):
                continue
        
        for hour in sorted(hourly_videos.keys()):
            units.append({
                'id': f"{day}/h{hour:02d}",
                'type': 'hourly_video',
                'path': hourly_videos[hour],
                'size': hourly_videos[hour].stat().st_size
            })
        
        # Format 1: Clip collections (Mar 15 – Apr 19)
        # Pattern: 2025-03-23/04/vogl_cam/*.mp4
        for hour_dir in sorted(day_dir.glob("[0-2][0-9]")):
            try:
                hour = int(hour_dir.name)
            except ValueError:
                continue
            
            vogl_cam = hour_dir / "vogl_cam"
            if vogl_cam.exists():
                clips = sorted(vogl_cam.glob("*.mp4"))
                if clips:
                    units.append({
                        'id': f"{day}/h{hour:02d}",
                        'type': 'clip_collection',
                        'clips': clips,
                        'count': len(clips)
                    })
    
    print(f"✅ Found {len(units)} units", file=sys.stderr)
    return units


# ============================================================
# MOTION DETECTION
# ============================================================

def detect_motion_video(video_path):
    """Process single video file"""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return []
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    prev_gray = None
    peaks = []
    frame_idx = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_idx % SAMPLE_RATE == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if prev_gray is not None:
                diff = cv2.absdiff(prev_gray, gray)
                thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                motion_pixels = 0
                for c in contours:
                    if cv2.contourArea(c) > MIN_AREA:
                        motion_pixels += cv2.contourArea(c)
                
                if motion_pixels > 0:
                    h, w = gray.shape
                    score = motion_pixels / (h * w)
                    
                    if score >= MOTION_THRESHOLD:
                        timestamp = frame_idx / fps
                        peaks.append({
                            'timestamp': timestamp,
                            'score': score,
                            'frame': frame_idx
                        })
            
            prev_gray = gray
        
        frame_idx += 1
    
    cap.release()
    return peaks


def detect_motion_clips(clips):
    """Process multiple clip files as one unit"""
    all_peaks = []
    cumulative_time = 0.0
    
    for clip_path in clips:
        cap = cv2.VideoCapture(str(clip_path))
        if not cap.isOpened():
            continue
        
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
        
        prev_gray = None
        frame_idx = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % SAMPLE_RATE == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)
                
                if prev_gray is not None:
                    diff = cv2.absdiff(prev_gray, gray)
                    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    motion_pixels = 0
                    for c in contours:
                        if cv2.contourArea(c) > MIN_AREA:
                            motion_pixels += cv2.contourArea(c)
                    
                    if motion_pixels > 0:
                        h, w = gray.shape
                        score = motion_pixels / (h * w)
                        
                        if score >= MOTION_THRESHOLD:
                            timestamp = cumulative_time + (frame_idx / fps)
                            all_peaks.append({
                                'timestamp': timestamp,
                                'score': score,
                                'clip': clip_path.name
                            })
                
                prev_gray = gray
            
            frame_idx += 1
        
        cap.release()
        cumulative_time += duration
    
    return all_peaks


# ============================================================
# BATCH PROCESSING
# ============================================================

def load_status():
    """Load batch status"""
    if STATUS_FILE.exists():
        with open(STATUS_FILE) as f:
            return json.load(f)
    return None


def save_status(status):
    """Save batch status"""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)


def load_completed():
    """Load list of completed units"""
    if COMPLETED_FILE.exists():
        with open(COMPLETED_FILE) as f:
            return set(line.strip() for line in f)
    return set()


def mark_completed(unit_id):
    """Mark unit as completed"""
    COMPLETED_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COMPLETED_FILE, 'a') as f:
        f.write(f"{unit_id}\n")


def process_batch():
    """Process all videos"""
    units = build_inventory()
    completed = load_completed()
    
    # Filter out completed
    todo = [u for u in units if u['id'] not in completed]
    
    if not todo:
        print("✅ All units processed!", file=sys.stderr)
        return
    
    print(f"📊 {len(todo)} units to process (out of {len(units)} total)", file=sys.stderr)
    
    # Resume from status or start fresh
    status = load_status()
    if status:
        start_idx = next((i for i, u in enumerate(todo) if u['id'] == status['current']), 0)
        print(f"📍 Resuming from {status['current']} (unit {start_idx+1}/{len(todo)})", file=sys.stderr)
    else:
        start_idx = 0
        status = {
            'started': datetime.now().isoformat(),
            'current': todo[0]['id'],
            'done': len(completed),
            'total': len(units),
            'peaks': 0
        }
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Open CSV for appending
    csv_existed = ALL_PEAKS_CSV.exists()
    csv_file = open(ALL_PEAKS_CSV, 'a')
    if not csv_existed:
        csv_file.write("unit_id,timestamp,score,video_hours\n")
    
    start_time = datetime.now()
    video_hours_done = 0.0
    
    for idx, unit in enumerate(todo[start_idx:], start=start_idx):
        unit_id = unit['id']
        print(f"\n🐦 [{idx+1}/{len(todo)}] {unit_id}...", file=sys.stderr)
        
        # Detect motion
        if unit['type'] == 'hourly_video':
            peaks = detect_motion_video(unit['path'])
            duration_hours = 1.0  # Approximation
        elif unit['type'] == 'clip_collection':
            peaks = detect_motion_clips(unit['clips'])
            duration_hours = len(unit['clips']) * 10 / 3600  # ~10 sec clips
        else:
            continue
        
        # Save peaks to CSV
        for p in peaks:
            ts = p['timestamp']
            mm = int(ts // 60)
            ss = int(ts % 60)
            csv_file.write(f"{unit_id},{ts:.2f},{p['score']:.4f},{duration_hours:.1f}\n")
        
        csv_file.flush()
        
        # Update status
        video_hours_done += duration_hours
        elapsed = datetime.now() - start_time
        elapsed_sec = elapsed.total_seconds()
        speed = video_hours_done / (elapsed_sec / 3600) if elapsed_sec > 0 else 0
        
        remaining_units = len(todo) - (idx + 1)
        eta_sec = (remaining_units / speed) * 3600 if speed > 0 else 0
        
        status.update({
            'current': unit_id,
            'last_id': unit_id,
            'done': len(completed) + idx + 1,
            'hours_done': f"{video_hours_done:.1f}",
            'peaks': status['peaks'] + len(peaks),
            'elapsed': str(elapsed).split('.')[0],
            'eta': str(timedelta(seconds=int(eta_sec))),
            'speed': f"{speed:.1f}",
            'last_peaks': [f"{int(p['timestamp']//60):02d}:{int(p['timestamp']%60):02d} (score={p['score']:.4f})" for p in peaks[-5:]],
            'last_update': datetime.now().isoformat()
        })
        save_status(status)
        
        # Mark as done
        mark_completed(unit_id)
        print(f"  ✅ {len(peaks)} peaks, {duration_hours:.1f}h, speed {speed:.1f}× RT", file=sys.stderr)
    
    csv_file.close()
    print("\n🎉 Batch processing complete!", file=sys.stderr)


def show_status():
    """Display current status"""
    status = load_status()
    if not status:
        print("No active batch")
        return
    
    print("=" * 60)
    print("🐦 VOGELHAUS BATCH MOTION DETECTION — STATUS")
    print("=" * 60)
    print(f"Gestartet:    {status.get('started', '?')}")
    print(f"Aktuell:      {status.get('current', '?')}")
    print(f"Fortschritt:  {status.get('done', 0)}/{status.get('total', 0)} Einheiten")
    print(f"Video-Std:    {status.get('hours_done', '?')}h verarbeitet")
    print(f"Peaks:        {status.get('peaks', 0)} Bewegungen gefunden")
    print(f"Laufzeit:     {status.get('elapsed', '?')}")
    print(f"ETA:          {status.get('eta', '?')}")
    print(f"Tempo:        {status.get('speed', '?')}× Echtzeit")
    print(f"Letztes Update: {status.get('last_update', '?')}")
    print("=" * 60)
    
    if 'last_peaks' in status and status['last_peaks']:
        print(f"\nLetzte Peaks ({status.get('current', '?')}):")
        for p in status['last_peaks']:
            print(f"  🐦 {p}")


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch motion detection for Vogelhaus videos')
    parser.add_argument('--status', action='store_true', help='Show current status')
    args = parser.parse_args()
    
    if args.status:
        show_status()
    else:
        process_batch()
