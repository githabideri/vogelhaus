# USB-Gadget Internet-Sharing: Pi Zero ↔ Pi 4

## Überblick

Der Pi Zero bekommt Internet über eine USB-Gadget-Verbindung (CDC Ethernet) durch den Pi 4.
Der Pi 4 fungiert als NAT-Gateway und leitet den Traffic des Zero über sein LAN-Interface weiter.

## Voraussetzungen

### Pi Zero
- `modules-load=dwc2,g_ether` in `cmdline.txt`
- USB-Datenkabel am **mittleren** Micro-USB-Port (DATA, nicht PWR)

### Pi 4
- `uhubctl` installiert (`apt install uhubctl`)
- VL805 Firmware ≥ `00137ad` (prüfen: `sudo rpi-eeprom-update`)
- IP-Forwarding aktiviert (`net.ipv4.ip_forward=1`)

## Netzwerk-Konfiguration

| Gerät | Interface | IP | Rolle |
|---|---|---|---|
| Pi 4 | usb0 | 10.42.0.1/24 | Gateway |
| Pi Zero | usb0 | 10.42.0.2/24 | Client |

DNS auf dem Zero: `nameserver 1.1.1.1`

## Systemd-Services

### Pi 4

**`usb-zero-powercycle.service`** — Läuft beim Boot, cycelt den USB2-Hub (VIA, 1-1) um dem Zero einen sauberen Start zu geben.

- Skript: `/usr/local/bin/usb-zero-powercycle.sh`
- Schaltet Hub 1-1 ab (5s), wartet 90s auf Zero-Boot
- SSD (Hub 2, USB3) bleibt unberührt
- Fallback: einzelner Data-Port-Recycle falls usb0 nach 90s fehlt

**`usb-internet-sharing.service`** — Konfiguriert IP + NAT auf usb0 nachdem der Zero erkannt wurde.

- Skript: `/usr/local/bin/usb-internet-sharing.sh`
- Wartet bis zu 60s auf usb0
- Setzt IP 10.42.0.1/24, aktiviert Forwarding + iptables MASQUERADE über eth0

### Pi Zero

**`usb-network.service`** — Konfiguriert die Zero-Seite der USB-Verbindung.

- Skript: `/usr/local/bin/usb-network.sh`
- Wartet auf usb0, setzt IP 10.42.0.2/24, Default-Route über Pi 4, DNS

## USB-Hub-Topologie (Pi 4)

```
Hub 2 (USB 3.0, per-port power switching)
  └─ Port 1: SSD (JMicron SATA) ← NICHT vom Powercycle betroffen!

Hub 1-1 (USB 2.0 VIA, per-port power switching)
  ├─ Port 1: (leer oder PWR-only)
  ├─ Port 2: Pi Zero USB-Gadget (Datenkabel)
  ├─ Port 3: Audio Codec
  └─ Port 4: (leer oder PWR-only)
```

## Kabel

- **K1** (2m XLAYER Premium, USB-A → Micro-USB, mit Klettverschluss): Getestet und funktioniert ✅
- Das Datenkabel muss am **mittleren** Micro-USB-Port des Zero stecken
- Das Stromkabel (PWR) bleibt am **äußeren** Port

## Fehlerbehebung

### usb0 erscheint nicht am Pi 4
1. Prüfen ob Zero läuft: `sudo uhubctl` — Gadget sollte auf Hub 1-1 Port 2 sichtbar sein
2. Port manuell recyclen: `sudo uhubctl -l 1-1 -p 2 -a 2`
3. Service neu starten: `sudo systemctl restart usb-internet-sharing.service`

### Zero hat kein Internet
1. Pi 4: `ip addr show usb0` — IP 10.42.0.1/24 vorhanden?
2. Pi 4: `sysctl net.ipv4.ip_forward` — muss 1 sein
3. Pi 4: `sudo iptables -t nat -L POSTROUTING` — MASQUERADE-Regel vorhanden?
4. Zero: `ip route` — Default-Route via 10.42.0.1?
5. Zero: `cat /etc/resolv.conf` — `nameserver 1.1.1.1`?

### Zero bootet nicht nach Pi4-Reboot
- **Nie `shutdown -h now` am Zero verwenden** wenn er über Pi4-USB Strom bekommt!
- Immer `sudo reboot` verwenden
- Der `usb-zero-powercycle.service` sorgt beim Pi4-Boot für einen sauberen USB-Powercycle
