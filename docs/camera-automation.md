# Camera Automation

Automatic camera switching between day (Pi4 main camera) and night (Pi Zero NoIR camera) based on sunrise/sunset times.

## Overview

The system consists of two scripts:

1. **`camera-switch.sh`** — Performs the actual camera switch in Restreamer
2. **`camera-scheduler.py`** — Calculates daily sunrise/sunset times and schedules switches via `at`

## How It Works

1. **Daily at 00:05** (via cron): `camera-scheduler.py` runs
2. Calculates today's sunrise and sunset times for your location
3. Schedules two `at` jobs:
   - **Sunrise - 10min** → Switch to Pi4 camera (`vogl-cam`)
   - **Sunset - 10min** → Switch to NoIR camera (`vogl-noir`)
4. At the scheduled times: `camera-switch.sh` runs and updates Restreamer config

## Installation

### Prerequisites

- `at` daemon installed and running:
  ```bash
  sudo apt install at
  sudo systemctl enable --now atd
  ```

### Deploy Scripts

```bash
# Copy scripts to system location
sudo cp scripts/camera-switch.sh /usr/local/bin/
sudo cp scripts/camera-scheduler.py /usr/local/bin/
sudo chmod +x /usr/local/bin/camera-switch.sh
sudo chmod +x /usr/local/bin/camera-scheduler.py

# Create log directory
sudo mkdir -p /var/log/vogelhaus
sudo chown $(whoami):$(whoami) /var/log/vogelhaus
```

### Configure

1. Copy `.env.template` to `.env`:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` and set your location:
   ```bash
   LOCATION_LAT=48.3069  # Your latitude
   LOCATION_LON=14.2858  # Your longitude
   ```

3. Optionally adjust:
   - `CAMERA_SWITCH_OFFSET_MIN=10` (minutes before sunrise/sunset)
   - `RESTREAMER_DOCKER=restreamer` (Docker container name)
   - `PI4_STREAM` / `NOIR_STREAM` (RTSP URLs)

### Add Cron Job

```bash
(crontab -l 2>/dev/null; echo "5 0 * * * /usr/local/bin/camera-scheduler.py") | crontab -
```

This runs the scheduler daily at 00:05 local time.

## Manual Usage

### Switch Cameras Manually

```bash
# Switch to Pi4 (day camera)
/usr/local/bin/camera-switch.sh pi4

# Switch to NoIR (night camera)
/usr/local/bin/camera-switch.sh noir
```

### Run Scheduler Manually

```bash
/usr/local/bin/camera-scheduler.py
```

### Check Logs

```bash
# Switch log (actual camera changes)
tail -f /var/log/vogelhaus/camera-switch.log

# Scheduler log (daily calculations)
tail -f /var/log/vogelhaus/camera-scheduler.log
```

### Check Scheduled Jobs

```bash
atq
```

### Cancel a Scheduled Job

```bash
atrm <job_number>
```

## Exit Codes

### camera-switch.sh

- `0` — Success
- `1` — Error (failed to switch or verify)
- `2` — Already active (no change needed)

### camera-scheduler.py

- `0` — Success
- `1` — Error (could not calculate times or schedule jobs)

## Troubleshooting

### Restreamer Not Restarting

- Check Docker permissions: user must be in `docker` group
- Verify container name: `docker ps | grep restreamer`

### Wrong Sunrise/Sunset Times

- Verify `LOCATION_LAT` and `LOCATION_LON` in `.env`
- Algorithm is accurate to ±10 minutes
- Check timezone: scheduler uses UTC internally, converts to local time for `at`

### At Jobs Not Running

- Ensure `atd` is running: `systemctl status atd`
- Check user permissions: `at` requires user to be allowed (usually automatic)
- Verify cron runs: `grep camera-scheduler /var/log/syslog`

### Logs Not Created

- Check directory permissions: `/var/log/vogelhaus` must be writable
- Run script manually to test: `sudo /usr/local/bin/camera-scheduler.py`

## Example Logs

### Successful Scheduler Run

```
[2026-03-03 00:05:12 CET] === Camera Scheduler Run ===
[2026-03-03 00:05:12 CET] Today's times (UTC): sunrise 05:42, sunset 16:28
[2026-03-03 00:05:12 CET] Switching at: sunrise 05:32, sunset 16:18
[2026-03-03 00:05:12 CET] ✅ Scheduled sunrise switch (job 1234): 05:32 → pi4
[2026-03-03 00:05:12 CET] ✅ Scheduled sunset switch (job 1235): 16:18 → noir
```

### Successful Switch

```
[2026-03-03 16:18:05 CET] === Camera Switch Request: noir ===
[2026-03-03 16:18:05 CET] Current source: rtsp://172.20.0.1:8554/vogl-cam
[2026-03-03 16:18:05 CET] Switching to: rtsp://172.20.0.1:8554/vogl-noir
[2026-03-03 16:18:05 CET] Restarting Restreamer...
[2026-03-03 16:18:11 CET] ✅ Switch successful: noir is now active
```

## Architecture Notes

- **Scheduler uses `at`** instead of cron for precise timing (sunrise/sunset change daily)
- **Switch script is idempotent** — safe to run multiple times
- **Logs are append-only** — rotate manually or via logrotate
- **No external dependencies** — pure Python stdlib + bash + at

## Future Enhancements

- [ ] systemd timer instead of cron
- [ ] Telegram/Matrix notifications on switch
- [ ] Graceful fallback if camera unavailable
- [ ] Configurable twilight offset (civil/nautical/astronomical)
