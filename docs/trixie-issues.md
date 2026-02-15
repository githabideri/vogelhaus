# Raspberry Pi Zero W v1.1 + Trixie OS: Issue Research Report
**Date:** 2026-02-15  
**Research Focus:** Compatibility, SSH, WiFi, and Network issues

---

## Executive Summary

**Critical Finding:** Raspberry Pi OS Trixie is **NOT recommended** for Pi Zero W v1.1 (ARMv6). Multiple open issues indicate significant compatibility problems, particularly with WiFi, networking infrastructure (Netplan/NetworkManager), and software compatibility.

**Key Recommendation:** Use **Raspberry Pi OS Bookworm Legacy (32-bit)** instead for Pi Zero W v1.

---

## 1. SSH Issues

### Status: LIMITED DIRECT EVIDENCE
- **No widespread SSH daemon failure reports found** specifically for Trixie on Pi Zero W
- However, related configuration issues exist:

#### Issue: Cloud-init configuration problems
- **GitHub Issue #26** - "Raspberry Pi OS trixie Lite: cloud-init keeps configuring after first boot"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/26
  - Status: Open | 14 comments
  - **Impact:** cloud-init modules run repeatedly instead of once, potentially interfering with SSH setup
  - **Root cause:** Raspberry Pi lacks RTC, causing incorrect timestamps that cloud-init relies on
  - **Implication:** SSH configuration via cloud-init/Imager may not persist properly

#### Issue: Boot disk ID mismatch (Fixed)
- **GitHub Issue #28** - "2025-10-01 Trixie Lite 32-bit images have wrong disk id"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/28
  - Status: Closed (Fixed in later images)
  - **Impact:** Systems couldn't boot due to `cmdline.txt` and `/etc/fstab` referencing wrong disk ID
  - **SSH implication:** No boot = no SSH access

---

## 2. WiFi Connectivity Issues ⚠️ CRITICAL

### Multiple confirmed WiFi problems in Trixie:

#### Issue #25: WiFi disconnects and won't reconnect
- **GitHub Issue #25** - "WiFi disconnects after some time, does not reconnect"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/25
  - Status: **Open** | 18 comments (very active)
  - **Symptoms:**
    - WiFi stable for 4-18 hours, then drops
    - Sometimes shows low signal, sometimes normal signal
    - Cannot reconnect automatically
    - Requires manual `nmcli connection down/up` to restore
  - **Affected:** Multiple Pi models including Pi 5
  - **Not fixed yet**

#### Issue #29: Cannot create wireless hotspot
- **GitHub Issue #29** - "Raspberry Pi 3b+ unable to create wireless hotspot under Trixie"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/29
  - Status: **Open** | 3 comments
  - **Symptoms:**
    - Works fine in Bookworm
    - Fails completely in Trixie
    - Affects Pi 3B+ (similar WiFi chipset to Zero W)
  - **Testing:** Verified with and without software updates

#### Issue #51: Access Point creation impossible
- **GitHub Issue #51** - "Access Point - Inability to create any Access Point"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/51
  - Status: **Open** | 3 comments
  - **Root cause:** **Netplan/NetworkManager architecture conflict**
  - **Developer assessment:**
    > "Netplan has become the 'single source of truth' for interface configuration... nmcli cannot just create an AP + DHCP"
  - **Impact:** Network management completely changed in Trixie
  - **Workaround:** Revert to legacy dnsmasq/hostapd (not ideal)

#### Issue #23: WiFi firmware issues on Zero 2W
- **GitHub Issue #23** - "Firmware issue with wifi-chip on Zero2w with *some* access-points"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/23
  - Status: **Open** | 2 comments
  - **Impact:** WiFi chip has firmware compatibility issues with certain access points

#### Issue #4282: Network bridge documentation broken
- **GitHub Issue #4282** - "Instructions for creating a network bridge don't work with current Trixie OS release"
  - URL: https://github.com/raspberrypi/documentation/issues/4282
  - Status: **Open** | 0 comments
  - **Tested on:** Pi Zero W with USB ethernet adapter
  - **Symptoms:** Official documentation procedures fail due to Netplan interference

---

## 3. Network Disappearing After Boot

### Related to WiFi issues above, plus:

#### Netplan/NetworkManager conflicts
- **GitHub Issue #40** - "Netplan - NetworkManager - Creating a second wireless network does not work"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/40
  - Status: **Open** | 4 comments

#### nmcli configuration persistence issues
- **GitHub Issue #3** - "nmcli creates nmconnection files in /run/NetworkManager/system-connections instead of /etc"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/3
  - Status: Closed | 45 comments (extensive discussion)
  - **Impact:** Network configurations may not persist across reboots

---

## 4. ARMv6 (Pi Zero W v1) Incompatibilities ⚠️ CRITICAL

### Official Recognition of Problems:

#### Issue #24: Stop recommending Trixie for Pi Zero
- **GitHub Issue #24** - "Stop the installer recommending Trixie for Pi Zero / W / WH"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/24
  - Status: **Open** | 10 comments
  - **Key points:**
    - Raspberry Pi Imager currently recommends Trixie for Pi Zero W
    - **This should be changed** according to community consensus
    - Recommended: Offer **Lite versions as default** for low-memory Pis
    - Developer assigned to modify official OS recommendation list

#### Issue #22: Browsers no longer compatible with ARMv6
- **GitHub Issue #22** - "[BUG]: Pi Zero W shows Trixie as recommended, but both browsers are no longer compatible"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/22
  - Status: Closed as "upstream issue" | 2 comments
  - **Critical finding:**
    - **Both Chromium and Firefox refuse to run** on Pi Zero W with Trixie
    - Error: Browsers are not compiled for ARMv6 architecture
    - Official response: "Upstream issue, nothing Raspberry Pi can do"
    - **Impact:** Desktop version essentially non-functional on Pi Zero W

#### Historical context - Linux Kernel Issue #4024
- **GitHub Issue #4024** - "firefox illegal instruction pi zero/zero w"
  - URL: https://github.com/raspberrypi/linux/issues/4024
  - Created: 2020-12-23 (predates Trixie)
  - Status: **Still open**
  - **Shows:** This is a long-standing ARMv6 compatibility problem

### Software Compatibility Issues:

#### From release notes (downloads.raspberrypi.com):
```
2022-04-04:
* OpenJDK 17 now defaults to 'client' JVM for ARMv6 compatibility
```
This shows ARMv6 has required special handling even in older releases.

#### Package availability concerns:
- **GitHub Issue #42** - "PiWheels PIP repository configuration is missing from the Trixie image"
  - URL: https://github.com/raspberrypi/trixie-feedback/issues/42
  - Status: Closed (Fixed)
  - **Impact:** 32-bit installs couldn't install many Python packages without PiWheels

---

## 5. Bookworm Legacy vs Trixie Recommendation

### Official OS List Analysis

**Available for Pi Zero W (pi1-32bit):**
1. ✅ Raspberry Pi OS (32-bit) - **Current Trixie-based**
2. ✅ **Raspberry Pi OS (Legacy, 32-bit)** - Bookworm-based
3. ✅ Raspberry Pi OS Lite (32-bit) - Trixie
4. ✅ Raspberry Pi OS Full (32-bit) - Trixie
5. ✅ **Raspberry Pi OS (Legacy, 32-bit) Lite** - Bookworm-based ⭐ **RECOMMENDED**
6. ✅ Raspberry Pi OS (Legacy, 32-bit) Full - Bookworm-based

### Community Consensus:
From Issue #24 discussion:
- **Trixie Desktop:** Not recommended (browsers don't work)
- **Trixie Lite:** May work but has networking issues
- **Bookworm Legacy Lite:** Most stable option for Pi Zero W

---

## 6. Key Technical Changes in Trixie (Root Causes)

### Networking Stack Overhaul:
1. **Netplan** introduced as "single source of truth" for network config
2. **NetworkManager** + Netplan integration issues
3. **cloud-init** conflicts with traditional configuration
4. **Breaking change:** nmcli cannot reliably create APs or custom network configs

### Kernel & Firmware:
- Kernel 6.12.47 (vs 6.1.x in Bookworm)
- New firmware with different WiFi chip behavior
- Some access point compatibility regressions

### Software Support:
- Chromium: No longer supports ARMv6
- Firefox: No longer supports ARMv6
- Various packages requiring ARMv7 minimum

---

## 7. Additional Relevant Issues

### DietPi Trixie Upgrade Thread
- **GitHub Issue #7644** - "Debian Trixie | Upgrade script support thread"
  - URL: https://github.com/MichaIng/DietPi/issues/7644
  - Status: **Open** | 328 comments (massive discussion)
  - **Context:** Community-maintained lightweight distribution
  - **Shows:** Extensive testing required for Trixie compatibility across Pi models

### Imager Customization Issues
- **GitHub Issue #1439** - "[BUG]: Image Customisation settings not applied"
  - URL: https://github.com/raspberrypi/rpi-imager/issues/1439
  - Status: **Open** | 34 comments
  - **Possible SSH impact:** Pre-configured SSH settings may not apply correctly

---

## 8. Recommendations

### For Pi Zero W v1.1:

#### ✅ RECOMMENDED:
- **Raspberry Pi OS (Legacy, 32-bit) Lite** (Bookworm-based)
  - Proven stable
  - All networking features work
  - SSH works reliably
  - WiFi is stable

#### ⚠️ USE WITH CAUTION:
- **Trixie Lite (32-bit)** - If you must use Trixie:
  - Expect WiFi disconnection issues
  - Be prepared to manually manage networking
  - SSH may work but network instability affects access
  - Access point creation won't work without legacy tools

#### ❌ NOT RECOMMENDED:
- **Trixie Desktop (any variant)** for Pi Zero W
  - Browsers don't work (ARMv6 incompatible)
  - 512MB RAM too limiting for GUI
  - Officially acknowledged as problematic

### Workarounds if stuck on Trixie:

#### For WiFi disconnections:
```bash
# Monitor connection, restart if needed
watch -n 60 'ping -c 1 8.8.8.8 || nmcli connection down preconfigured && nmcli connection up preconfigured'
```

#### For Access Point creation:
- Revert to legacy hostapd + dnsmasq configuration
- Disable Netplan interference
- See Issue #51 for details

#### For SSH:
- Use wired connection if possible (USB ethernet)
- Ensure cloud-init completes fully before expecting SSH
- Check `sudo systemctl status ssh` and `sudo systemctl status sshd`

---

## 9. Sources & Links

### Primary GitHub Repositories:
- **raspberrypi/trixie-feedback** - Main issue tracker for Trixie
  - https://github.com/raspberrypi/trixie-feedback/issues

### Critical Issues:
1. https://github.com/raspberrypi/trixie-feedback/issues/24 - Stop recommending Trixie for Zero
2. https://github.com/raspberrypi/trixie-feedback/issues/22 - Browsers incompatible
3. https://github.com/raspberrypi/trixie-feedback/issues/25 - WiFi disconnects
4. https://github.com/raspberrypi/trixie-feedback/issues/51 - Access Point broken
5. https://github.com/raspberrypi/trixie-feedback/issues/29 - Hotspot creation fails
6. https://github.com/raspberrypi/trixie-feedback/issues/26 - cloud-init configuration loops
7. https://github.com/raspberrypi/documentation/issues/4282 - Network bridge broken

### Official Resources:
- OS Downloads: https://downloads.raspberrypi.com/
- Release Notes: https://downloads.raspberrypi.com/raspios_lite_armhf/release_notes.txt
- OS List (Imager): https://downloads.raspberrypi.com/os_list_imagingutility_v4.json

### Community:
- DietPi Trixie Testing: https://github.com/MichaIng/DietPi/issues/7644

---

## 10. Conclusion

**Raspberry Pi OS Trixie is currently problematic for Pi Zero W v1.1** due to:

1. ❌ **ARMv6 architecture incompatibilities** (browsers don't work)
2. ❌ **Netplan/NetworkManager conflicts** causing WiFi and networking issues
3. ❌ **Active open issues** with no clear resolution timeline
4. ❌ **Community consensus** that it should not be recommended
5. ⚠️ **Developers assigned** to change official recommendations

**The Pi Zero W v1 is based on ARMv6 (BCM2835), which is increasingly unsupported by modern software.** Trixie's move to newer Debian packages has exposed these limitations.

### Clear Answer: Use Bookworm Legacy (32-bit) Lite for Pi Zero W v1.1

This provides:
- ✅ Stable WiFi
- ✅ Working SSH
- ✅ Persistent network configuration
- ✅ Access point capabilities
- ✅ Known-good software compatibility

---

**Report compiled:** 2026-02-15  
**Research method:** GitHub issue tracking, official documentation, release notes  
**Primary sources:** raspberrypi/trixie-feedback repository, official Raspberry Pi documentation
