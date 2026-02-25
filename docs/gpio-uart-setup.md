# GPIO UART Fallback Link (Pi 4 ↔ Pi Zero W)

A 3-wire UART link provides an out-of-band rescue path between the two Pis.
It works independently of Wi-Fi and USB networking.

---

## Why this exists

Use UART as the **recovery/control plane** when:
- Wi-Fi association fails
- USB gadget/networking is unstable
- you still need shell access to the Pi Zero

Recommended default mode: **serial getty** (interactive login shell).

---

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

---

## Software setup

## 1) Enable UART in boot config

On both Pis (`/boot/firmware/config.txt` on Bookworm-based images):

```ini
enable_uart=1
```

For Pi Zero W, ensure the stable UART is available on GPIO:

```ini
dtoverlay=miniuart-bt
```

(Alternative: `dtoverlay=disable-bt` if Bluetooth is not needed at all.)

## 2) Keep serial login shell on the Pi Zero

On Pi Zero:

```bash
sudo systemctl enable --now serial-getty@ttyAMA0.service
```

## 3) Avoid port contention on the Pi 4 monitor side

If Pi 4 is used as the serial terminal for Pi Zero, disable getty on Pi 4 UART:

```bash
sudo systemctl disable --now serial-getty@ttyAMA0.service
```

---

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

---

## Operational modes

### Mode A: Getty (recommended default)
- Interactive shell over serial
- Lowest risk and simplest recovery path
- Ideal for diagnostics and emergency fixes

### Mode B: PPP over serial (optional)
- Provides IP over UART
- More complex and easy to misconfigure
- Not recommended as default; use only when intentionally needed

---

## Small file transfer over UART (emergency only)

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

---

## Where this fits in the repo

- Architecture overview: `README.md`
- Physical build routing: `docs/assembly.md`
- Hardware/network design: `docs/hardware.md`
- Failure handling and checks: `docs/troubleshooting.md`

---

## References

- https://pinout.xyz/pinout/uart
- https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-uarts
- https://elinux.org/RPi_Serial_Connection
