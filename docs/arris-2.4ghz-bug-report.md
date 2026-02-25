# ARRIS TG3442 — 2.4 GHz ASSOC-REJECT Bug Report

## Zusammenfassung
Nach einem Werksreset des ARRIS TG3442 (Firmware 9.1.103GY, HW v4) lehnt das 2.4 GHz WLAN alle Verbindungsversuche eines Raspberry Pi 4 (BCM43455 WLAN-Chip) mit IEEE 802.11 Status Code 16 ab. Das 5 GHz WLAN des selben Routers funktioniert mit demselben Client und demselben Passwort einwandfrei.

## Geräte
- **Router:** ARRIS TG3442DE, Firmware 9.1.103GY, Hardware v4, ISP: Liwest
- **Client:** Raspberry Pi 4 Model B, WLAN-Chip Broadcom BCM43455 (brcmfmac), Raspberry Pi OS Bookworm (Kernel 6.1.21-v8+), wpa_supplicant v2.9

## Reproduktion

### Ausgangssituation
- Router auf Werkseinstellungen zurückgesetzt
- 2.4 GHz WLAN konfiguriert: SSID „<YOUR_WIFI_2G_SSID>", WPA2-PSK (AES), Kanal 6
- 5 GHz WLAN konfiguriert: SSID „<YOUR_WIFI_5G_SSID>", WPA2-PSK (AES), selbes Passwort
- Client (Raspberry Pi 4) per LAN verbunden, WLAN-Konfiguration via wpa_supplicant

### Schritte
1. wpa_supplicant.conf mit korrekter SSID + PSK konfiguriert
2. `sudo systemctl restart wpa_supplicant`
3. Client versucht Assoziation mit 2.4 GHz BSSID (2c:99:24:83:12:49, freq=2437)

### Ergebnis
```
wlan0: Trying to associate with 2c:99:24:83:12:49 (SSID='<YOUR_WIFI_2G_SSID>' freq=2437 MHz)
wlan0: CTRL-EVENT-ASSOC-REJECT bssid=2c:99:24:83:12:4f status_code=16
```

### Erwartetes Ergebnis
Erfolgreiche Assoziation und WPA2-Handshake.

## Analyse

### Status Code 16
IEEE 802.11 Status Code 16 = „Association denied because AP is unable to handle additional associated STAs" — der AP behauptet, keine weiteren Clients aufnehmen zu können. Nach einem Werksreset mit nur einem verbundenen Client (Smartphone) ist dies nicht plausibel.

### BSSID-Anomalie
Der Client sendet den Assoziationsversuch an die **2.4 GHz BSSID** (2c:99:24:83:12:49), aber die Ablehnung kommt von der **5 GHz BSSID** (2c:99:24:83:12:4f). Dies deutet auf ein internes Routing-Problem in der Firmware hin, möglicherweise durch Band-Steering-Logik die auch bei getrennten SSIDs aktiv ist.

### Ausschlussdiagnose

| Test | Ergebnis |
|------|----------|
| 5 GHz WLAN mit selber PSK | ✅ Sofort verbunden (COMPLETED, IP erhalten) |
| 2.4 GHz nach Router-Neustart | ❌ Status Code 16 |
| 2.4 GHz mit expliziter BSSID + freq_list | ❌ Status Code 16 |
| 2.4 GHz mit p2p_disabled=1 | ❌ Status Code 16 |
| 2.4 GHz mit proto=RSN pairwise=CCMP | ❌ Status Code 16 |
| 5 GHz deaktiviert, nur 2.4 GHz aktiv | ❌ Status Code 16 (BSSID-Anomalie bleibt) |
| 5 GHz deaktiviert + Router-Neustart | ❌ Status Code 16 |
| Smartphone (Android) auf 2.4 GHz | ✅ Funktioniert |
| Kanalbandbreite auf 20 MHz geändert | ❌ Status Code 16 |

### Schlussfolgerung
Das Problem ist spezifisch für die Kombination ARRIS TG3442 Firmware 9.1.103GY + Broadcom BCM43455 (brcmfmac) auf 2.4 GHz. Die Firmware scheint den Client intern auf die 5 GHz-Logik umzuleiten, die dann ablehnt — auch wenn 5 GHz deaktiviert ist.

## Router-Einstellungen (2.4 GHz zum Zeitpunkt des Tests)
- Wireless-Modus: G/N mixed
- Kanal: 6 (manuell)
- Kanalbandbreite: 20 MHz (nach Änderung von 20/40)
- Sicherheit: WPA2-PSK (AES)
- WMM: aktiviert, Energiesparmodus: aus
- WPS: deaktiviert
- AP-Isolierung: aus
- Frame-Bursting: an

## Mögliche Workarounds
- 5 GHz WLAN für den betroffenen Client verwenden (funktioniert)
- Externen USB-WLAN-Stick am Pi 4 testen (anderer Treiber/Chip)
- Firmware-Update anfragen

## Kontakt
ISP: Liwest Kabelmedien GmbH
Router-Seriennummer: 8BW2SZ788403581
