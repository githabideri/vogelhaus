# Pi Zero W System Inventory

> Last updated: 2026-03

Full system inventory of the camera unit (voglberry-light).

## Hardware

| Component | Details |
|-----------|---------|
| Model | Raspberry Pi Zero W Rev 1.1 (BCM2835, ARMv6l) |
| RAM | 364 MB (shared with GPU) |
| SD Card | 32 GB (mmcblk0) |
| Camera | OV5647 NoIR + 2x 850nm IR LEDs (LDR-controlled) |
| Network | WiFi only (wlan0) |
| Power | USB from Pi 4 (no dedicated PSU) |

## Operating System

| Parameter | Value |
|-----------|-------|
| OS | Raspbian Bookworm (12) |
| Kernel | 6.12.47+rpt-rpi-v6 (armv6l, 32-bit) |
| User | `vb-light` (uid 1000) |
| Architecture | ARMv6l (32-bit only) |

**Important**: ARMv6 architecture requires Legacy OS — Trixie is incompatible.

## Storage

### SD Card (32 GB)

- **Usage**: 8% used (~2.1 GB), 25 GB free
- **Boot partition**: `/boot/firmware` (512 MB, vfat)
- **Root partition**: `/` (28.7 GB, ext4)
- **Wear leveling**: Good due to minimal writes

### Storage Performance
- **Read speed**: ~20-25 MB/s (Class 10 SD card)
- **Write speed**: ~10-15 MB/s
- **Random I/O**: Limited, avoid database workloads

## Software Stack

Minimal installation — no Docker, no web services, optimized for camera operation.

### Native Services (systemd)

| Service | Purpose | Status |
|---------|---------|--------|
| ssh | Remote access | running |
| wpa_supplicant | WiFi | running |
| NetworkManager | Network management | running |
| tailscaled | Tailscale VPN | running |
| usb-gadget | USB device mode | enabled |
| usb-failover | Network failover | enabled |

### Camera System

- **Sensor**: OV5647 detected at `/base/soc/i2c0mux/i2c@1/ov5647@36`
- **Tuning file**: `/usr/share/libcamera/ipa/rpi/vc4/ov5647.json`
- **Command**: `rpicam-still` (NOT `libcamera-still`)
- **Note**: `vcgencmd get_camera` shows `detected=0` but camera works normally

### Available Camera Modes

| Resolution | FPS | Crop | Use Case |
|-----------|-----|------|----------|
| 640×480 | 58.9 | 2560×1920 center | Testing, low bandwidth |
| 1296×972 | 46.3 | Full sensor | Medium quality stream |
| 1920×1080 | 32.8 | 1928×1080 center | HD streaming |
| 2592×1944 | 15.6 | Full sensor | Maximum quality photos |

### IR LED Control

- **LEDs**: 2x 850nm IR LEDs, ~3W each
- **Control**: LDR (light sensor) with adjustable potentiometer
- **Auto mode**: LEDs activate automatically in darkness
- **Current draw**: ~1.8A combined (exceeds Pi Zero 3.3V capacity)
- **Recommendation**: Use only one LED or external power

## Network Configuration

| Interface | Address | Purpose |
|-----------|---------|---------|
| wlan0 | `<ZERO_WLAN_IP>/24` | Local WiFi (primary) |
| usb0 | `<ZERO_USB_IP>/16` | USB Gadget to Pi 4 |
| tailscale0 | `<TAILSCALE_ZERO>/32` | VPN overlay |

### USB Gadget Configuration

- **Mode**: CDC Ethernet (g_ether)
- **Host**: Pi 4 at `<PI4_USB_IP>`
- **Gateway**: Internet via Pi 4 NAT
- **MAC**: Fixed address `02:22:33:44:55:66`

### WiFi Configuration

- **Primary**: 2.4 GHz network (Pi Zero W limitation)
- **Fallback**: USB Gadget internet sharing via Pi 4
- **Roaming**: Basic support, manual reconnection

## Performance Characteristics

### CPU Usage
- **Idle**: 2-5%
- **Camera operation**: 10-20%
- **Network activity**: 5-15%
- **Maximum**: Single-core ARMv6 @ 1 GHz

### Memory Usage
- **Base system**: ~150MB
- **Camera processes**: ~50MB
- **Network services**: ~30MB
- **Available for apps**: ~130MB

### Thermal Management
- **Typical temperature**: 35-50°C
- **No heatsink**: Passive cooling only
- **Throttling**: Rare due to low power

## Connectivity Options

### SSH Access Methods

1. **Via WiFi (direct)**:
   ```bash
   ssh vb-light@<ZERO_WLAN_IP>
   ```

2. **Via USB Gadget**:
   ```bash
   ssh vb-light@<ZERO_USB_IP>
   ```

3. **Via Tailscale**:
   ```bash
   ssh vb-light@<TAILSCALE_ZERO>
   ```

4. **Via Pi 4 ProxyJump**:
   ```bash
   ssh -J vogl@<TAILSCALE_PI4> vb-light@<ZERO_USB_IP>
   ```

### Emergency Access

- **UART recovery**: 3-wire serial via GPIO pins
- **USB direct**: Connect to computer as USB device
- **Physical**: SD card removal for recovery

## Resource Constraints

### Memory Limitations
- **Total RAM**: 364MB (GPU shared)
- **Available**: ~200-250MB for applications
- **Swap**: Not recommended (SD card wear)

### CPU Limitations
- **Architecture**: ARMv6l (older instruction set)
- **Cores**: Single core, no parallel processing
- **Floating point**: Limited hardware support

### Network Limitations
- **WiFi**: 2.4 GHz only (no 5 GHz support)
- **Bandwidth**: ~50-100 Mbps theoretical
- **Latency**: Higher than Pi 4 due to processing overhead

## Maintenance

### Regular Tasks
- **Log rotation**: Automatic via systemd-journald
- **Package updates**: Manual, infrequent (stability focus)
- **SD card health**: Monitor via `sudo fdisk -l`

### Monitoring
```bash
# System status
htop
free -h
vcgencmd measure_temp

# Camera status
rpicam-hello --list-cameras

# Network status
ip addr show
sudo systemctl status usb-gadget
```

## Known Issues

### Hardware
- IR LEDs may cause brownouts if both used simultaneously
- WiFi antenna placement affects signal quality
- USB connector fragility requires careful cable management

### Software
- Trixie OS completely broken on ARMv6
- Some modern packages unavailable for armhf architecture
- Limited hardware acceleration for video processing

### Workarounds
- Use only one IR LED for stable operation
- Prefer USB Gadget for reliable connectivity
- Offload video processing to Pi 4

## Timeline

| Date | Event |
|------|-------|
| Jan 2026 | Pi Zero W acquired |
| Feb 2026 | Initial OS installation and testing |
| Mar 2026 | USB Gadget configuration |
| Mar 2026 | Camera integration and testing |
| Mar 2026 | Tailscale and failover setup |

## Integration Notes

- **Role**: Camera source only, no video processing
- **Data flow**: Pi Zero → USB → Pi 4 → MediaMTX → Streaming
- **Management**: Remote via Pi 4 or direct SSH
- **Power**: Dependent on Pi 4 for power and internet