# dhcpcd Crash Issue (Debian Bullseye)

## Summary

**Issue:** dhcpcd 8.1.2 (Raspberry Pi OS Bullseye) crashes frequently with SEGV when Docker veth interfaces appear/disappear.

**Impact:** MINIMAL - Network stays up thanks to workarounds, but dhcpcd restarts every 10-60 seconds.

**Status:** KNOWN ISSUE, workaround deployed, monitoring stability.

---

## Root Cause

### Affected Version
- **OS:** Raspberry Pi OS (Debian Bullseye 11)
- **dhcpcd:** 8.1.2-1+rpt9
- **Upstream bugs:** 
  - https://github.com/NetworkConfiguration/dhcpcd/issues/156
  - https://github.com/NetworkConfiguration/dhcpcd/issues/235

### Trigger
- Docker veth interfaces (virtual ethernet pairs for containers)
- dhcpcd attempts to manage veth interfaces on hotplug
- NULL pointer dereference in dhcp.c:263 or dhcp.c:3339
- Result: SEGV crash

### Timeline
- **28.02.2026 13:42 CET:** First crash after implementing dhcpcd override (coincidence)
- **28.02-04.03.2026:** System ran 4+ days with constant crashes (~180/day)
- **04.03.2026 11:02 CET:** Undervoltage event caused system crash (unrelated to dhcpcd)
- **04.03.2026 12:00 CET:** System restarted, dhcpcd crashes continue

---

## Workaround (Deployed)

### Configuration Files

**`/etc/dhcpcd.conf`:**
```bash
# Persist interface configuration when dhcpcd exits
persistent
```

**`/etc/systemd/system/dhcpcd.service.d/override.conf`:**
```ini
[Service]
# Don't send RELEASE on stop (prevents network loss during crash)
ExecStop=

# Restart on failure (auto-recovery)
Restart=on-failure
RestartSec=10

# Rate limiting to prevent runaway restarts
StartLimitBurst=5
StartLimitIntervalSec=60
```

### How It Works

1. **`persistent`** → Kernel keeps IP addresses even when dhcpcd dies
2. **`ExecStop=`** → No DHCP RELEASE sent on crash (network stays up)
3. **`Restart=on-failure`** → systemd automatically restarts dhcpcd
4. **Rate limiting** → Prevents infinite crash-loop if something goes really wrong

### Result
- ✅ Network stays stable (no IP loss, no connectivity interruption)
- ⚠️ dhcpcd crashes every 10-60 seconds (cosmetic, logs are noisy)
- ✅ Auto-recovery within seconds

---

## Attempted Fixes (Did NOT Work)

### ❌ `denyinterfaces veth*`
```bash
# Added to /etc/dhcpcd.conf
denyinterfaces veth*
```

**Result:** dhcpcd still crashes BEFORE processing the deny rule.

### ❌ `allowinterfaces eth0 wlan0 wlan1 usb0`
```bash
# Added to /etc/dhcpcd.conf
allowinterfaces eth0 wlan0 wlan1 usb0
```

**Result:** dhcpcd crashes on usb0 (Pi Zero USB-Gadget) with same bug.

**Conclusion:** The bug is triggered during interface discovery, BEFORE dhcpcd reads interface filters.

---

## Long-Term Solutions

### Option 1: OS Upgrade to Bookworm
**Pros:**
- dhcpcd 9.4.1 available (has some fixes)
- Modern package versions

**Cons:**
- Major OS upgrade (risky for production system)
- Bookworm dhcpcd 9.4.1 STILL has the bug (fixed in 9.5.x)
- Not available as stable Raspberry Pi OS yet (as of March 2026)

### Option 2: Wired Ethernet (RECOMMENDED)
**Setup:**
- Use flat Ethernet cable instead of WiFi
- Benefits:
  - **dhcpcd crashes reduced** (no WiFi hotplug events)
  - **Undervoltage risk reduced** (WiFi uses 300-500mA, Ethernet ~100mA)
  - **More stable** (no WiFi reconnects)
  - **Faster** (1 Gbps vs ~150 Mbps WiFi)

**Status:** Under consideration (Thomas evaluating flat cable purchase)

### Option 3: Switch to NetworkManager
**Pros:**
- Modern, actively maintained
- Better Docker integration
- No known crash bugs

**Cons:**
- Different configuration paradigm
- Requires testing/migration effort
- May affect existing scripts that read dhcpcd state

### Option 4: Wait for Raspberry Pi OS Bookworm + dhcpcd 9.5+
**Status:** Best long-term option when available.

---

## Monitoring

### Check dhcpcd Status
```bash
systemctl status dhcpcd
```

### Count Recent Crashes
```bash
journalctl -u dhcpcd --since '1 hour ago' | grep -c SEGV
```

### Verify Network Stays Up
```bash
# IPs should persist even during crashes
ip addr show eth0 wlan0
```

### Baseline (as of 04.03.2026)
- Crashes: ~6-12 per hour
- Network uptime: 100% (no interruptions)
- System stable despite crashes

---

## References

- [GitHub dhcpcd Issue #156](https://github.com/NetworkConfiguration/dhcpcd/issues/156)
- [GitHub dhcpcd Issue #235](https://github.com/NetworkConfiguration/dhcpcd/issues/235)
- [Debian Bug #1024357](https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1024357)
- [RaspberryPi Forums Thread](https://forums.raspberrypi.com/viewtopic.php?t=269253)

---

## Decision Log

**04.03.2026:**
- Attempted `denyinterfaces veth*` → Failed
- Attempted `allowinterfaces` → Failed
- Decision: Accept crashes, maintain stable network via workaround
- Future: Evaluate wired Ethernet (reduces crashes + undervoltage risk)

**Status:** STABLE WORKAROUND DEPLOYED, monitoring over next few days.
