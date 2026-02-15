# OV5647 NoIR Camera Module — Research Report

**Date:** 2026-02-15
**Context:** Vogelhaus-Projekt, Fraktalia

---

## 1. Product Identification

**Module:** Kuman SC15 (or identical clone)
- Common brands: Kuman, DORHEA, SUKRAGRAHA, AZDelivery, generic AliExpress
- All feature: OV5647 sensor, two cylindrical 850nm IR LEDs with heatsinks, LDR sensor, adjustable potentiometer

**Our specific unit:**
- One heatsink missing on left IR LED
- Handwritten label "IR 5MP" on sensor
- Connected via Flex-Kabel to Pi Zero W V1.1

## 2. Technical Specifications

| Parameter | Value |
|-----------|-------|
| Sensor | OmniVision OV5647, 5MP |
| Resolution | Up to 2592x1944 (15fps), 1080p (30fps), 1296x972 (46fps) |
| FOV | 72.4° |
| IR LEDs | 2x 850nm, ~3W each |
| LED Current | ~909mA @ 3.3V per LED |
| Total LED Draw | ~1.8A from 3.3V rail |
| LDR | Automatic threshold switching, adjustable via potentiometer |
| Effective IR Range | 1-3 meters optimal |
| I2C Address | 0x36 |
| Interface | CSI (Flex-Kabel) |

## 3. ⚠️ CRITICAL: Power Warning

**Die zwei 3W IR-LEDs ziehen zusammen ~1.8A von der 3.3V-Leitung!**

Der Raspberry Pi Zero kann nur 1.0-1.5A auf dem 3.3V-Rail liefern (inkl. SoC-Eigenverbrauch). Das bedeutet:

- **Brownouts/Freezes** wenn beide LEDs aktiv sind
- **Instabiler Betrieb**, besonders unter Last (Kamera + WLAN + LEDs)
- **Überlastung des Spannungsreglers** → verkürzte Lebensdauer

### Lösungen (nach Empfehlung sortiert):

1. **Nur EINE LED betreiben** — reicht für Vogelhaus-Innenraum (15-20cm Abstand)
2. **Externe Stromversorgung** — 5V→3.3V Buck-Converter für die LEDs, getrennt vom Pi
3. **GPIO-Steuerung mit externem Netzteil** — Transistor-Schaltung, LEDs nur bei Bedarf

## 4. Board-Layout & Pinout

```
[LED1 + Heatsink] --- [OV5647 Linse] --- [LED2 + Heatsink]
                       [LDR]  [Poti]

Rückseite:
[Kühlrippen/Gold] --- [Sensor-Chip + Label] --- [Kühlrippen]
                      [Flex-Kabel-Anschluss]
```

**Stromversorgung der LEDs:**
- Loch/Pad nahe LDR: +3.3V
- Loch/Pad nahe Poti: GND
- LDR schaltet die LEDs über einen Transistor auf dem Board

**Poti:** Regelt die Lichtschwelle ab der die LEDs einschalten (im Uhrzeigersinn = empfindlicher)

## 5. IR-LED Thermal-Analyse

### Beobachtung
Die LED ohne Kühlrippe leuchtet deutlich heller und sichtbarer rot als die mit Kühlrippe.

### Erklärung
- **Wellenlängen-Drift:** ~0.1-0.3 nm/°C → bei 30°C Differenz: 855-860nm (wandert WEITER ins IR, nicht ins Sichtbare)
- **Hauptursache: Stromerhöhung** — ohne Kühlung sinkt der Vorwärtsspannungsabfall → bei gleicher Spannung fließt MEHR Strom → LED leuchtet heller
- Eine hellere 850nm-LED hat auch ein stärkeres sichtbares "Tail" im roten Spektrum
- **Thermal Runaway Risiko:** heißer → mehr Strom → noch heißer → LED-Tod

### Empfehlung
- Fehlende Kühlrippe ersetzen (Alu-Plättchen + Wärmeleitkleber)
- ODER diese LED abklemmen (eine reicht)
- Nicht dauerhaft ohne Kühlung betreiben

## 6. Wildlife Camera Best Practices

Aus erfolgreichen Vogelhaus-Projekten mit diesem Modul:

- **Abstand:** NoIR-Cam 15-30cm vom Motiv positionieren
- **Beleuchtung:** Eine IR-LED reicht für kleine Räume (Meisennistkasten)
- **Kühlung:** Kühlrippen NICHT entfernen, Ventilation im Gehäuse vorsehen
- **LDR-Schwelle:** Poti so einstellen dass LEDs erst bei echter Dunkelheit angehen
- **Lila-Stich:** Normal bei Tageslicht (NoIR = kein IR-Filter = Farbverfälschung)
- **Strom:** Separate Stromversorgung für LEDs empfohlen
- **Vögel:** 850nm IR ist für Meisen/Singvögel unsichtbar, minimales rotes Glimmen stört nicht

## 7. GPIO-Steuerung (falls gewünscht)

### Schaltung
```
Pi GPIO Pin ──[1kΩ]──┤ Base
                      │
                   2N2222 (NPN)
                      │
              LED(+)──┤ Collector
                      │
                GND ──┤ Emitter

3.3V (extern!) ──── LED(-)
```

### Software
```bash
# LED einschalten
echo "18" > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio18/direction
echo "1" > /sys/class/gpio/gpio18/value

# LED ausschalten
echo "0" > /sys/class/gpio/gpio18/value
```

### Voraussetzung
- LDR-Schaltung auf dem Board umgehen (Leiterbahn kappen)
- Externe 3.3V Versorgung für LEDs
- Transistor, 1kΩ Widerstand, Kabel

### Referenzen
- RPi Forum GPIO IR-LED Control: https://forums.raspberrypi.com/viewtopic.php?t=225060
- Pi Zero Night Camera Tutorial: https://sgvandijk.medium.com/the-electronics-and-electromagnetism-pertaining-to-a-baby-monitor-42b38bc4de1c

## 8. Bekannte Probleme

| Problem | Ursache | Lösung |
|---------|---------|--------|
| Pi friert ein bei Dunkelheit | Beide LEDs überlasten 3.3V Rail | Nur 1 LED oder externe Stromversorgung |
| Lila-Stich bei Tageslicht | NoIR hat keinen IR-Filter | Normal, nicht behebbar ohne Hardware-Mod |
| LED leuchtet sichtbar rot | 850nm, nicht 940nm | Normal, für Vögel kein Problem |
| Bild zu dunkel nachts | LEDs zu schwach oder zu weit weg | Abstand reduzieren (<1m), Reflektor verwenden |
| Überhitzung | Kühlrippe fehlt/schlecht | Ersetzen, nur 1 LED nutzen |

---

*Report erstellt von Mox Chaos, basierend auf Recherche vom 2026-02-15*
