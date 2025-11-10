# 🪪 Hamburg PersoBot

Hamburg PersoBot ist ein Open-Source-Discord-Bot, geschrieben in **Python** mit der Bibliothek **discord.py**.  
Er ermöglicht es, digitale Ausweise zu erstellen, anzusehen, zu löschen und zu verwalten.  
Ein integriertes Annahmesystem erlaubt es Moderatoren, Ausweise zu prüfen und zu genehmigen.  
Alle Aktionen werden automatisch im Log-Ordner gespeichert.

---

## 🚀 Funktionen

### 🔹 Ausweise
- **Ausweis erstellen:**  
  Benutzer können offizielle oder gefälschte Ausweise erstellen.  
  Der Bot führt sie dabei Schritt für Schritt durch den Vorgang.

- **Ausweis ansehen:**  
  Benutzer können ihren eigenen oder den eines anderen Nutzers einsehen.

- **Ausweis löschen:**  
  Benutzer oder Administratoren können Ausweise dauerhaft entfernen.

---

### 🔹 Annahmesystem
- Jeder erstellte Ausweis muss von einem Moderator im Annahme-Kanal überprüft werden.  
- Der Moderator kann den Ausweis:
  - ✅ **Annehmen** – er wird in die Datenbank eingetragen.  
  - ❌ **Ablehnen** – er wird gelöscht.

---

### 🔹 Datenbank
- Alle angenommenen Ausweise werden sicher in einer Datenbank gespeichert.  
- Nur autorisierte Personen haben Zugriff darauf.  
- Export oder Löschung sind nur durch Administratoren möglich.

---

### 🔹 Logs
- Alle Aktionen (Erstellung, Annahme, Löschung usw.) werden automatisch im **Ordner `/logs`** gespeichert.  
- Es gibt **keinen Befehl**, um Logs im Chat anzuzeigen.  

---

### 🔹 Befehle
| Befehl | Beschreibung |
|---------|---------------|
| `/ausweis erstellen` | Erstellt einen neuen Ausweis (offiziell oder gefälscht). |
| `/ausweis ansehen` | Zeigt den Ausweis eines Benutzers an. |
| `/ausweis löschen` | Löscht einen bestehenden Ausweis. |
| `/ausweis prüfen` | Öffnet das Annahmesystem für Prüfer. |

---

## ⚙️ Nutzung & Hosting
Wenn du den Bot hostest:

- Der Bot benötigt Zugriff auf die **Server-IP** und grundlegende **Statusdaten**, um Updates und Stabilität sicherzustellen.  
  *(Diese Daten werden ausschließlich zur Verbesserung und Wartung genutzt und nicht an Dritte weitergegeben.)*  
- Der Bot kann automatisch aktualisiert werden, um Kompatibilität und Sicherheit zu gewährleisten.  
- Du darfst **keine Änderungen am Code** vornehmen, da offizielle Updates regelmäßig bereitgestellt werden.

---

## ⚠️ Nutzungsbedingungen
- Der gesamte Code und dieses Repository bleiben **Eigentum von Hamburg PersoBot Development**.  
- Es ist **nicht gestattet**, den Code oder Teile davon auf deinem **eigenen GitHub-Profil** oder auf anderen Plattformen zu veröffentlichen.  
- Du darfst **keine Änderungen am Code oder an der Struktur** des Projekts vornehmen.  
- Forks zu Lernzwecken sind erlaubt, dürfen aber **nicht öffentlich** oder **kommerziell genutzt** werden.

---

## 🧠 Technologien
- **Python 3.10+**
- **discord.py**
- SQLite oder MongoDB
- Lokales Log-System (`/logs`-Ordner)

---

## 📦 Installation

### 1. Repository klonen
```bash
git clone https://github.com/deinusername/hamburg-persobot.git
cd hamburg-persobot
