# USB WiFi Failover

Two Raspberry Pis connected via USB OTG (g_ether gadget) can act as WiFi backup for each other. If one Pi loses WiFi, it routes traffic through the USB link to the other Pi which still has a working connection.

## Prerequisites

- Two Pis connected via USB OTG cable
- USB Ethernet Gadget (`g_ether`) configured on the device-side Pi
- Static link-local IPs on both sides of the USB link
- SSH key access between the Pis (for enabling forwarding on the peer)

## How it works

```
Normal mode:
  Pi-A ──WiFi──► Router ──► Internet
  Pi-B ──WiFi──► Router ──► Internet
       ◄──USB──►  (idle)

Failover (Pi-A WiFi down):
  Pi-A ──USB──► Pi-B ──WiFi──► Router ──► Internet
```

Every 30 seconds (configurable), each Pi pings an external host (1.1.1.1) through its WiFi interface. If unreachable:

1. Check if USB peer is reachable
2. Ask peer to enable IP forwarding + NAT
3. Add a low-metric default route via USB peer
4. Traffic now flows through peer's WiFi

When local WiFi recovers, the failover route is removed automatically.

## Setup

### 1. USB Gadget Network (device-side Pi)

The Pi acting as USB gadget needs a persistent network config on `usb0`:

```bash
# Using NetworkManager (Bookworm):
sudo nmcli connection add type ethernet con-name usb-gadget \
  ifname usb0 ipv4.method manual ipv4.addresses 169.254.246.2/16 \
  ipv6.method disabled autoconnect yes

# Using dhcpcd (Bullseye) — add to /etc/dhcpcd.conf:
interface usb0
  static ip_address=169.254.246.2/16
  nogateway
```

The host-side Pi typically auto-assigns a link-local address via avahi/dhcpcd. To set a static one:

```bash
# Bullseye (dhcpcd) — add to /etc/dhcpcd.conf:
interface usb0
  static ip_address=169.254.246.156/16
  nogateway
```

### 2. Configuration

Create `/etc/usb-failover.conf` on each Pi:

**On the host Pi (e.g., Pi 4 at 169.254.246.156):**
```bash
PEER_USB_IP="169.254.246.2"
CHECK_INTERVAL=30
```

**On the gadget Pi (e.g., Pi Zero at 169.254.246.2):**
```bash
PEER_USB_IP="169.254.246.156"
CHECK_INTERVAL=30
```

### 3. SSH Keys Between Pis

The Pis should have SSH key access to each other for easy administration:

```bash
# On each Pi:
ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519

# Deploy keys (from Pi 4):
ssh-copy-id vb-light@169.254.246.2    # via USB
ssh-copy-id vb-light@<ZERO_LAN_IP>     # via LAN

# Deploy keys (from Pi Zero):
ssh-copy-id vogl@169.254.246.156      # via USB
```

### 4. Install

```bash
sudo ./scripts/usb-failover.sh --install
```

This:
- Copies the script to `/usr/local/bin/`
- Creates a systemd service that checks every 30 seconds
- Enables and starts the service (survives reboot)

### 5. Verify

```bash
sudo usb-failover.sh --status
```

Shows current state, link status, peer reachability, and routes.

### 6. Uninstall

```bash
sudo usb-failover.sh --uninstall
```

## Testing

To simulate WiFi failure:

```bash
# Disconnect WiFi temporarily
sudo ip link set wlan0 down

# Run failover check (or wait for timer)
sudo usb-failover.sh check

# Verify internet still works (via USB peer)
ping 1.1.1.1

# Restore WiFi
# NetworkManager: use nmcli (ip link set up alone won't reconnect)
sudo nmcli device connect wlan0
# dhcpcd: ip link set wlan0 up suffices

# Run check again (or wait for timer) — should recover
sudo usb-failover.sh check
```

**Important routing note:** The failover route uses `src <usb-ip>` to ensure return
packets come back through USB, not through the LAN. Without this, NAT de-translation
on the peer routes replies via LAN instead of USB, causing 100% packet loss.

If the peer Pi runs Docker, you also need FORWARD rules allowing USB traffic through
Docker's firewall (FORWARD policy is DROP with Docker). See the `rc.local` setup below.

## Docker Firewall (Pi 4 specific)

If the peer Pi runs Docker, the FORWARD chain policy is set to DROP. You need
explicit rules to allow USB traffic through:

```bash
# Add to /etc/rc.local (runs after Docker sets up its chains):
iptables -I FORWARD 1 -i usb0 -o wlan0 -j ACCEPT
iptables -I FORWARD 2 -i usb0 -o eth0 -j ACCEPT
iptables -I FORWARD 3 -i wlan0 -o usb0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -I FORWARD 4 -i eth0 -o usb0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -I DOCKER-USER -i usb0 -j ACCEPT
iptables -I DOCKER-USER -o usb0 -j ACCEPT
```

## Limitations

- **Not instant**: up to 30 seconds detection time (configurable via `CHECK_INTERVAL`)
- **SSH required**: the failover script SSHs to the peer to enable forwarding. Needs passwordless SSH (key-based) between the Pis.
- **NAT**: failover uses masquerading, so inbound connections to the failed Pi won't work during failover
- **Single point of failure**: if the router/ISP is down, neither Pi has internet regardless
- **Not a bonding solution**: only one path is active at a time, no bandwidth aggregation

## Files

| File | Purpose |
|------|---------|
| `scripts/usb-failover.sh` | Main script (check, install, uninstall, status) |
| `/etc/usb-failover.conf` | Per-machine configuration (IPs, intervals) |
| `/run/usb-failover.state` | Runtime state (normal/failover), lost on reboot |
