# 🐦 Pi Zero W — Flash-Anleitung (Schritt für Schritt)

**Zuletzt aktualisiert:** 21. Februar 2026  
**Zweck:** Pi Zero W komplett neu aufsetzen  
**Durchführung:** Thomas (vor Ort) + Vogelhauswart (remote, Schritt für Schritt)

---

## Übersicht

| Was | Details |
|-----|---------|
| Gerät | Raspberry Pi Zero W v1.1 |
| OS | Raspberry Pi OS Legacy Lite (Bookworm, 32-bit) |
| Hostname | `voglberry-light` |
| User | `vb-light` |
| Passwort | `1234` (temporär, wird nachher geändert) |
| WLAN | `<YOUR_WIFI_SSID>` (2.4 GHz) |
| USB Gadget | `dwc2` + `libcomposite` (feste MAC-Adresse) |

---

## Voraussetzungen

- [ ] Pi 4 (voglberry) läuft und ist per LAN-Kabel am Router
- [ ] Pi Zero W ist vom Pi 4 abgesteckt
- [ ] SD-Karte (32 GB) aus dem Pi Zero entnommen
- [ ] Cardreader am Windows-PC angesteckt
- [ ] Raspberry Pi Imager installiert (https://www.raspberrypi.com/software/)

---

## Phase 1: SD-Karte flashen (Thomas am PC)

### Schritt 1: Raspberry Pi Imager starten

Programm öffnen. Du siehst drei große Buttons.

### Schritt 2: Gerät auswählen

- Klick auf **"Gerät auswählen"**
- Wähle: **Raspberry Pi Zero** (⚠️ NICHT "Zero 2 W"! Im Imager heißt es nur "Zero")

### Schritt 3: Betriebssystem auswählen

- Klick auf **"Betriebssystem auswählen"**
- Wähle: **Raspberry Pi OS (other)**
- Dann: **Raspberry Pi OS (Legacy, 32-bit) Lite**

⚠️ **WICHTIG:**
- Es MUSS "Legacy" sein (nicht das normale Raspberry Pi OS)
- Es MUSS "Lite" sein (ohne Desktop)
- Es MUSS "32-bit" sein

### Schritt 4: SD-Karte auswählen

- Klick auf **"SD-Karte auswählen"**
- Wähle deine 32 GB SD-Karte
- Falls nichts erscheint: Cardreader rausstecken und nochmal reinstecken

> ⚠️ **Cardreader-Bug:** Funktioniert manchmal nur einmal nach dem Windows-Start.
> Falls er streikt: Windows komplett neu starten, dann sofort alles in einem Durchgang machen.

### Schritt 5: Einstellungen öffnen

- Klick auf **"Weiter"**
- Es erscheint: "OS-Anpassung verwenden?"
- Klick auf **"Einstellungen bearbeiten"**

### Schritt 6: Allgemeine Einstellungen

Im Tab **"ALLGEMEIN"**:

| Einstellung | Wert |
|------------|------|
| ☑ Hostname setzen | `voglberry-light` |
| ☑ Benutzername und Passwort setzen | |
| → Benutzername | `vb-light` |
| → Passwort | `1234` |
| ☑ WLAN konfigurieren | |
| → SSID | `<YOUR_WIFI_SSID>` |
| → Passwort | *[hier dein WLAN-Passwort eintippen]* |
| → WLAN-Land | `AT` |
| ☑ Gebietsschema festlegen | |
| → Zeitzone | `Europe/Vienna` |
| → Tastaturlayout | `de` |

### Schritt 7: Dienste-Einstellungen

Im Tab **"DIENSTE"**:

| Einstellung | Wert |
|------------|------|
| ☑ SSH aktivieren | |
| → Passwort zur Authentifizierung verwenden | ☑ (ankreuzen!) |

### Schritt 8: Speichern und Flashen

1. Klick auf **"Speichern"**
2. Klick auf **"Ja"** bei "OS-Anpassung verwenden?"
3. Klick auf **"Ja"** bei "Alle Daten werden gelöscht"
4. **Warten** — dauert ca. 5 Minuten
5. Wenn fertig: **NOCH NICHT auswerfen!** → Weiter zu Phase 2

---

## Phase 2: USB Gadget vorbereiten (Thomas am PC)

Nach dem Flash hat die SD-Karte eine Partition namens **"bootfs"** die Windows lesen kann.

### Schritt 9: config.txt bearbeiten

1. Öffne den **Windows Explorer**
2. Gehe zum Laufwerk **"bootfs"**
3. Rechtsklick auf **`config.txt`** → **"Öffnen mit"** → **Notepad** (Editor)
4. Scrolle ganz nach **unten**
5. Füge als **letzte Zeile** hinzu:

```
dtoverlay=dwc2
```

6. **Speichern** (Strg+S) und schließen

### Schritt 10: cmdline.txt bearbeiten

⚠️ **GANZ WICHTIG:** Diese Datei hat nur **EINE EINZIGE ZEILE!** Nicht umbrechen!

1. Rechtsklick auf **`cmdline.txt`** → **"Öffnen mit"** → **Notepad**
2. Du siehst eine lange Zeile. Suche das Wort `rootwait`
3. **Direkt NACH** `rootwait` ein Leerzeichen und dann einfügen:

```
modules-load=dwc2,g_ether
```

4. Das Ergebnis sieht ungefähr so aus:

**Vorher:**
```
... rootwait quiet ...
```

**Nachher:**
```
... rootwait modules-load=dwc2,g_ether quiet ...
```

5. Prüfe: **Alles muss in EINER Zeile stehen!**

> ⚠️ **WICHTIG:** `g_ether` MUSS dabei sein! Ohne g_ether gibt es beim ersten Boot kein USB-Netzwerk und man kommt nicht per SSH drauf. Später wird g_ether durch libcomposite ersetzt (für stabile MAC-Adressen).
6. **Speichern** (Strg+S) und schließen

### Schritt 11: SD-Karte auswerfen

1. Rechtsklick auf das Laufwerk "bootfs" im Explorer
2. **"Auswerfen"** klicken
3. Warten bis Windows sagt "kann sicher entfernt werden"
4. Cardreader rausstecken
5. SD-Karte aus dem Cardreader nehmen

---

## Phase 3: Pi Zero starten (Thomas am Vogelhaus)

### Schritt 12: SD-Karte einsetzen

1. SD-Karte in den Pi Zero stecken
   - Kontakte nach oben (zum Board hin)
   - Sanft reinschieben bis es klickt

### Schritt 13: Pi Zero anschließen

1. Nimm das **Datenkabel** (XLAYER Premium 2m, USB-A → Micro-USB)
2. Stecke das **Micro-USB-Ende** in den Pi Zero
   - ⚠️ In den **mittleren** USB-Port! (beschriftet mit "USB", NICHT "PWR")
3. Stecke das **USB-A-Ende** in den Pi 4

Der Pi Zero bootet jetzt automatisch (er bekommt Strom über USB vom Pi 4).

### Schritt 14: Warten und kontrollieren

- **Grüne LED** am Pi Zero sollte **blinken** (= er bootet)
- Erster Boot dauert **1-2 Minuten** (SD-Karte wird eingerichtet)
- Wenn die LED nach 2 Minuten aufhört wild zu blinken → bereit

### Schritt 15: Melden

Nachricht an den VHW (Vogelhaus-Chat):

> "Pi Zero ist geflasht, SD-Karte drin, hängt am Pi 4. LED hat geblinkt."

---

## Phase 4: Fernkonfiguration (Vogelhauswart per SSH)

*Ab hier übernimmt der VHW remote. Thomas muss nichts mehr tun (außer bei Problemen).*

### Was der VHW macht:

1. **SSH-Zugang testen** (via WiFi ProxyJump über Pi 4)
2. **USB Gadget einrichten** (libcomposite mit fester MAC-Adresse)
   - Pi Zero MAC: `02:22:33:44:55:66`
   - Pi 4 MAC: `02:22:33:44:55:67`
3. **USB-Netzwerk konfigurieren** (statische IPs)
   - Pi Zero: `169.254.246.2`
   - Pi 4: `169.254.246.156`
4. **USB Failover installieren** (gegenseitiges WLAN-Sharing)
5. **SSH-Keys tauschen** (Pi 4 ↔ Pi Zero)
6. **Tailscale installieren** (Fernzugang)
7. **Kamera testen** (`rpicam-still`)
8. **Reboot-Test** (prüfen ob alles überlebt)

### VHW-Checkliste nach Setup:

- [ ] SSH via WiFi funktioniert
- [ ] SSH via USB Gadget funktioniert (169.254.246.2)
- [ ] USB Gadget MAC ist fest (02:22:33:44:55:66)
- [ ] USB Failover aktiv auf beiden Pis
- [ ] Tailscale verbunden
- [ ] Kamera macht Fotos
- [ ] Reboot-Test bestanden (IPs und MACs gleich wie vorher)
- [ ] Temporäres Passwort `1234` geändert

---

## Fehlerbehebung

### "LED blinkt gar nicht"
- SD-Karte richtig drin? (Klick beim Einstecken?)
- USB-Kabel im richtigen Port? (USB, nicht PWR!)
- Anderes USB-Kabel probieren (muss Datenkabel sein, nicht nur Ladekabel)

### "VHW kommt nicht per SSH drauf"
- Warten! Erster Boot braucht bis zu 2 Minuten
- WLAN-Passwort korrekt eingegeben?
- Pi Zero nochmal abstecken, 10 Sekunden warten, wieder anstecken

### "Cardreader zeigt nichts an"
- Windows neu starten
- Cardreader sofort nach Boot verwenden (Bug: funktioniert nur einmal)
- Alles in EINEM Durchgang machen!

### "Imager zeigt kein Legacy OS"
- Raspberry Pi Imager aktualisieren (neueste Version von der Website)
- Unter "Raspberry Pi OS (other)" schauen

---

## Technische Details (für Martin/VHW)

### Flash-Settings Zusammenfassung
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

### USB Gadget Architektur (nach Post-Flash-Setup)
```
Pi Zero W (voglberry-light)              Pi 4 (voglberry)
┌──────────────────────┐                ┌──────────────────────┐
│ usb-gadget.service   │                │                      │
│ (libcomposite)       │                │                      │
│                      │    USB OTG     │                      │
│ usb0: 169.254.246.2  │◄──────────────►│ usb0: 169.254.246.156│
│ MAC: 02:22:33:44:55:66                │ MAC: 02:22:33:44:55:67
│                      │                │                      │
│ wlan0: DHCP          │                │ wlan0: <PI4_WLAN_IP>   │
│ (Pyramidenverleih    │                │ (Happy Wifi, 5GHz)   │
│  Ramses, 2.4GHz)     │                │ eth0: <PI4_LAN_IP>   │
│                      │                │ (LAN-Kabel)          │
│ usb-failover.sh ◄────────────────────►│ usb-failover.sh      │
│ (teilt Pi4 WiFi/LAN) │                │ (teilt Zero WiFi)    │
└──────────────────────┘                └──────────────────────┘
```

### Dateien im Repo
- `docs/pi-zero-flash-guide.md` — Diese Anleitung
- `docs/usb-failover.md` — USB Failover Dokumentation
- `scripts/usb-failover.sh` — Failover-Skript

---

🐦 *K.u.K. Vogelhaus-Amt — Technische Dokumentation*
