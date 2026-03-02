# Network Topology

> Last updated: 2026-03

This document provides a comprehensive overview of the network architecture used in the Vogelhaus project.

## Overview

The system uses multiple network layers for redundancy and different access methods:

1. **WiFi networks** (primary connectivity)
2. **USB Gadget network** (Pi-to-Pi communication)
3. **Ethernet** (Pi 4 wired backup)
4. **Tailscale VPN** (remote access)
5. **GPIO UART** (emergency out-of-band access)

## Network Diagram

```
                    Internet
                        │
                ┌───────┴────────┐
                │  Router/ISP    │
                │  <ROUTER_IP>   │
                └─┬─────────────┬┘
                  │             │
              WiFi 5GHz     Ethernet
                  │             │
          ┌───────┴──────┐      │
          │   Pi 4       │◄─────┘
          │ voglberry    │
          │ WiFi: <PI4_WLAN_IP>
          │ LAN:  <PI4_LAN_IP>
          │ USB:  <PI4_USB_IP>
          │ TS:   <TAILSCALE_PI4>
          └──────┬───────┘
                 │ USB OTG
                 │
          ┌──────┴───────┐
          │   Pi Zero W  │
          │voglberry-light│
          │ WiFi: <ZERO_WLAN_IP>
          │ USB:  <ZERO_USB_IP>
          │ TS:   <TAILSCALE_ZERO>
          └──────────────┘
```

## Network Configuration

### WiFi Networks

| Network | Frequency | SSID | Usage |
|---------|-----------|------|-------|
| Primary | 5 GHz | `<YOUR_WIFI_SSID>` | Pi 4 main connection |
| Fallback | 2.4 GHz | `<YOUR_WIFI_SSID_ALT>` | Pi Zero, emergency backup |

**Note**: 2.4 GHz network has known issues with ARRIS router firmware causing Broadcom WiFi chip problems. Use 5 GHz when possible.

### IP Address Allocation

#### Pi 4 (voglberry)
| Interface | IP Address | Gateway | Purpose |
|-----------|------------|---------|---------|
| `wlan0` | `<PI4_WLAN_IP>` | `<ROUTER_IP>` | Primary WiFi |
| `eth0` | `<PI4_LAN_IP>` | `<ROUTER_IP>` | Ethernet backup |
| `usb0` | `<PI4_USB_IP>` | N/A | USB Gadget host |

#### Pi Zero W (voglberry-light)
| Interface | IP Address | Gateway | Purpose |
|-----------|------------|---------|---------|
| `wlan0` | `<ZERO_WLAN_IP>` | `<ROUTER_IP>` | WiFi connectivity |
| `usb0` | `<ZERO_USB_IP>` | `<PI4_USB_IP>` | USB Gadget client |

### USB Gadget Network

The USB Gadget network provides direct Pi-to-Pi communication:

- **Network**: `169.254.246.0/16` (link-local)
- **Pi 4 (host)**: `<PI4_USB_IP>`
- **Pi Zero (gadget)**: `<ZERO_USB_IP>`
- **Purpose**: 
  - Fallback internet sharing
  - Direct communication when WiFi fails
  - Camera stream forwarding

### Tailscale VPN

Tailscale provides secure remote access to both devices:

| Device | Tailscale IP | Hostname | Access |
|--------|--------------|----------|--------|
| Pi 4 | `<TAILSCALE_PI4>` | `voglberry` | Direct SSH, web services |
| Pi Zero | `<TAILSCALE_ZERO>` | `voglberry-light` | SSH (when online) |

## DNS Configuration

### Pi 4
```
nameserver 1.1.1.1
nameserver 8.8.8.8
```

### Pi Zero
```
# Normal mode (WiFi)
nameserver 1.1.1.1

# Failover mode (USB)
nameserver <PI4_USB_IP>  # Pi 4 forwards DNS
```

## Routing and Metrics

### Pi 4 Interface Priorities
| Interface | Metric | Priority |
|-----------|--------|----------|
| `eth0` | 50 | Highest (when connected) |
| `wlan0` | 100 | Medium |
| `usb0` | 150 | Lowest |

### Pi Zero Interface Priorities
| Interface | Metric | Priority |
|-----------|--------|----------|
| `wlan0` | 100 | Highest |
| `usb0` | 200 | Fallback only |

## Port Configuration

### Pi 4 Services
| Service | Port | Access | Purpose |
|---------|------|--------|---------|
| SSH | 22 | LAN, Tailscale | Remote shell |
| MediaMTX RTSP | 8554 | Local only | Camera streams |
| MediaMTX WebRTC | 8889 | LAN, Tailscale | Browser viewing |
| Restreamer | 8080 | LAN, Tailscale | Stream management |
| Netdata | 19999 | LAN, Tailscale | System monitoring |

### Pi Zero Services
| Service | Port | Access | Purpose |
|---------|------|--------|---------|
| SSH | 22 | USB, WiFi, Tailscale | Remote shell |
| Camera stream | N/A | USB forwarding | Via Pi 4 MediaMTX |

### Firewall Rules

**Pi 4**: Docker manages most firewall rules. Additional rules for USB traffic:
```bash
# Allow USB traffic through Docker firewall
iptables -I DOCKER-USER -i usb0 -j ACCEPT
iptables -I DOCKER-USER -o usb0 -j ACCEPT
```

**Pi Zero**: Default UFW rules, SSH allowed.

## NAS Integration

### Network Mount
- **Path**: `/mnt/nas`
- **Protocol**: CIFS/SMB
- **Server**: `<NAS_IP>`
- **Share**: `<NAS_SHARE>`
- **Credentials**: Stored in `/etc/cifs-credentials`

### Mount Command
```bash
sudo mount -t cifs //<NAS_IP>/<NAS_SHARE> /mnt/nas \
  -o credentials=/etc/cifs-credentials,uid=1000,gid=1000
```

## Failover Behavior

### USB Failover
1. **Detection**: Each Pi pings `1.1.1.1` every 30 seconds via WiFi
2. **Trigger**: If WiFi ping fails, check USB peer connectivity
3. **Action**: Add route via USB peer, enable NAT on peer
4. **Recovery**: When WiFi returns, remove failover route

### Manual Failover Testing
```bash
# Simulate WiFi failure
sudo ip link set wlan0 down

# Check failover activation
sudo usb-failover.sh --status

# Test internet via failover
ping -I usb0 8.8.8.8

# Restore WiFi
sudo nmcli device connect wlan0
```

## Troubleshooting Network Issues

### Connectivity Tests

**Pi 4**:
```bash
# Test interfaces
ping -I wlan0 8.8.8.8
ping -I eth0 8.8.8.8
ping -I usb0 <ZERO_USB_IP>

# Check routes
ip route show
```

**Pi Zero**:
```bash
# Test connectivity
ping -I wlan0 8.8.8.8
ping -I usb0 <PI4_USB_IP>

# Check USB gadget
cat /sys/class/net/usb0/address
```

### Common Issues

**WiFi not connecting**:
- Check network name and password
- For 2.4 GHz: may need router firmware update
- Check signal strength: `iwconfig wlan0`

**USB Gadget not working**:
- Verify cable in correct Pi Zero port (USB, not PWR)
- Check `g_ether` module: `lsmod | grep g_ether`
- Restart USB services: `sudo systemctl restart usb-*`

**Tailscale connection problems**:
- Check service: `sudo systemctl status tailscaled`
- Re-authenticate: `sudo tailscale up`
- Check network ACLs in Tailscale admin

### Emergency Access

If all network access fails:
1. **Physical access**: Direct keyboard/monitor to Pi 4
2. **UART recovery**: 3-wire serial connection between Pis
3. **USB direct**: Connect Pi directly to computer

See [UART Recovery](../setup/uart-recovery.md) for serial access details.

## Security Considerations

### SSH Access
- Key-based authentication preferred
- Password authentication only on local networks
- Tailscale provides encrypted transport

### Network Isolation
- Camera streams not exposed to internet
- Management interfaces only on trusted networks
- Regular security updates via `unattended-upgrades`

### VPN Security
- Tailscale uses WireGuard protocol
- Device certificates managed centrally
- Network ACLs control access between devices

## Performance Optimization

### Network Tuning
- Large TCP windows for video streaming
- MTU optimization for USB Gadget
- QoS prioritization for camera streams

### Bandwidth Usage
| Service | Bandwidth | Direction |
|---------|-----------|-----------|
| Pi Zero → Pi 4 | ~5-10 Mbps | USB Gadget |
| Pi 4 → Twitch | ~3-6 Mbps | WiFi/LAN upload |
| Remote SSH | ~1-10 Kbps | Bidirectional |
| NAS backup | Variable | LAN only |