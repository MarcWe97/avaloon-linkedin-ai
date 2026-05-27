# Valoon LinkedIn AI Automation – Railway Deploy Anleitung

## Overview
Dieses Script empfängt Lemlist Webhooks für LinkedIn Replies, ruft Claude mit Web-Tools auf, und loggt die Antworten für Review (2 Wochen).

---

## Phase 1: Accounts erstellen (5 Min)

### 1.1 GitHub Account
- Gehe zu https://github.com/signup
- Email + Passwort
- Email bestätigen
- **Nicht vergessen:** Username merken (z.B. `dein-github-username`)

### 1.2 Railway Account
- Gehe zu https://railway.app
- "Login with GitHub" klicken
- GitHub-Zugriff erlauben
- Fertig!

### 1.3 API Keys besorgen

**Anthropic API Key:**
1. Gehe zu https://console.anthropic.com
2. Login mit deinem Anthropic Account
3. Linke Sidebar: "Settings" → "API Keys"
4. "Create Key" klicken
5. Key kopieren (sieht so aus: `sk-ant-v0-xxxxx...`)

**Lemlist API Key:**
1. Gehe zu Lemlist
2. Account → Settings → Integrations
3. "API" Sektion → Key anzeigen
4. Kopieren

**Lemlist Sender User ID:**
1. Lemlist → Account → Settings → Developer
2. "User ID" kopieren (sieht so aus: `usr_xxxxx`)

---

## Phase 2: GitHub Repo erstellen & Code pushen (10 Min)

### 2.1 Neues Repo auf GitHub
1. Gehe zu https://github.com/new
2. Repository name: `valoon-linkedin-ai`
3. Description: `AI-powered LinkedIn reply automation for Valoon`
4. Public oder Private (egal)
5. "Create repository" klicken

### 2.2 Drei Dateien hinzufügen

**Datei 1: main.py**
1. Im Repo: "Add file" → "Create new file"
2. Dateiname: `main.py`
3. Kopiere den Inhalt von `main.py` hier rein (gesamter Code)
4. Unten: "Commit new file" klicken

**Datei 2: requirements.txt**
1. "Add file" → "Create new file"
2. Dateiname: `requirements.txt`
3. Kopiere Inhalt rein
4. "Commit new file"

**Datei 3: railway.json**
1. "Add file" → "Create new file"
2. Dateiname: `railway.json`
3. Kopiere Inhalt rein
4. "Commit new file"

**Datei 4: .env.example** (optional, für lokale Tests)
1. "Add file" → "Create new file"
2. Dateiname: `.env.example`
3. Folgenden Inhalt kopieren:
   ```
   ANTHROPIC_API_KEY=sk-ant-v0-your-key-here
   LEMLIST_API_KEY=your-lemlist-api-key
   LEMLIST_SENDER_USER_ID=usr_xxxxx
   REVIEW_MODE=true
   ```
4. "Commit new file"

---

## Phase 3: Railway Deploy (5 Min)

### 3.1 Projekt erstellen
1. Gehe zu https://railway.app
2. "New Project" klicken
3. "Deploy from GitHub repo" auswählen
4. GitHub verbinden (falls noch nicht geschehen)
5. Dein `valoon-linkedin-ai` Repo auswählen
6. "Deploy" klicken
7. **Warten** (ca. 2-3 Minuten)

### 3.2 Environment Variables eintragen
1. Im Railway-Projekt: Tab "Variables" öffnen
2. "Add Variable" klicken, folgende hinzufügen:

| Key | Value |
|-----|-------|
| `ANTHROPIC_API_KEY` | dein-anthropic-key (sk-ant-...) |
| `LEMLIST_API_KEY` | dein-lemlist-api-key |
| `LEMLIST_SENDER_USER_ID` | usr_xxxxx |
| `REVIEW_MODE` | true |

3. Nach jeder Variable: Enter drücken oder "Add" klicken

### 3.3 Webhook URL kopieren
1. Im Projekt: Tab "Settings" öffnen
2. Unter "Domains" findest du die Public URL:
   ```
   https://valoon-linkedin-ai-production-xxxxx.up.railway.app
   ```
3. Diese URL merken!
4. Später: `/webhook` anhängen → finale URL:
   ```
   https://valoon-linkedin-ai-production-xxxxx.up.railway.app/webhook
   ```

### 3.4 Logs anschauen (optional, zum Debuggen)
1. Tab "Logs" öffnen
2. Deploy-Prozess sehen
3. Nach Deploy: "Status: ok" sollte stehen

---

## Phase 4: Lemlist Webhook eintragen (2 Min)

1. Gehe zu Lemlist
2. Settings → Integrations → Webhooks
3. "Add Webhook" klicken
4. Folgendes eintragen:
   - **URL:** `https://deine-railway-url.up.railway.app/webhook`
   - **Event:** `linkedinReplied` (aus Dropdown)
   - **Active:** Toggle an
5. "Save" klicken

---

## Phase 5: Testen (2 Min)

### 5.1 Railway Logs anschauen
1. In Railway: Tab "Logs" öffnen
2. Dort solltest du folgendes sehen:
   ```
   Uvicorn running on http://0.0.0.0:8000
   ```
   = Script läuft ✅

### 5.2 Test-Reply simulieren
1. In Lemlist: Einen Lead aus deiner LinkedIn-Kampagne nehmen
2. Manuell eine Test-Antwort senden (z.B. "Hallo, wie funktioniert das?")
3. Zurück zu Railway → Logs

### 5.3 Logs lesen
Du solltest sehen:
```
Webhook received
Lead: Max Mustermann
Language detected: de
Generating response for Max Mustermann...
Response generated: [deine AI-Antwort]
REVIEW MODE: Response logged, not sent to Lemlist
```

### 5.4 Antwort in Google Sheet loggen (2-Wochen-Review)
1. Gehe zu: `https://deine-railway-url.up.railway.app/logs`
2. Alle generierten Antworten als JSON sehen
3. Du kannst diese manuell in Google Sheets kopieren oder selbst ein Script bauen

---

## Phase 6: Nach 2 Wochen Review → Auto-Send aktivieren

Wenn die Antwortqualität passt:

1. In Railway: Variables
2. `REVIEW_MODE` von `true` zu `false` ändern
3. Deploy startet automatisch
4. **Jetzt** werden Antworten direkt via Lemlist API gesendet

---

## Troubleshooting

### "Deployment failed"
- Railway Logs anschauen
- Meist: Falsche Umgebungsvariablen oder GitHub Zugriff fehlt

### "Webhook wird nicht empfangen"
1. URL in Lemlist richtig? (keine Leerzeichen, https nicht http)
2. Railway Logs: Sieht du die Webhook Requests?
3. Lemlist App: Ist das Webhook aktiv (Toggle)?

### "Claude API error"
- ANTHROPIC_API_KEY richtig kopiert?
- API Key hat keine Leerzeichen am Anfang/Ende?

### "Lemlist API error"
- LEMLIST_API_KEY und LEMLIST_SENDER_USER_ID richtig?

### Antworten sind zu kurz/schlecht
- Nach 2 Wochen: Prompt in `main.py` anpassen
- Danach: Code ändern → auf GitHub pushen → Railway deployed automatisch

---

## URLs zum Nachschauen

- **Railway Logs:** https://railway.app → Projekt → "Logs" Tab
- **AI Antworten:** https://deine-railway-url.up.railway.app/logs
- **Health Check:** https://deine-railway-url.up.railway.app/health

---

## Support

Wenn was nicht funktioniert:
1. Railway Logs anschauen (meist der beste Hinweis)
2. Umgebungsvariablen doppelchecken (keine Typos, keine Leerzeichen)
3. GitHub Repo public machen (falls private)
4. Railway App einmal manuell restarten (Settings → "Restart")

---

**Das war's! 🚀**

Nach 2 Wochen Review: `REVIEW_MODE=false` setzen → Auto-Send an!
