# 🪪 Hamburg PersoBot

**Hamburg PersoBot** ist ein Open-Source-Discord-Bot, mit dem Benutzer digitale Ausweise erstellen, ansehen, löschen und verwalten können.  
Der Bot enthält ein System zur Prüfung und Annahme von Ausweisen sowie eine interne Datenbank zur Speicherung aller akzeptierten Ausweise.

---

## 🚀 Funktionen

### 🔹 Ausweise
- **Ausweis erstellen:**  
  Benutzer können einen **offiziellen** oder **gefälschten** Ausweis erstellen.  
  Der Bot führt den Benutzer dabei interaktiv durch den Erstellungsprozess.

- **Ausweis ansehen:**  
  Benutzer können ihren eigenen Ausweis oder den eines anderen Nutzers anzeigen lassen.

- **Ausweis löschen:**  
  Benutzer oder Admins können Ausweise aus dem System entfernen.

---

### 🔹 Annahmesystem
- Jeder erstellte Ausweis muss von einem **Annahme-Kanal** geprüft werden.  
- Ein **Prüfer** (z. B. Moderator oder Beamter) kann dort den Ausweis:
  - ✅ **Annehmen** – Der Ausweis wird in der Datenbank gespeichert.  
  - ❌ **Ablehnen** – Der Ausweis wird verworfen und gelöscht.  

---

### 🔹 Datenbank
- Alle **angenommenen Ausweise** werden sicher in einer Datenbank gespeichert.  
- Zugriff nur für autorisierte Nutzer oder Admins.  
- Datenbank kann zur Analyse oder Verwaltung exportiert werden.

---

### 🔹 Befehle
| Befehl | Beschreibung |
|---------|---------------|
| `/ausweis erstellen` | Erstellt einen neuen Ausweis (offiziell oder gefälscht). |
| `/ausweis ansehen` | Zeigt den Ausweis eines Benutzers an. |
| `/ausweis löschen` | Löscht einen bestehenden Ausweis. |
| `/ausweis prüfen` | Öffnet das Annahmesystem für Prüfer. |
| `/logs` | Zeigt System- oder Annahmelogs an. |

---

## ⚙️ Logs & Annahmekanal
- Alle Aktionen (z. B. Erstellung, Löschung, Annahme) werden im **Log-Kanal** protokolliert.  
- Ein spezieller **Annahme-Kanal** dient der Verwaltung offener Ausweise.  
  Dort können Prüfer über Buttons oder Reaktionen entscheiden, ob ein Ausweis angenommen oder abgelehnt wird.

---

## 🧠 Technologien
- Discord.js (Node.js)
- SQLite oder MongoDB (je nach Setup)
- Slash Commands
- Event Logging System

---

## 🔐 Lizenz
Dieses Projekt ist **Open Source** und steht unter der [MIT-Lizenz](LICENSE).

---

## 👥 Mitwirken
Pull Requests, Bug Reports und Feature-Vorschläge sind jederzeit willkommen!  
Erstelle einfach ein Issue oder sende einen PR auf GitHub.

---

## 💬 Beispiel
```bash
/user: /ausweis erstellen
/bot: Bitte gib deinen Namen ein:
...
/bot: Dein Ausweis wurde erstellt und wartet auf Annahme.
