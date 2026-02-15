# 📖 Project Journal

The messy, honest, sometimes funny diary of building a smart birdhouse.

---

## 2026-02-15 — Day One: Badezimmer-Surveillance

**Participants:** martin (remote), thomas (on-site), mox (AI, sandboxed)

### What happened

- Set up SSH access from AI sandbox to Pi 4 via Tailscale ✅
- Discovered Pi Zero was running Trixie (broken on ARMv6) — reflashed to Bookworm Legacy Lite
- First photo from Pi 4 camera: **completely black** (camera was in Thomas's dark bathroom)
- Second photo with lights on: **Thomas's washing machine** in full glory 🧺
- "Waschmaschinen-Surveillance as a Service" was briefly considered as a Twitch category
- Set up SSH ProxyJump: Mox → Tailscale → Pi 4 → LAN → Pi Zero ✅
- First photo from Pi Zero NoIR camera: also the bathroom, but with IR illumination
- IR LED light cone test on radiator — beam angle ~90-120°, plenty for a birdhouse
- Identified camera module as Kuman SC15 compatible (OV5647 NoIR + 2x 850nm IR LEDs)
- Discovered IR LED power issue: both LEDs draw 1.8A from 3.3V rail (too much for Pi Zero!)
- Thomas's parents visiting, Pis moved from bathroom to living room
- Three people simultaneously tried to shut down the same Pi via SSH 😄

### Decisions made

- **NoIR camera (Pi Zero) → inside birdhouse** (Twitch main stream, 24/7 night vision)
- **IMX708 Wide (Pi 4) → outside/entrance** (B-camera, on-demand)
- **"Variant C" build:** Everything in birdhouse, removable tech-roof, single USB-C cable out
- **English repo** for wider reach, Austrian flavor in the journal

### Key learnings

- 850nm IR is invisible to songbirds (they see UV, not IR) ✅
- IR LEDs produce negligible heat (near-IR ≠ thermal radiation)
- Missing heatsink = LED runs hotter → draws more current → glows brighter → thermal runaway risk
- `libcamera-still` on Pi 4, `rpicam-still` on Pi Zero — don't mix them up
- Base64-over-SSH works for file transfer when SCP has permission issues

### Running jokes

- "Schleudergang Live" — the next ASMR Twitch hit
- "<YOUR_WIFI_SSID>" — best WiFi SSID ever
- Thomas photographs his thumb instead of the IR LED
- The AI keeps forgetting what we already discussed
