# Pi Zero W Flash Guide

> Last updated: 2026-03

This guide walks through completely setting up a Raspberry Pi Zero W from scratch, with USB Gadget mode and network configuration.

## Overview

| Component | Details |
|-----------|---------|
| Device | Raspberry Pi Zero W v1.1 |
| OS | Raspberry Pi OS Legacy Lite (Bookworm, 32-bit) |
| Hostname | `voglberry-light` |
| User | `vb-light` |
| Password | `1234` (temporary, changed after setup) |
| WiFi | `<YOUR_WIFI_SSID>` (2.4 GHz) |
| USB Gadget | `dwc2` + `libcomposite` (fixed MAC address) |

## Prerequisites

- [ ] Pi 4 running and connected via LAN cable to router
- [ ] Pi Zero W disconnected from Pi 4
- [ ] SD card (32GB) removed from Pi Zero
- [ ] Card reader connected to Windows PC
- [ ] Raspberry Pi Imager installed (https://www.raspberrypi.com/software/)

## Phase 1: Flash SD Card

### Step 1: Start Raspberry Pi Imager

Open the program. You'll see three large buttons.

### Step 2: Choose Device

- Click **"Choose Device"**
- Select: **Raspberry Pi Zero** (⚠️ NOT "Zero 2 W"! In Imager it's just called "Zero")

### Step 3: Choose Operating System

- Click **"Choose OS"**
- Select: **Raspberry Pi OS (other)**
- Then: **Raspberry Pi OS (Legacy, 32-bit) Lite**

⚠️ **IMPORTANT:**
- Must be "Legacy" (not regular Raspberry Pi OS)
- Must be "Lite" (without desktop)
- Must be "32-bit"

### Step 4: Choose SD Card

- Click **"Choose Storage"**
- Select your 32GB SD card
- If nothing appears: unplug card reader and reconnect

> ⚠️ **Card reader bug:** Sometimes only works once after Windows startup.
> If it fails: restart Windows completely, then do everything in one go.

### Step 5: Open Settings

- Click **"Next"**
- Dialog appears: "Use OS customisation?"
- Click **"Edit Settings"**

### Step 6: General Settings

In the **"GENERAL"** tab:

| Setting | Value |
|---------|-------|
| ☑ Set hostname | `voglberry-light` |
| ☑ Set username and password | |
| → Username | `vb-light` |
| → Password | `1234` |
| ☑ Configure wireless LAN | |
| → SSID | `<YOUR_WIFI_SSID>` |
| → Password | *[enter your WiFi password]* |
| → Wireless LAN country | `AT` |
| ☑ Set locale settings | |
| → Time zone | `Europe/Vienna` |
| → Keyboard layout | `de` |

### Step 7: Services Settings

In the **"SERVICES"** tab:

| Setting | Value |
|---------|-------|
| ☑ Enable SSH | |
| → Use password authentication | ☑ (check this!) |

### Step 8: Save and Flash

1. Click **"Save"**
2. Click **"Yes"** for "Use OS customisation?"
3. Click **"Yes"** for "All existing data will be erased"
4. **Wait** — takes about 5 minutes
5. When done: **DON'T eject yet!** → Continue to Phase 2

## Phase 2: Prepare USB Gadget

After flashing, the SD card has a partition called **"bootfs"** that Windows can read.

### Step 9: Edit config.txt

1. Open **Windows Explorer**
2. Go to the **"bootfs"** drive
3. Right-click **`config.txt`** → **"Open with"** → **Notepad**
4. Scroll to the **bottom**
5. Add as the **last line**:

```
dtoverlay=dwc2
```

6. **Save** (Ctrl+S) and close

### Step 10: Edit cmdline.txt

⚠️ **VERY IMPORTANT:** This file has only **ONE SINGLE LINE!** Do not line-break!

1. Right-click **`cmdline.txt`** → **"Open with"** → **Notepad**
2. You'll see one long line. Find the word `rootwait`
3. **Directly AFTER** `rootwait` add a space and insert:

```
modules-load=dwc2,g_ether
```

4. The result should look like this:

**Before:**
```
... rootwait quiet ...
```

**After:**
```
... rootwait modules-load=dwc2,g_ether quiet ...
```

5. Verify: **Everything must be on ONE line!**

> ⚠️ **IMPORTANT:** `g_ether` MUST be included! Without g_ether there's no USB network on first boot and SSH access fails. Later g_ether is replaced by libcomposite (for stable MAC addresses).

6. **Save** (Ctrl+S) and close

### Step 11: Eject SD Card

1. Right-click the "bootfs" drive in Explorer
2. Click **"Eject"**
3. Wait until Windows says "safe to remove"
4. Unplug card reader
5. Remove SD card from reader

## Phase 3: Start Pi Zero

### Step 12: Insert SD Card

1. Insert SD card into Pi Zero
   - Contacts facing up (toward board)
   - Push gently until it clicks

### Step 13: Connect Pi Zero

1. Take the **data cable** (USB-A to Micro-USB)
2. Insert **micro-USB end** into Pi Zero
   - ⚠️ Into the **middle** USB port! (labeled "USB", NOT "PWR")
3. Insert **USB-A end** into Pi 4

The Pi Zero boots automatically (gets power via USB from Pi 4).

### Step 14: Wait and Monitor

- **Green LED** on Pi Zero should **blink** (= booting)
- First boot takes **1-2 minutes** (SD card setup)
- When LED stops rapid blinking after 2 minutes → ready

### Step 15: Report Status

Message to administrator:

> "Pi Zero flashed, SD card inserted, connected to Pi 4. LED was blinking."

## Phase 4: Remote Configuration

*From here, remote configuration takes over via SSH.*

### Configuration Steps:

1. **Test SSH access** (via WiFi ProxyJump through Pi 4)
2. **Set up USB Gadget** (libcomposite with fixed MAC address)
   - Pi Zero MAC: `02:22:33:44:55:66`
   - Pi 4 MAC: `02:22:33:44:55:67`
3. **Configure USB network** (static IPs)
   - Pi Zero: `169.254.246.2`
   - Pi 4: `169.254.246.156`
4. **Install USB Failover** (mutual WiFi sharing)
5. **Exchange SSH keys** (Pi 4 ↔ Pi Zero)
6. **Install Tailscale** (remote access)
7. **Test camera** (`rpicam-still`)
8. **Reboot test** (verify configuration survives)

### Post-Setup Checklist:

- [ ] SSH via WiFi works
- [ ] SSH via USB Gadget works (169.254.246.2)
- [ ] USB Gadget MAC is fixed (02:22:33:44:55:66)
- [ ] USB Failover active on both Pis
- [ ] Tailscale connected
- [ ] Camera takes photos
- [ ] Reboot test passed (IPs and MACs same as before)
- [ ] Temporary password `1234` changed

## Troubleshooting

### "LED doesn't blink"
- SD card properly inserted? (Click when inserting?)
- USB cable in correct port? (USB, not PWR!)
- Try different USB cable (must be data cable, not charge-only)

### "SSH access fails"
- Wait! First boot needs up to 2 minutes
- WiFi password entered correctly?
- Disconnect Pi Zero, wait 10 seconds, reconnect

### "Card reader shows nothing"
- Restart Windows
- Use card reader immediately after boot (bug: only works once)
- Do everything in ONE session!

### "Imager doesn't show Legacy OS"
- Update Raspberry Pi Imager (latest version from website)
- Look under "Raspberry Pi OS (other)"

## Technical Details

### Flash Settings Summary
```yaml
Device: Raspberry Pi Zero W
OS: Raspberry Pi OS (Legacy, 32-bit) Lite — Bookworm
Hostname: voglberry-light
User: vb-light
Password: 1234
WiFi: <YOUR_WIFI_SSID> (2.4 GHz, AT)
SSH: enabled (password auth)
Timezone: Europe/Vienna
Keyboard: de

Manual boot edits:
  config.txt:  dtoverlay=dwc2 (last line)
  cmdline.txt: modules-load=dwc2,g_ether (after rootwait)
```

### USB Gadget Architecture
```
Pi Zero W (voglberry-light)              Pi 4 (voglberry)
┌──────────────────────┐                ┌──────────────────────┐
│ usb-gadget.service   │                │                      │
│ (libcomposite)       │                │                      │
│                      │    USB OTG     │                      │
│ usb0: 169.254.246.2  │◄──────────────►│ usb0: 169.254.246.156│
│ MAC: 02:22:33:44:55:66                │ MAC: 02:22:33:44:55:67
│                      │                │                      │
│ wlan0: DHCP          │                │ wlan0: <PI4_WLAN_IP> │
│ (<YOUR_WIFI_SSID>,   │                │ (<YOUR_WIFI_SSID>,   │
│  2.4GHz)             │                │  5GHz)               │
│                      │                │ eth0: <PI4_LAN_IP>   │
│                      │                │ (LAN cable)          │
│ usb-failover.sh ◄────────────────────►│ usb-failover.sh      │
│ (shares Pi4 WiFi/LAN)│                │ (shares Zero WiFi)   │
└──────────────────────┘                └──────────────────────┘
```