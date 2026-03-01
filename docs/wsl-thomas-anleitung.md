# WSL2 Setup — Anleitung für Thomas

## Schritt 1: WSL aktualisieren und systemd aktivieren

**In WSL (Ubuntu-Fenster) eingeben:**

```bash
cat /etc/wsl.conf
```

Falls die Datei leer ist oder `[boot] systemd=true` NICHT drinsteht:

```bash
echo -e '[boot]\nsystemd=true' | sudo tee /etc/wsl.conf
```

Passwort eingeben wenn gefragt (man sieht beim Tippen nichts — normal!).

---

## Schritt 2: WSL neu starten

**Ubuntu-Fenster schließen**, dann in **PowerShell** (kein Admin nötig):

```powershell
wsl --shutdown
```

3 Sekunden warten, dann WSL wieder starten:

```powershell
wsl
```

---

## Schritt 3: SSH-Server + Tailscale installieren

**Im neuen Ubuntu-Fenster — alles auf einmal kopieren und einfügen:**

```bash
sudo apt update && sudo apt install -y openssh-server && sudo systemctl enable ssh && sudo systemctl start ssh && curl -fsSL https://tailscale.com/install.sh | sh && sudo systemctl enable --now tailscaled && echo "FERTIG! Jetzt Schritt 4!"
```

---

## Schritt 4: SSH-Schlüssel einrichten

**Im Ubuntu-Fenster:**

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMSvpdAxzLP7GHjHhM3UTRXK2zupvSqVZyjblcdsf2A8 vhw@vogelhaus.local-wsl' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo "SSH-Key installiert!"
```

---

## Schritt 5: Tailscale verbinden

**Im Ubuntu-Fenster:**

```bash
sudo tailscale up
```

Es erscheint ein Link (https://login.tailscale.com/...) — **diesen Link hier in den Chat kopieren!**

Martin kümmert sich dann um den Rest.

---

## Schritt 6: NAS als Netzlaufwerk einrichten

**In Windows (nicht WSL!):**
1. **Datei-Explorer** öffnen (Windows-Taste + E)
2. Oben auf **"..."** (drei Punkte) → **"Netzlaufwerk verbinden"**
3. Laufwerksbuchstabe: **N:**
4. Ordner: `\\<NAS_IP>\Meisen_aus_Urfahr`
5. ✅ "Verbindung bei Anmeldung wiederherstellen" anhaken
6. Benutzer: `vogelhauswart`, Passwort: (das vom NAS)

Danach ist das NAS in WSL unter `/mnt/n/` erreichbar.

---

## Schritt 7: WSL Leistung optimieren (optional, kann Martin auch machen)

In **Notepad++** eine neue Datei erstellen mit diesem Inhalt:

```ini
[wsl2]
memory=24GB
processors=8
swap=0
guiApplications=true

[experimental]
autoMemoryReclaim=dropCache
sparseVhd=true
```

Speichern als: `C:\Users\tom89\.wslconfig` (WICHTIG: kein `.txt` am Ende!)

Dann in PowerShell: `wsl --shutdown` und wieder `wsl` starten.

---

## Geschafft!

Nach diesen Schritten können Martin und der Vogelhauswart per SSH auf dein WSL zugreifen (nur wenn du WSL gestartet hast!) und dort die restliche Software installieren — ffmpeg, Python, Videoanalyse-Tools etc.

Du musst dafür nichts mehr tun. 🎉
