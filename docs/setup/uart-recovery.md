# UART Recovery Link

> Last updated: 2026-03

A 3-wire UART link provides an out-of-band rescue path between the Pi 4 and Pi Zero W.
It works independently of Wi-Fi and USB networking.

## Why This Exists

Use UART as the **recovery/control plane** when:
- Wi-Fi association fails
- USB gadget/networking is unstable
- You still need shell access to the Pi Zero

Recommended default mode: **serial getty** (interactive login shell).

## Wiring (3 wires only)

```
Pi 4 TX (GPIO14, pin 8)   -> Pi Zero RX (GPIO15, pin 10)
Pi 4 RX (GPIO15, pin 10)  -> Pi Zero TX (GPIO14, pin 8)
Pi 4 GND (pin 6)          -> Pi Zero GND (pin 6)
```

### Rules
- Cross TX/RX, connect GND, **do not connect 3.3V**
- Both boards are 3.3V TTL, no level shifter needed
- Keep cable length moderate and strain-relieved inside the roof


## Additional Wire: RUN-Pin Reset (4th wire)

For remote reset capability, add a 4th connection:

```
Pi 4 GPIO 17 (pin 11, inner row) -> Pi Zero RUN pad (square pad near the header)
```

### Physical Connection

- **Wire colors in our build:** Orange (Zero end) → crimp adapter → Brown (Pi 4 end)
- **Connection type:** Plugged (Dupont connectors), not soldered
- **RUN pad location:** Square pad on the Pi Zero board near the GPIO header

### Function

Pulling GPIO 17 LOW for ~0.2 seconds triggers a hardware reset of the Pi Zero.
The Pi Zero will restart and be back online in approximately 40 seconds.

### Usage

First, export and configure GPIO 17 (one-time setup, or via boot script/udev rule):

```bash
echo 17 > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio17/direction
echo 1 > /sys/class/gpio/gpio17/value  # HIGH = normal operation
```

To reset the Pi Zero:

```bash
echo 0 > /sys/class/gpio/gpio17/value  # Pull LOW
sleep 0.2
echo 1 > /sys/class/gpio/gpio17/value  # Release
```

### Automatic USB Network Restoration

After a RUN-pin reset, the USB network connection is automatically restored by:

- **udev rule:** `/etc/udev/rules.d/90-usb-zero-network.rules`
- **Helper script:** `/usr/local/bin/usb-zero-reconnect.sh`

These detect the Pi Zero's USB gadget reappearance and reconfigure the network interface.

### Integration

The RUN-pin reset provides a hardware-level recovery mechanism when:
- Pi Zero software is hung but Pi 4 is responsive
- UART shell access is unavailable or not responding
- USB network has failed but you want to trigger a clean restart

**Note:** This is a hard reset — unsaved work on the Pi Zero will be lost.

## Software Setup

### 1) Enable UART in boot config

On both Pis (`/boot/firmware/config.txt` on Bookworm-based images):

```ini
enable_uart=1
```

For Pi Zero W, ensure the stable UART is available on GPIO:

```ini
dtoverlay=miniuart-bt
```

(Alternative: `dtoverlay=disable-bt` if Bluetooth is not needed at all.)

### 2) Keep serial login shell on the Pi Zero

On Pi Zero:

```bash
sudo systemctl enable --now serial-getty@ttyAMA0.service
```

### 3) Avoid port contention on the Pi 4 monitor side

If Pi 4 is used as the serial terminal for Pi Zero, disable getty on Pi 4 UART:

```bash
sudo systemctl disable --now serial-getty@ttyAMA0.service
```

## Connect from Pi 4

```bash
screen /dev/ttyAMA0 115200
```

Useful checks:

```bash
readlink -f /dev/serial0
stty -F /dev/ttyAMA0 -a
```

If no prompt appears, send Enter a few times.

## Operational Modes

### Mode A: Getty (recommended default)
- Interactive shell over serial
- Lowest risk and simplest recovery path
- Ideal for diagnostics and emergency fixes

### Mode B: PPP over serial (optional)
- Provides IP over UART
- More complex and easy to misconfigure
- Not recommended as default; use only when intentionally needed

## Small File Transfer over UART (emergency only)

UART can carry small files as base64 if needed.

Sender (Pi Zero shell):

```bash
echo __B64_BEGIN__
base64 -w0 /tmp/test.jpg
echo
echo __B64_END__
```

Receiver parses data between markers and decodes base64.

### Throughput expectation at 115200 (8N1)
- Practical payload: ~11 kB/s
- Example: ~55 kB image transfers in ~7–10 seconds

So this is fine for occasional diagnostics, not for normal media workflows.

## Emergency Access Examples

### Check Pi Zero status from Pi 4
```bash
# Connect to Pi Zero via UART
screen /dev/ttyAMA0 115200

# Once connected (in Pi Zero shell):
systemctl status
df -h
ip addr show
```

### Restart services on Pi Zero
```bash
# From Pi Zero UART shell:
sudo systemctl restart usb-gadget
sudo systemctl restart tailscale
```

### Network troubleshooting
```bash
# Check connectivity from Pi Zero:
ping 8.8.8.8
ip route
cat /etc/resolv.conf
```

## Integration Notes

- Physical wiring documented in [Assembly Guide](../hardware/assembly.md)
- Network troubleshooting procedures in [Troubleshooting](../operations/troubleshooting.md)
- USB Gadget alternative in [USB Gadget Setup](usb-gadget.md)

## References

- https://pinout.xyz/pinout/uart
- https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-uarts
- https://elinux.org/RPi_Serial_Connection