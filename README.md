# Reflect AI 🤖
### Social on Auto-Pilot — Relationship Intelligence Dashboard

Reflect AI connects to your Telegram, analyzes your conversations using a large language model, and gives you a live dashboard showing the health of every relationship — with actionable insights and a drafted message ready to send.

---

## Pipeline

```
Telegram API
     │
     ▼
telegram_fetcher.py  →  data/*.json
                              │
                              ▼
                         parser.py
                              │
                              ▼
                        analyzer.py  ◄──┐
                              │         │
                              ▼         │  Groq LLM
                         merger.py      │  (Llama-3.3-70B)
                              │         │
                              ▼         │
                         scorer.py      │
                              │         │
                              ▼         │
                        insights.py  ◄──┘
                              │
                              ▼
                    app.py (Flask :5000)
                              │
                              ▼
                      Web Dashboard 🌐
```

---

## Features

- **Telegram Ingestion** — Authenticates via Telethon and fetches your last 200 messages per dialog
- **LLM Analysis** — Chunks conversations and sends them to Groq (Llama-3.3-70B) to extract mood, urgency, topics, todos, and calendar events
- **Relationship Scoring** — Computes a 0–100 health score based on recency, frequency, reciprocity, and sentiment
- **AI Insights** — Generates a Pattern, Risk assessment, and a ready-to-send Action message per contact
- **Web Dashboard** — Filter contacts by Active / Cooling / At Risk, search by name, and download PDF reports

---

## Setup

### 1. Clone & install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure `.env`
```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+91xxxxxxxxxx
GROQ_API_KEY=your_groq_key
```

Get Telegram credentials at [my.telegram.org](https://my.telegram.org).  
Get a free Groq key at [console.groq.com](https://console.groq.com).

### 3. Run
```bash
python main.py
```

On first run, Telegram will send a verification code to your phone. Enter it in the terminal.  
The dashboard will then be live at **http://localhost:5000**.

---

## Project Structure

| File | Role |
|------|------|
| `main.py` | Orchestrator — runs fetcher then starts Flask |
| `telegram_fetcher.py` | Connects to Telegram, saves messages to `data/` |
| `parser.py` | Normalises raw JSON into a standard message format |
| `analyzer.py` | Chunks messages, calls Groq LLM for structured analysis |
| `merger.py` | Consolidates all chunk analyses into one profile per contact |
| `scorer.py` | Computes relationship health score (0–100) |
| `insights.py` | Calls Groq LLM for Pattern / Risk / Action insights |
| `app.py` | Flask web server with in-memory cache |
| `pdf_generator.py` | Exports contact profiles as downloadable PDFs |

---

## Tech Stack

- **[Telethon](https://docs.telethon.dev/)** — Telegram client
- **[Groq](https://console.groq.com/)** — LLM inference (Llama-3.3-70B)
- **[Flask](https://flask.palletsprojects.com/)** — Web server
- **[FPDF2](https://py-pdf.github.io/fpdf2/)** — PDF generation
- **[python-dotenv](https://pypi.org/project/python-dotenv/)** — Environment config

---

## Notes

- The session file (`reflect_session.session`) is created after first login — delete it to re-authenticate.
- All fetched data is stored locally in `data/` — nothing is sent to any external server except the Groq API for analysis.
- Run with `PYTHONIOENCODING=utf-8` on Windows to avoid emoji encoding issues.
