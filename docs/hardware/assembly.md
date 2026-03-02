# Assembly Guide

> Last updated: 2026-03

## Design: "Variant C" — Everything Inside

The chosen design puts all electronics inside the birdhouse with a removable tech-roof.

### Concept

```
┌─────────────────────────────┐
│     Removable Tech Roof     │ ← Pi 4 + Pi Zero + connections
│  ┌──────┐  USB  ┌────────┐ │
│  │Pi Zero├──────►│  Pi 4  │ │
│  │+NoIR  │      │+IMX708 │ │
│  └──┬───┘      └───┬────┘ │
│     │cam            │cam    │
├─────┼───────────────┼──────┤
│     ▼               ▼      │
│  [Nest area]    [Entrance] │
│                             │
│         Birdhouse           │
└─────────────────────────────┘
          │
     USB-C cable
     (single cable out)
```

### Key Design Decisions

1. **Removable roof** — All tech mounted on the roof piece for easy maintenance
2. **Single cable** — Only USB-C power cable exits the birdhouse
3. **Short flex cables** — Cameras close to Pis, avoiding signal issues from long ribbon cables
4. **UART fallback wiring** — Add a fixed 4-wire (UART + RUN-pin reset) GPIO UART link between Pi 4 and Pi Zero for recovery access
5. **Ventilation** — Air holes in the roof (Pi 4 heat = bird heating in winter 😄)
6. **Weather protection** — Sealed enclosure, cable grommet for USB-C exit

### Camera Placement

- **Camera A (Pi 4, IMX708 Wide):** Top-down view of the nesting chamber (mounted in the ceiling/roof area, looking straight down)
- **Camera B (Pi Zero, OV5647 NoIR):** Angled top-down view of the same nesting chamber area (mounted at an angle from above, same perspective as Camera A but from a different angle). Has IR illumination for night vision. Planned to be repositioned toward the entrance during next roof opening.

### Parts Needed

- [ ] Short camera flex cable for Pi Zero (10-15cm)
- [ ] Short USB data cable Pi 4 → Pi Zero
- [ ] 4-wire connection set for UART + RUN-pin reset (GND, TX, RX, GPIO17→RUN)
- [ ] Weatherproof housing/sealing for tech compartment
- [ ] Mounting hardware for Pis inside the roof

### Build Steps

> 🚧 TODO: Detailed step-by-step instructions once the physical build is complete.

1. Prepare the birdhouse (standard nesting box with removable roof)
2. Mount Pi 4 and Pi Zero on the roof interior
3. Connect cameras with short flex cables
4. Route cameras to their positions (both pointing at the nesting area from above, Camera A straight down, Camera B at an angle)
5. Connect Pi Zero to Pi 4 via USB
6. Add UART + RUN-pin wiring (Pi4 TX->Zero RX, Pi4 RX->Zero TX, GND->GND, Pi4 GPIO17->Zero RUN pad)
7. Drill ventilation holes
8. Route USB-C power cable out through sealed grommet
9. Test everything before sealing
10. Mount birdhouse outside


For RUN-pin reset wiring (4th wire, remote reboot capability), see [GPIO UART Setup — RUN-Pin Reset](../setup/uart-recovery.md#additional-wire-run-pin-reset-4th-wire).
