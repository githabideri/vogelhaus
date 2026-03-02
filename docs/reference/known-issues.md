# Known Issues

> Last updated: 2026-03

This document catalogs known issues and their workarounds in the Vogelhaus project.

## Critical OS Compatibility Issues

### Pi Zero W: Do NOT Use Trixie OS

**Issue**: Raspberry Pi OS Trixie (Debian 13) is incompatible with Pi Zero W v1.1 (ARMv6).

**Symptoms**:
- WiFi disconnects after 4-18 hours and won't reconnect automatically
- USB Gadget mode completely broken
- Browsers (Chromium/Firefox) refuse to run (ARMv6 incompatibility)
- Network configuration via Netplan/NetworkManager conflicts
- Access point creation impossible
- Many modern packages unavailable for armhf/ARMv6

**Root Cause**: ARMv6 architecture increasingly unsupported; Netplan networking conflicts.

**Solution**: Use **Raspberry Pi OS Legacy Lite (Bookworm-based, 32-bit)** instead.

**Status**: Official recommendation change pending (GitHub issue #24).

### ARRIS Router 2.4GHz WiFi Bug

**Issue**: ARRIS TG3442 router firmware causes Broadcom WiFi chips to fail on 2.4GHz networks.

**Symptoms**:
- WiFi connection attempts fail or are unstable on 2.4GHz
- Broadcom-based Pi devices (Pi Zero W, older Pi models) affected
- 5GHz networks work normally

**Affected Hardware**:
- ARRIS TG3442 with firmware 9.1.103GY
- Raspberry Pi Zero W (Broadcom BCM43438)
- Older Pi models with Broadcom WiFi

**Workarounds**:
1. **Use 5GHz WiFi** when possible (Pi 4)
2. **Use different router** or firmware update
3. **USB Gadget networking** via Pi 4 for Pi Zero
4. **Ethernet connection** for Pi 4

**Status**: ISP (Liwest) issue, no fix available.

## Network and Connectivity Issues

### dhcpcd Service Crash Bug

**Issue**: dhcpcd daemon occasionally crashes, causing network loss.

**Symptoms**:
- Sudden loss of network connectivity
- `ip addr` shows interface without IP
- `systemctl status dhcpcd` shows service failed
- Requires manual restart to recover

**Affected Systems**: Both Pi 4 and Pi Zero W running dhcpcd.

**Workaround**:
```bash
# Check dhcpcd status
sudo systemctl status dhcpcd

# Restart if crashed
sudo systemctl restart dhcpcd

# Monitor for crashes
sudo journalctl -u dhcpcd -f
```

**Root Cause**: Unknown, appears related to network topology changes.

**Monitoring**: USB Failover script detects and can recover automatically.

### USB Gadget MAC Address Randomization

**Issue**: USB Gadget interfaces get random MAC addresses on each boot, breaking static configurations.

**Symptoms**:
- Network rules based on MAC address fail
- DHCP reservations don't work
- USB Failover routing becomes unstable

**Solution**: Fixed MAC addresses in USB Gadget configuration:
```bash
# Pi Zero MAC: 02:22:33:44:55:66
# Pi 4 MAC: 02:22:33:44:55:67
```

**Status**: Fixed in current configuration.

## Hardware Issues

### IR LED Power Overload

**Issue**: Both IR LEDs together draw ~1.8A from Pi Zero's 3.3V rail (capacity: 1.0-1.5A).

**Symptoms**:
- Pi Zero freezes or crashes in darkness when both LEDs activate
- Voltage brownouts under camera + WiFi + LED load
- Unstable operation

**Root Cause**: LDR-controlled LEDs exceed voltage regulator capacity.

**Solutions**:
1. **Disconnect one LED** (sufficient for birdhouse interior)
2. **External 3.3V power supply** for LEDs
3. **GPIO control** with external power (advanced)

**Status**: Documented in [Camera Modules](../hardware/camera-modules.md).

### Missing IR LED Heatsink

**Issue**: One IR LED missing heatsink causes visible red glow and potential thermal runaway.

**Symptoms**:
- LED glows visibly red/brighter than the other
- Higher current draw due to reduced forward voltage
- Risk of LED failure from overheating

**Solution**: Replace heatsink with aluminum plate + thermal adhesive.

**Workaround**: Disconnect LED without heatsink.

## Camera Detection Issues

### vcgencmd False Negative

**Issue**: `vcgencmd get_camera` shows `detected=0` even when camera works normally.

**Affected**: Pi Zero W with OV5647 NoIR camera.

**Workaround**: Use `rpicam-hello --list-cameras` for actual camera detection.

**Root Cause**: Known Pi Zero issue, not a real problem.

### MediaMTX Camera Lock

**Issue**: MediaMTX service locks camera access, preventing direct camera commands.

**Symptoms**:
- `libcamera-still` fails with "camera busy" error
- Cannot take photos while streaming

**Solution**: Use RTSP stream for photos:
```bash
ffmpeg -y -rtsp_transport tcp -i rtsp://127.0.0.1:8554/vogl-cam -frames:v 1 -q:v 2 photo.jpg
```

**Alternative**: Temporarily stop MediaMTX:
```bash
sudo systemctl stop mediamtx
libcamera-still -o photo.jpg
sudo systemctl start mediamtx
```

## Boot and Configuration Issues

### cmdline.txt Line Endings

**Issue**: Windows editing creates CRLF line endings, breaking Pi boot.

**Symptoms**:
- Pi fails to boot
- USB Gadget modules not loaded
- Kernel parameters ignored

**Solution**: Convert to Unix line endings:
```bash
sed -i 's/\r$//' /boot/firmware/cmdline.txt
```

**Prevention**: Use Unix-compatible editors or tools.

### USB Gadget Module Loading

**Issue**: Boot configuration missing `g_ether` module causes no USB network on first boot.

**Symptoms**:
- USB interface doesn't appear on Pi 4
- Pi Zero not accessible via USB
- Must use WiFi for initial setup

**Solution**: Ensure `cmdline.txt` includes:
```
modules-load=dwc2,g_ether
```

**Note**: Later replaced by libcomposite for stable MAC addresses.

## Serial/UART Issues

### GPIO UART Signal Integrity

**Issue**: Long UART cables or poor connections cause data corruption.

**Symptoms**:
- Garbled characters in serial console
- Connection drops intermittently
- No response from remote device

**Solutions**:
1. **Shorter cables** (<30cm recommended)
2. **Proper grounding** (connect GND pins)
3. **Lower baud rate** if needed (from 115200 to 9600)
4. **Level shifter** for electrical isolation

### UART Service Conflicts

**Issue**: Multiple getty services on same UART port cause conflicts.

**Symptoms**:
- No prompt on serial connection
- Characters echoed but no response
- Service fails to start

**Solution**: Enable getty on target device only:
```bash
# On Pi Zero (target)
sudo systemctl enable --now serial-getty@ttyAMA0

# On Pi 4 (monitor)
sudo systemctl disable serial-getty@ttyAMA0
```

## Docker and Container Issues

### Restreamer Container Stability

**Issue**: Restreamer container occasionally stops or fails to restart.

**Symptoms**:
- Stream to Twitch stops
- Container shows "Exited" status
- Web interface not accessible

**Diagnosis**:
```bash
docker ps -a
docker logs restreamer
```

**Solutions**:
- **Restart container**: `docker restart restreamer`
- **Check logs**: Look for ffmpeg errors or network issues
- **Resource limits**: Ensure adequate CPU/memory

### Docker Firewall Conflicts

**Issue**: Docker's iptables rules block USB Gadget traffic.

**Symptoms**:
- USB Failover doesn't work
- Pi Zero can reach Pi 4 but not internet through Pi 4
- NAT forwarding fails

**Solution**: Add explicit allow rules in `/etc/rc.local`:
```bash
iptables -I DOCKER-USER -i usb0 -j ACCEPT
iptables -I DOCKER-USER -o usb0 -j ACCEPT
```

## Performance and Resource Issues

### SD Card Wear

**Issue**: Excessive logging and writes reduce SD card lifespan.

**Symptoms**:
- Filesystem corruption
- Read-only remount errors
- Boot failures

**Mitigation**:
- **Log rotation**: Configured via systemd
- **Docker log limits**: 50MB × 3 files max
- **Avoid swap**: Reduces write cycles
- **External storage**: Use SSD for high-volume data

### Memory Pressure on Pi Zero

**Issue**: Pi Zero W has only 364MB RAM, limiting applications.

**Symptoms**:
- OOM killer activates
- Services fail to start
- System becomes unresponsive

**Solutions**:
- **Minimal services**: Only essential processes
- **No GUI**: Use Lite OS variant
- **Efficient software**: Avoid memory-heavy applications

## Workaround Summary

| Issue | Quick Fix |
|-------|-----------|
| Trixie OS on Pi Zero | Use Bookworm Legacy instead |
| ARRIS 2.4GHz WiFi | Use 5GHz or USB Gadget |
| dhcpcd crash | `sudo systemctl restart dhcpcd` |
| IR LED overload | Disconnect one LED |
| Camera busy | Use RTSP for photos |
| Windows line endings | `sed -i 's/\r$//' file` |
| USB Gadget missing | Add `g_ether` to cmdline.txt |
| UART conflicts | Enable getty on target only |
| Docker blocking USB | Add DOCKER-USER rules |

## Reporting New Issues

When encountering new issues:

1. **Check logs**: `sudo journalctl -u service-name -f`
2. **Test isolation**: Reproduce with minimal configuration
3. **Document symptoms**: Include error messages and system state
4. **Note environment**: OS version, hardware revision, network config
5. **Try workarounds**: Check this document and troubleshooting guide

Add findings to this document or report to the project maintainer.