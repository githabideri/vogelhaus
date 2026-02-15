#!/usr/bin/env python3
"""
ir-led-control.py — GPIO control for IR LEDs on OV5647 NoIR camera module.

Requires hardware modification: bypass the onboard LDR circuit and route
LED power through an NPN transistor (e.g., 2N2222) controlled by a GPIO pin.

Wiring:
    GPIO Pin → 1kΩ resistor → Transistor Base
    External 3.3V → LED(+) → LED(-) → Transistor Collector
    Transistor Emitter → GND

References:
    - https://forums.raspberrypi.com/viewtopic.php?t=225060
    - https://sgvandijk.medium.com/the-electronics-and-electromagnetism-pertaining-to-a-baby-monitor-42b38bc4de1c
"""

import sys
import time

# Default GPIO pin for IR LED control
GPIO_PIN = 18
GPIO_PATH = f"/sys/class/gpio/gpio{GPIO_PIN}"


def gpio_export(pin):
    """Export GPIO pin to userspace."""
    try:
        with open("/sys/class/gpio/export", "w") as f:
            f.write(str(pin))
    except OSError:
        pass  # Already exported

    with open(f"{GPIO_PATH}/direction", "w") as f:
        f.write("out")


def gpio_set(pin, value):
    """Set GPIO pin high (1) or low (0)."""
    with open(f"/sys/class/gpio/gpio{pin}/value", "w") as f:
        f.write(str(value))


def gpio_cleanup(pin):
    """Unexport GPIO pin."""
    try:
        with open("/sys/class/gpio/unexport", "w") as f:
            f.write(str(pin))
    except OSError:
        pass


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <on|off|pulse [seconds]>")
        print(f"  on     — Turn IR LEDs on (GPIO {GPIO_PIN} HIGH)")
        print(f"  off    — Turn IR LEDs off (GPIO {GPIO_PIN} LOW)")
        print(f"  pulse  — Turn on for N seconds (default 5), then off")
        sys.exit(1)

    action = sys.argv[1].lower()
    gpio_export(GPIO_PIN)

    try:
        if action == "on":
            gpio_set(GPIO_PIN, 1)
            print(f"IR LEDs ON (GPIO {GPIO_PIN})")

        elif action == "off":
            gpio_set(GPIO_PIN, 0)
            print(f"IR LEDs OFF (GPIO {GPIO_PIN})")

        elif action == "pulse":
            duration = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
            gpio_set(GPIO_PIN, 1)
            print(f"IR LEDs ON for {duration}s...")
            time.sleep(duration)
            gpio_set(GPIO_PIN, 0)
            print("IR LEDs OFF")

        else:
            print(f"Unknown action: {action}")
            sys.exit(1)

    except KeyboardInterrupt:
        gpio_set(GPIO_PIN, 0)
        print("\nInterrupted — IR LEDs OFF")


if __name__ == "__main__":
    main()
