# 🪪 Hamburg PersoBot

Hamburg PersoBot ist ein Open-Source-Discord-Bot, geschrieben in **Python** mit der Bibliothek **discord.py**.  
Er ermöglicht es, digitale Ausweise zu erstellen, anzusehen, zu löschen und zu verwalten.  
Ein integriertes Annahmesystem erlaubt es Moderatoren, Ausweise zu prüfen und zu genehmigen.  
Alle Aktionen werden automatisch protokolliert.

---

## 🚀 Funktionen

### 🔹 Ausweise
- **Ausweis erstellen:**  
  Benutzer können offizielle oder gefälschte Ausweise erstellen.  
  Der Bot führt sie dabei Schritt für Schritt durch den Vorgang mit einem interaktiven Modal-Formular.
  
- **Ausweis ansehen:**  
  Benutzer können ihren eigenen oder den eines anderen Nutzers einsehen.  
  Bei fremden Ausweisen wird eine Freigabeanfrage an den Besitzer gesendet.

- **Ausweis löschen:**  
  Benutzer können ihre eigenen Ausweise über ein Dropdown-Menü löschen.  
  Administratoren haben erweiterte Löschrechte.

---

### 🔹 Annahmesystem
- Jeder erstellte Ausweis muss von einem Moderator im Annahme-Kanal überprüft werden.  
- Der Moderator kann den Ausweis:
  - ✅ **Annehmen** – er wird in die Datenbank eingetragen und der Benutzer erhält eine DM-Bestätigung.  
  - ❌ **Ablehnen** – er wird mit Begründung gelöscht und der Benutzer wird informiert.
- Gefälschte Ausweise werden mit 🚨 gekennzeichnet und haben eine orange Farbe.

---

### 🔹 Lock-System
- Benutzer können für eine bestimmte Zeit gesperrt werden (Lock).
- Gesperrte Benutzer können keine neuen Ausweise erstellen.
- Locks werden in `locks.json` gespeichert und beim Bot-Start automatisch geladen.

---

### 🔹 Datenbank
- Alle angenommenen Ausweise werden sicher in einer JSON-Datenbank gespeichert (`PersonenDB`).  
- Jeder Ausweis erhält eine eindeutige UUID zur Identifikation.
- Benutzer können maximal **2 Ausweise gleichzeitig** haben.
- Export oder Löschung sind nur durch Administratoren möglich.

---

### 🔹 Logging
- Alle wichtigen Aktionen werden automatisch protokolliert.
- Logs werden im konfigurierten Log-Ordner gespeichert (siehe `variables.ini`).
- Zusätzlich werden wichtige Events über einen Webhook geloggt.

---

### 🔹 Befehle

#### Slash Commands (/)
| Befehl | Beschreibung | Channel-Beschränkung |
|---------|---------------|---------------------|
| `/ausweis-erstellen` | Erstellt einen neuen Ausweis (offiziell oder gefälscht) | `#ausweis-erstellen` |
| `/ausweis-ansehen` | Zeigt den Ausweis eines Benutzers an | `#ausweis-ansehen` |
| `/ausweis-löschen` | Löscht einen eigenen Ausweis | `#ausweis-erstellen` |
| `/report` | Sendet einen Bugreport an das Dev-Team | Überall |

#### Prefix Commands ($)
| Befehl | Beschreibung | Berechtigung |
|---------|---------------|--------------|
| `$userdata id=<ID>` | Zeigt alle Ausweise eines Benutzers | Admin |
| `$dellperso uuid=<UUID> id=<ID>` | Löscht einen spezifischen Ausweis | Admin |
| `$stop` | Stoppt den Bot (mit Bestätigung) | Admin |
| `$get-channel guild=<ID> id=<ID>` | Exportiert Embeds aus einem Channel | Admin |

---

## ⚙️ Installation & Setup

### 1. Repository herunterladen
Lade das Repository als ZIP herunter oder klone es:
```bash
git clone https://github.com/deinusername/hamburg-persobot.git
cd hamburg-persobot
```

### 2. Dependencies installieren
Installiere alle benötigten Python-Pakete:
```bash
pip install discord.py aiohttp requests
```

**Benötigte Pakete:**
- `discord.py` - Discord Bot Library
- `aiohttp` - Asynchrone HTTP-Anfragen
- `requests` - HTTP-Anfragen für Webhooks

### 3. Konfiguration anpassen

#### **Bot Token einfügen:**
In der letzten Zeile von `main.py` deinen Discord Bot Token eintragen:
```python
bot.run("DEIN_BOT_TOKEN_HIER")
```

#### **Channel IDs in `variables.ini` anpassen:**
```ini
[DISCORD]
GUILD = DEINE_GUILD_ID
CREATION = DEINE_ERSTELLUNGS_CHANNEL_ID
SHOW = DEINE_ANZEIGE_CHANNEL_ID
```

#### **Webhook URLs anpassen (optional):**
- **Zeile 207:** Log-Webhook für Admin-Aktionen
- **Zeile 675:** IFTTT-Webhook für Bugreports

### 4. Bot starten
```bash
python main.py
```

---

## 🔧 Discord IDs finden

### Channel-IDs finden:
1. Discord Developer Mode aktivieren (Einstellungen → Erweitert → Entwicklermodus)
2. Rechtsklick auf Channel → "ID kopieren"

### User-IDs finden:
1. Rechtsklick auf Benutzer → "ID kopieren"

### Webhook erstellen:
1. Channel-Einstellungen → Integrationen → Webhooks → Neuer Webhook
2. URL kopieren und im Code einfügen

---

## 🧠 Technologien
- **Python 3.10+**
- **discord.py 2.0+**
- JSON-basierte Datenbank (PersonenDB)
- INI-basierte Konfiguration
- Logging-System mit Datei- und Webhook-Logs
- Async/Await für performante API-Calls

---

## 📋 Features im Detail

### Dokumenttypen
- **Normaler Ausweis (O):** Offizieller Personalausweis für reguläres RP
- **Gefälschter Ausweis (G):** Für spezielle RP-Szenarien, optisch gekennzeichnet

### Sicherheit
- Channel-basierte Zugriffskontrolle
- Benutzer-ID-basierte Admin-Befehle
- UUID-System zur eindeutigen Identifikation
- Lock-System gegen Spam
- Freigabesystem für fremde Ausweise

### User Experience
- Interaktive Modals für Dateneingabe
- Dropdown-Menüs für Auswahl
- Embed-basierte Darstellung
- Ephemeral Messages für Privatsphäre
- DM-Benachrichtigungen über Status

---

## ⚠️ Nutzungsbedingungen

- Der gesamte Code und dieses Repository bleiben **Eigentum von Hamburg PersoBot Development**.  
- Es ist **nicht gestattet**, den Code oder Teile davon auf deinem **eigenen GitHub-Profil** oder auf anderen Plattformen zu veröffentlichen.  
- Du darfst **keine Änderungen am Code oder an der Struktur** des Projekts vornehmen.  
- Forks zu Lernzwecken sind erlaubt, dürfen aber **nicht öffentlich** oder **kommerziell genutzt** werden.

---

## 📞 Support & Kontakt

Bei Fragen, Bugs oder Feature-Requests nutze den `/report`-Befehl im Bot oder öffne ein Issue auf GitHub.

---

## 📝 Lizenz

Dieses Projekt ist urheberrechtlich geschützt.  
Alle Rechte vorbehalten © Hamburg PersoBot Development
