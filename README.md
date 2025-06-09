# 🧠 COS – Cognitive Orchestrated Scheduling

> _„Planung ist nichts – Planung ist alles.“_

**Otto** ist ein neuartiger, kognitiv unterstützter Planungsassistent. Im Kern steht das Konzept **COS – Cognitive Orchestrated Scheduling**:  
Ein flexibles, KI-gestütztes System zur Erkennung, Strukturierung und Weiterverarbeitung von Aufgaben, Meetings, Entscheidungen und Verantwortlichkeiten – automatisch, nachvollziehbar, assistierend.

## 🌐 Zielsetzung

- **Automatisierung** repetitiver Planungs- und Verwaltungsprozesse
- **Kontextuelle Intelligenz** durch semantische Analyse von Transkripten, Dokumenten und Benutzerinteraktionen
- **Strukturierte Zusammenarbeit** durch Aufgaben-, Meeting- und Rollenmanagement
- **Erweiterbarkeit** durch modulare Architektur und offene Schnittstellen
- **Selbstlernend & adaptiv** durch Feedback-Schleifen und Integration lokaler und externer LLMs

## 🧩 COS-Grundmodule (aktuell in Otto)

| Modul                  | Funktion                                                                 |
|------------------------|--------------------------------------------------------------------------|
| 🗓️ Meetings             | Agenda-Verwaltung, Protokolltranskripte, automatische Task-Extraktion   |
| 🧠 KI / LLM             | OpenAI / Ollama-Integration für GPT/Mistral-basierte Auswertung          |
| 🔍 Vektorsuche          | Kontextbezogene Recherche mit qdrant                                  |
| 🧑 Personen / Mandanten | Benutzer, Rollen, Organisationen, Mandantenfähig                        |
| 📬 E-Mail Integration   | Microsoft Graph API: Kalender, Mails, Benutzerinformationen              |
| 📝 Tasks & Projekte     | Strukturierte Planung & Verantwortungszuweisung                         |
| 💬 Kommentare           | Kontextsensitive Diskussion & Feedback direkt im Item                   |
| 📊 Analyse / Jupyter    | Jupyter-Knoten für technische Analyse und Promptentwicklung              |

## 💡 Leitsatz

> **„COS denkt mit – und denkt voraus.“**  
> Durch den Einsatz von Sprache, semantischer Kontextanalyse und KI werden nicht nur Aufgaben erkannt, sondern direkt im richtigen Zusammenhang priorisiert, verknüpft und vorbereitet.

## 🧱 Zukunftsbausteine (Vision)

- Adaptive Agentenlogik (z. B. MeetingBot, TaskBot)
- Multimodale Eingabe (Audio, OCR, PDF)
- Plagiat- & Ähnlichkeitsprüfung (z. B. in Studienarbeiten)
- Verhaltensmodelle für Nutzerführung & Empfehlungen
- Berechtigungs- und Kontextsicherheitsmodell
- Progressive Web App / Offlinefähigkeit

## GitHub-Integration

Damit im Projektformular GitHub-Repositories auswählbar sind, müssen folgende
Umgebungsvariablen gesetzt sein (z.B. in einer `.env` Datei):

```
GitHub_API_URL=https://api.github.com
GitHub_ORGNAME=<deine Organisation>
GitHub_API_KEY=<persönlicher Access Token>
```

Christian Angermeier, Mai 2025
