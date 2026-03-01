#!/usr/bin/env python3
"""
Motion Detection with NVIDIA GPU decoding — Vogelhauswart
Uses ffmpeg h264_cuvid for hardware-accelerated video analysis.

Usage:
    python3 motion-detect-gpu.py <video.mp4> [--fps 1] [--threshold auto]

Requirements:
    - ffmpeg with CUDA/NVDEC support (h264_cuvid)
    - NVIDIA GPU with compatible drivers
    - numpy

Output:
    - Console: Progress + detected motion peaks
    - CSV: <video>_motion.csv with per-second motion scores
"""
import subprocess
import sys
import time
import argparse
import numpy as np


def parse_args():
    p = argparse.ArgumentParser(description="GPU-accelerated motion detection for bird videos")
    p.add_argument("video", help="Path to video file")
    p.add_argument("--fps", type=int, default=1, help="Frames per second to sample (default: 1)")
    p.add_argument("--width", type=int, default=640, help="Analysis width (default: 640)")
    p.add_argument("--height", type=int, default=360, help="Analysis height (default: 360)")
    p.add_argument("--threshold", type=float, default=0, help="Manual threshold (0=auto: mean+2*std)")
    p.add_argument("--top", type=int, default=20, help="Number of top peaks to show")
    p.add_argument("--no-gpu", action="store_true", help="Use CPU decoding instead of GPU")
    return p.parse_args()


def main():
    args = parse_args()
    video = args.video
    fps = args.fps
    width, height = args.width, args.height

    print(f"Analysing: {video}")

    # Build ffmpeg command
    if args.no_gpu:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", video,
            "-vf", f"scale={width}:{height},format=gray",
            "-r", str(fps),
            "-f", "rawvideo", "-pix_fmt", "gray",
            "pipe:1",
        ]
        print(f"CPU decode @ {fps} fps, {width}x{height}")
    else:
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-hwaccel", "cuda", "-hwaccel_output_format", "cuda",
            "-c:v", "h264_cuvid",
            "-i", video,
            "-vf", f"scale_cuda={width}:{height},hwdownload,format=nv12,format=gray",
            "-r", str(fps),
            "-f", "rawvideo", "-pix_fmt", "gray",
            "pipe:1",
        ]
        print(f"GPU decode (h264_cuvid) @ {fps} fps, {width}x{height}")

    start = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    frame_size = width * height
    prev_frame = None
    scores = []
    frame_num = 0

    while True:
        data = proc.stdout.read(frame_size)
        if len(data) < frame_size:
            break
        frame = np.frombuffer(data, dtype=np.uint8).reshape(height, width)
        if prev_frame is not None:
            diff = np.mean(np.abs(frame.astype(float) - prev_frame.astype(float))) / 255.0
            scores.append((frame_num, diff))
        prev_frame = frame.copy()
        frame_num += 1
        if frame_num % 300 == 0:
            elapsed = time.time() - start
            print(f"  {frame_num}s ({frame_num / 60:.0f}min) processed in {elapsed:.1f}s real")

    elapsed = time.time() - start
    proc.wait()

    speed = frame_num / elapsed if elapsed > 0 else 0
    print(f"\nDone! {frame_num} frames ({frame_num / 60:.1f} min video) in {elapsed:.1f}s")
    print(f"Speed: {speed:.1f}x realtime")

    # Analyse peaks
    if scores:
        arr = np.array([s[1] for s in scores])
        mean_score = np.mean(arr)
        std_score = np.std(arr)
        threshold = args.threshold if args.threshold > 0 else mean_score + 2 * std_score
        peaks = [(s[0], s[1]) for s in scores if s[1] > threshold]

        print(f"\nBaseline: {mean_score:.4f} +/- {std_score:.4f}, Threshold: {threshold:.4f}")
        print(f"Peaks above threshold: {len(peaks)}")

        if peaks:
            print(f"\nTop {args.top} peaks (potential bird activity):")
            peaks.sort(key=lambda x: -x[1])
            for sec, score in peaks[: args.top]:
                minutes = sec // 60
                secs = sec % 60
                print(f"  {minutes:02d}:{secs:02d} - score {score:.4f}")

        # Save CSV
        csv_path = video.rsplit(".", 1)[0] + "_motion.csv"
        with open(csv_path, "w") as f:
            f.write("second,score\n")
            for sec, score in scores:
                f.write(f"{sec},{score:.6f}\n")
        print(f"\nCSV saved: {csv_path}")


if __name__ == "__main__":
    main()
