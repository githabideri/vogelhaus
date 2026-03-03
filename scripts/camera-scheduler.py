#!/usr/bin/env python3
"""
camera-scheduler.py — Schedule automatic camera switching at sunrise/sunset
Calculates sunrise/sunset times and schedules `at` jobs to switch cameras.
Run daily via cron (e.g., 00:05).
"""

import os
import sys
import math
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

# Load from environment or .env
def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ.setdefault(key, val)

load_env()

LOCATION_LAT = float(os.getenv('LOCATION_LAT', '48.3069'))  # Linz
LOCATION_LON = float(os.getenv('LOCATION_LON', '14.2858'))
SWITCH_SCRIPT = os.getenv('CAMERA_SWITCH_SCRIPT', 
                          str(Path(__file__).parent / 'camera-switch.sh'))
SWITCH_OFFSET_MIN = int(os.getenv('CAMERA_SWITCH_OFFSET_MIN', '10'))  # Switch 10min before sunrise/sunset
LOG_DIR = Path(os.getenv('LOG_DIR', '/var/log/vogelhaus'))
LOG_FILE = LOG_DIR / 'camera-scheduler.log'

# ============================================================
# LOGGING
# ============================================================

def log(msg):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    log_line = f"[{timestamp}] {msg}"
    print(log_line, file=sys.stderr)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')

# ============================================================
# SUN CALCULATIONS
# ============================================================

def calculate_sun_times(lat, lon, date=None):
    """
    Calculate sunrise and sunset times for given location and date.
    Uses simplified solar position algorithm (good to ±10 min).
    
    Returns: (sunrise_utc, sunset_utc) as datetime objects
    """
    if date is None:
        date = datetime.now().date()
    
    # Julian day
    a = (14 - date.month) // 12
    y = date.year + 4800 - a
    m = date.month + 12 * a - 3
    jdn = date.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    jd = jdn + 0.5
    
    # Days since J2000.0
    n = jd - 2451545.0
    
    # Mean solar noon
    j_star = n - lon / 360.0
    
    # Solar mean anomaly
    M = (357.5291 + 0.98560028 * j_star) % 360
    M_rad = math.radians(M)
    
    # Equation of center
    C = 1.9148 * math.sin(M_rad) + 0.0200 * math.sin(2 * M_rad) + 0.0003 * math.sin(3 * M_rad)
    
    # Ecliptic longitude
    lambda_sun = (M + C + 180 + 102.9372) % 360
    lambda_rad = math.radians(lambda_sun)
    
    # Solar transit
    j_transit = 2451545.0 + j_star + 0.0053 * math.sin(M_rad) - 0.0069 * math.sin(2 * lambda_rad)
    
    # Declination
    sin_delta = math.sin(lambda_rad) * math.sin(math.radians(23.44))
    delta_rad = math.asin(sin_delta)
    
    # Hour angle
    lat_rad = math.radians(lat)
    cos_omega = (math.sin(math.radians(-0.83)) - math.sin(lat_rad) * sin_delta) / \
                (math.cos(lat_rad) * math.cos(delta_rad))
    
    if abs(cos_omega) > 1:
        # Polar day/night
        return (None, None)
    
    omega_rad = math.acos(cos_omega)
    omega_deg = math.degrees(omega_rad)
    
    # Sunrise/sunset JD
    j_rise = j_transit - omega_deg / 360.0
    j_set = j_transit + omega_deg / 360.0
    
    # Convert to datetime
    def jd_to_datetime(jd_val):
        jd_val += 0.5
        z = int(jd_val)
        f = jd_val - z
        
        if z < 2299161:
            a_val = z
        else:
            alpha = int((z - 1867216.25) / 36524.25)
            a_val = z + 1 + alpha - alpha // 4
        
        b = a_val + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)
        
        day = b - d - int(30.6001 * e) + f
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715
        
        hours = (day - int(day)) * 24
        minutes = (hours - int(hours)) * 60
        seconds = (minutes - int(minutes)) * 60
        
        return datetime(year, month, int(day), int(hours), int(minutes), int(seconds))
    
    sunrise = jd_to_datetime(j_rise)
    sunset = jd_to_datetime(j_set)
    
    return (sunrise, sunset)

# ============================================================
# SCHEDULING
# ============================================================

def schedule_at_job(time_dt, command):
    """
    Schedule a command via `at`.
    Returns: at job ID or None on failure
    """
    time_str = time_dt.strftime("%H:%M %Y-%m-%d")
    
    try:
        result = subprocess.run(
            ['at', time_str],
            input=command.encode(),
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            # Parse job ID from output: "job 123 at ..."
            output = result.stderr.decode().strip()
            if 'job' in output:
                job_id = output.split()[1]
                return job_id
        return None
    except Exception as e:
        log(f"ERROR scheduling at job: {e}")
        return None

# ============================================================
# MAIN
# ============================================================

def main():
    log("=== Camera Scheduler Run ===")
    
    # Calculate today's sunrise/sunset
    sunrise, sunset = calculate_sun_times(LOCATION_LAT, LOCATION_LON)
    
    if sunrise is None or sunset is None:
        log("ERROR: Could not calculate sun times (polar day/night?)")
        return 1
    
    # Apply offset (switch 10min before)
    sunrise_switch = sunrise - timedelta(minutes=SWITCH_OFFSET_MIN)
    sunset_switch = sunset - timedelta(minutes=SWITCH_OFFSET_MIN)
    
    log(f"Today's times (UTC): sunrise {sunrise.strftime('%H:%M')}, sunset {sunset.strftime('%H:%M')}")
    log(f"Switching at: sunrise {sunrise_switch.strftime('%H:%M')}, sunset {sunset_switch.strftime('%H:%M')}")
    
    # Schedule sunrise → pi4
    sunrise_cmd = f"{SWITCH_SCRIPT} pi4"
    sunrise_job = schedule_at_job(sunrise_switch, sunrise_cmd)
    
    if sunrise_job:
        log(f"✅ Scheduled sunrise switch (job {sunrise_job}): {sunrise_switch.strftime('%H:%M')} → pi4")
    else:
        log(f"⚠️  Failed to schedule sunrise switch")
    
    # Schedule sunset → noir
    sunset_cmd = f"{SWITCH_SCRIPT} noir"
    sunset_job = schedule_at_job(sunset_switch, sunset_cmd)
    
    if sunset_job:
        log(f"✅ Scheduled sunset switch (job {sunset_job}): {sunset_switch.strftime('%H:%M')} → noir")
    else:
        log(f"⚠️  Failed to schedule sunset switch")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
