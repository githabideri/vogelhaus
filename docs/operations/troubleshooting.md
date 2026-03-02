# Troubleshooting

> Last updated: 2026-03

## Pi Zero W: Do NOT Use Trixie

Raspberry Pi OS Trixie (Debian 13) is broken on Pi Zero W v1.1 (ARMv6):
- WiFi doesn't work (firmware loading fails)
- USB Gadget mode broken
- Many packages unavailable for armhf/armel

**Use Raspberry Pi OS Legacy Lite (Bookworm-based, 32-bit) instead.**

See [Known Issues](../reference/known-issues.md) for the full investigation.

## Camera Detection Issues

`vcgencmd get_camera` may show `detected=0` even when the camera works fine. Test with:

```bash
# Pi Zero
rpicam-hello --list-cameras

# Pi 4
libcamera-hello --list-cameras
```

If cameras are detected but photos fail, check permissions and service conflicts.

## Pi 4: Camera Locked by MediaMTX

If `libcamera-still` fails with a "camera busy" error:

```bash
sudo systemctl stop mediamtx
libcamera-still -o photo.jpg
sudo systemctl start mediamtx
```

**Preferred solution**: Use RTSP stream for photos to avoid stopping services:
```bash
ffmpeg -y -rtsp_transport tcp -i rtsp://127.0.0.1:8554/vogl-cam -frames:v 1 -q:v 2 photo.jpg
```

## Network Connectivity Issues

### Pi Zero Not Accessible

1. **Check USB Gadget connection**:
   ```bash
   # On Pi 4
   ip addr show usb0
   # Should show 169.254.246.156
   
   # Test connectivity
   ping 169.254.246.2
   ```

2. **Check USB Hub status**:
   ```bash
   sudo uhubctl
   # Look for Pi Zero on Hub 1-1 Port 2
   ```

3. **Restart USB services**:
   ```bash
   sudo systemctl restart usb-internet-sharing
   sudo systemctl restart usb-zero-powercycle
   ```

### WiFi Connection Problems

1. **Check WiFi status**:
   ```bash
   # Pi 4
   iwconfig wlan0
   
   # Pi Zero
   iwconfig wlan0
   ```

2. **Check network configuration**:
   ```bash
   cat /etc/dhcpcd.conf
   ip route show
   ```

3. **Restart networking**:
   ```bash
   sudo systemctl restart dhcpcd
   sudo systemctl restart networking
   ```

## Serial Fallback (GPIO UART) Not Working

If Wi-Fi/USB fail and no serial prompt appears:

1. **Verify wiring**: GND↔GND, TX↔RX crossed
2. **Confirm UART enabled** (`enable_uart=1` in config.txt)
3. **Confirm target has serial getty enabled**:
   ```bash
   sudo systemctl status serial-getty@ttyAMA0
   ```
4. **Ensure monitor side has no conflicting serial getty**
5. **Test connection**:
   ```bash
   # Monitor side
   screen /dev/ttyAMA0 115200
   ```

If needed, press Enter a few times to trigger the prompt.

See [UART Recovery](../setup/uart-recovery.md) for full details.

## Power and Hardware Issues

### Pi Freezes in the Dark

Both IR LEDs draw ~1.8A from the 3.3V rail, exceeding the regulator's capacity. Solutions:

1. **Disconnect one IR LED** (one is usually sufficient)
2. **Use external power supply** for LEDs
3. **Add GPIO control** to enable LEDs only when needed

See [Camera Modules](../hardware/camera-modules.md) for power details.

### Boot Configuration Issues

**`cmdline.txt` line endings**: File MUST have Unix line endings (LF), not Windows (CR LF). If edited on Windows:
```bash
sed -i 's/\r$//' /boot/firmware/cmdline.txt
```

**USB Gadget not working**: Ensure `modules-load=dwc2,g_ether` is correctly added to `cmdline.txt` after `rootwait`.

## Service Issues

### MediaMTX Problems

**Service won't start**:
```bash
sudo journalctl -u mediamtx -f
sudo systemctl status mediamtx
```

**Camera initialization fails**:
```bash
# Check camera access
libcamera-hello --list-cameras
# Restart service
sudo systemctl restart mediamtx
```

### Restreamer Issues

**Container not running**:
```bash
docker ps -a
docker logs restreamer
docker restart restreamer
```

**Stream not reaching Twitch**:
- Check stream key in Restreamer web UI
- Verify network connectivity: `ping live.twitch.tv`
- Check ffmpeg process: `docker exec restreamer ps aux | grep ffmpeg`

### Tailscale Connection Problems

**Service not connected**:
```bash
sudo tailscale status
sudo tailscale up
```

**Can't reach devices**:
```bash
tailscale ping <device-name>
```

## Image Quality Issues

### Night Vision: Purple Tint

NoIR cameras show a purple tint in daylight. This is normal — the missing IR filter lets infrared light through, which the sensor interprets as purple/magenta.

**Solutions**:
- **For night images**: Purple tint disappears with IR illumination
- **Force grayscale**: `rpicam-still -o photo.jpg --saturation 0`
- **Use day camera**: IMX708 has proper IR filter for daylight

### Camera Commands Reference

**Important**: Different Pis use different camera commands:

| Device | Command | Example |
|--------|---------|---------|
| Pi 4 | `libcamera-still` | `libcamera-still -o photo.jpg` |
| Pi Zero | `rpicam-still` | `rpicam-still -o photo.jpg` |

Don't mix them up — they're different packages with different capabilities.

## System Resource Issues

### High CPU Usage

Monitor system resources:
```bash
htop
vcgencmd measure_temp
```

**Common causes**:
- Video encoding/streaming using too many resources
- Multiple camera processes running simultaneously
- Background analysis tasks

### Storage Full

**Check disk usage**:
```bash
df -h
du -sh /var/log/*
```

**Clean up**:
```bash
# Clean old logs
sudo journalctl --rotate
sudo journalctl --vacuum-time=7d

# Clean package cache
sudo apt clean
```

## Emergency Recovery

### Via UART (if network fails)

1. Connect via UART as described in [UART Recovery](../setup/uart-recovery.md)
2. Check network status:
   ```bash
   ip addr
   ip route
   systemctl status networking
   ```
3. Restart services as needed

### USB Power Cycle

If Pi Zero becomes unresponsive:
```bash
# On Pi 4, cycle USB power
sudo uhubctl -l 1-1 -p 2 -a 0  # Power off
sleep 5
sudo uhubctl -l 1-1 -p 2 -a 1  # Power on
```

### Factory Reset

As last resort, reflash SD cards following:
- [Pi Zero Flash Guide](../setup/pi-zero-flash.md)
- Hardware setup in [Assembly Guide](../hardware/assembly.md)