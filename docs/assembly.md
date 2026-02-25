# Assembly Guide

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
4. **UART fallback wiring** — Add a fixed 3-wire GPIO UART link between Pi 4 and Pi Zero for recovery access
5. **Ventilation** — Air holes in the roof (Pi 4 heat = bird heating in winter 😄)
6. **Weather protection** — Sealed enclosure, cable grommet for USB-C exit

### Camera Placement

- **NoIR camera (Pi Zero):** Points DOWN into the nesting area — this is the main Twitch stream
- **IMX708 Wide (Pi 4):** Points toward the entrance hole — B-camera for on-demand snapshots

### Parts Needed

- [ ] Short camera flex cable for Pi Zero (10-15cm)
- [ ] Short USB data cable Pi 4 → Pi Zero
- [ ] 3-wire jumper set / soldered wires for UART fallback (GND, TX, RX)
- [ ] Weatherproof housing/sealing for tech compartment
- [ ] Mounting hardware for Pis inside the roof

### Build Steps

> 🚧 TODO: Detailed step-by-step instructions once the physical build is complete.

1. Prepare the birdhouse (standard nesting box with removable roof)
2. Mount Pi 4 and Pi Zero on the roof interior
3. Connect cameras with short flex cables
4. Route cameras to their positions (NoIR down, IMX708 toward entrance)
5. Connect Pi Zero to Pi 4 via USB
6. Add UART fallback wiring (Pi4 TX->Zero RX, Pi4 RX->Zero TX, GND->GND)
7. Drill ventilation holes
8. Route USB-C power cable out through sealed grommet
9. Test everything before sealing
10. Mount birdhouse outside

For UART pin mapping and service setup, see [GPIO UART Setup](gpio-uart-setup.md).
