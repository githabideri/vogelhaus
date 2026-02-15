# Troubleshooting

## Pi Zero W: Do NOT Use Trixie

Raspberry Pi OS Trixie (Debian 13) is broken on Pi Zero W v1.1 (ARMv6):
- WiFi doesn't work (firmware loading fails)
- USB Gadget mode broken
- Many packages unavailable for armhf/armel

**Use Raspberry Pi OS Legacy Lite (Bookworm-based, 32-bit) instead.**

See `pi_zero_w_trixie_issues_report.md` for the full investigation.

## Camera Not Detected

`vcgencmd get_camera` may show `detected=0` even when the camera works fine. Test with:
```bash
# Pi Zero
rpicam-hello --list-cameras

# Pi 4
libcamera-hello --list-cameras
```

## Pi 4: Camera Locked by mediamtx

If `libcamera-still` fails with a "camera busy" error:
```bash
sudo systemctl stop mediamtx
libcamera-still -o photo.jpg
sudo systemctl start mediamtx
```

## Pi Freezes in the Dark

Both IR LEDs draw ~1.8A from the 3.3V rail, exceeding the regulator's capacity. Solutions:
1. Disconnect one IR LED
2. Use external power for LEDs
3. See [Power Warning](hardware.md#⚠️-power-warning)

## Boot Config: Line Endings Matter

`cmdline.txt` MUST have Unix line endings (LF), not Windows (CR LF). If edited on Windows:
```bash
sed -i 's/\r$//' /boot/firmware/cmdline.txt
```

## SSH Tips

- Pi 4 command: `libcamera-still` 
- Pi Zero command: `rpicam-still`
- Don't mix them up — they're different packages

## Night Vision: Purple Tint

NoIR cameras show a purple tint in daylight. This is normal — the missing IR filter lets infrared light through, which the sensor interprets as purple/magenta. In darkness with IR LEDs, the image is grayscale.

For better night images, force grayscale:
```bash
rpicam-still -o photo.jpg --saturation 0
```
