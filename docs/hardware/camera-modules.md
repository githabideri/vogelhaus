# Camera Modules

> Last updated: 2026-03

## OV5647 NoIR Camera Module

### Product Identification

**Module:** Kuman SC15 (or identical clone)
- Common brands: Kuman, DORHEA, SUKRAGRAHA, AZDelivery, generic suppliers
- Features: OV5647 sensor, two cylindrical 850nm IR LEDs with heatsinks, LDR sensor, adjustable potentiometer

### Technical Specifications

| Parameter | Value |
|-----------|-------|
| Sensor | OmniVision OV5647, 5MP |
| Resolution | Up to 2592x1944 (15fps), 1080p (30fps), 1296x972 (46fps) |
| FOV | 72.4° |
| IR LEDs | 2x 850nm, ~3W each |
| LED Current | ~909mA @ 3.3V per LED |
| Total LED Draw | ~1.8A from 3.3V rail |
| LDR | Automatic threshold switching, adjustable via potentiometer |
| Effective IR Range | 1-3 meters optimal |
| I2C Address | 0x36 |
| Interface | CSI (flex cable) |

### ⚠️ CRITICAL: Power Warning

**The two 3W IR LEDs together draw ~1.8A from the 3.3V rail!**

The Raspberry Pi Zero can only supply 1.0-1.5A on the 3.3V rail (including SoC consumption). This means:

- **Brownouts/freezes** when both LEDs are active
- **Unstable operation**, especially under load (camera + WiFi + LEDs)
- **Voltage regulator overload** → reduced lifespan

### Solutions (in order of recommendation):

1. **Operate only ONE LED** — sufficient for birdhouse interior (15-20cm distance)
2. **External power supply** — 5V→3.3V buck converter for LEDs, separate from Pi
3. **GPIO control with external power** — transistor circuit, LEDs only when needed

## Board Layout & Pinout

```
[LED1 + Heatsink] --- [OV5647 Lens] --- [LED2 + Heatsink]
                       [LDR]  [Potentiometer]

Back side:
[Heat fins] --- [Sensor chip] --- [Heat fins]
                [Flex cable connector]
```

**LED Power Supply:**
- Pad near LDR: +3.3V
- Pad near potentiometer: GND
- LDR switches LEDs via on-board transistor

**Potentiometer:** Controls light threshold for LED activation (clockwise = more sensitive)

## IR LED Thermal Analysis

### Observation
LED without heatsink glows visibly brighter and more red than the one with heatsink.

### Explanation
- **Wavelength drift:** ~0.1-0.3 nm/°C → at 30°C difference: 855-860nm (shifts FURTHER into IR, not into visible)
- **Main cause: Increased current** — without cooling, forward voltage drops → at same voltage MORE current flows → LED glows brighter
- A brighter 850nm LED also has stronger visible "tail" in red spectrum
- **Thermal runaway risk:** hotter → more current → even hotter → LED failure

### Recommendation
- Replace missing heatsink (aluminum plate + thermal adhesive)
- OR disconnect this LED (one is sufficient)
- Do not operate without cooling permanently

## Wildlife Camera Best Practices

From successful birdhouse projects with this module:

- **Distance:** Position NoIR cam 15-30cm from subject
- **Illumination:** One IR LED sufficient for small spaces (tit nesting box)
- **Cooling:** Do NOT remove heatsinks, provide ventilation in housing
- **LDR threshold:** Adjust potentiometer so LEDs only activate in true darkness
- **Purple tint:** Normal in daylight (NoIR = no IR filter = color distortion)
- **Power:** Separate power supply for LEDs recommended
- **Birds:** 850nm IR invisible to tits/songbirds, minimal red glow doesn't disturb

## IMX708 Wide Camera Module

### Specifications

| Parameter | Value |
|-----------|-------|
| Sensor | Sony IMX708, 12MP |
| Type | Pi Camera Module 3 (Wide) |
| Resolution | Up to 4608x2592, various aspect ratios |
| FOV | ~120° diagonal (wide angle) |
| Interface | CSI (22-pin flex cable) |
| IR Filter | Yes (not suitable for night vision) |
| Focus | Fixed focus, optimized for infinity |

### Usage Notes
- **Day camera only** — has IR-cut filter, requires external IR for night vision
- Use `libcamera-still` on Pi 4 (not `rpicam-still`)
- MediaMTX locks camera access — stop service for manual capture
- Suitable for nesting chamber monitoring from above and overview shots

## GPIO Control for IR LEDs (Advanced)

### Circuit
```
Pi GPIO Pin ──[1kΩ]──┤ Base
                      │
                   2N2222 (NPN)
                      │
              LED(+)──┤ Collector
                      │
                GND ──┤ Emitter

3.3V (external!) ──── LED(-)
```

### Software
```bash
# Enable LED
echo "18" > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio18/direction
echo "1" > /sys/class/gpio/gpio18/value

# Disable LED
echo "0" > /sys/class/gpio/gpio18/value
```

### Requirements
- Bypass LDR circuit on board (cut trace)
- External 3.3V supply for LEDs
- Transistor, 1kΩ resistor, wiring

## Known Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Pi freezes in darkness | Both LEDs overload 3.3V rail | Use only 1 LED or external power |
| Purple tint in daylight | NoIR has no IR filter | Normal, not fixable without hardware mod |
| LED glows visibly red | 850nm, not 940nm | Normal, no problem for birds |
| Image too dark at night | LEDs too weak or too far | Reduce distance (<1m), use reflector |
| Overheating | Missing/poor heatsink | Replace heatsink, use only 1 LED |
| `vcgencmd get_camera` shows `detected=0` | Known Pi Zero issue | Camera still works normally |