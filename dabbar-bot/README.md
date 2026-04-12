# Dabbar Bot (دبّر)

Personal AI assistant for UAE consumers, delivered via Telegram. Powered by local Ollama
(Llama 3.1 8B) running on DGX Spark.

## Features (MVP)

- 💬 **Conversational chat** — Arabic (Gulf dialect) and English
- ⏰ **Reminders** — "remind me to call Ahmad in 10 minutes"
- 📝 **To-do list** — add, list, complete, delete tasks
- 🔎 **Web search** — DuckDuckGo results summarised by the LLM
- 🗄️ **Per-user SQLite** — isolated storage per Telegram user

Roadmap: Google Calendar + Gmail integration, expense tracking, voice messages, document generation.

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Telegram    │───▶│ dabbar-bot   │───▶│ Ollama          │
│ (aiogram)   │    │ (Python)     │    │ (Llama 3.1 8B)  │
└─────────────┘    └──────┬───────┘    └─────────────────┘
                          │
                   ┌──────▼───────┐
                   │ Per-user     │
                   │ SQLite DBs   │
                   └──────────────┘
```

- `src/bot.py` — aiogram entry point, message handlers, APScheduler
- `src/llm.py` — Ollama chat client + tool-call parser
- `src/dispatcher.py` — executes tool calls against user DB
- `src/db.py` — per-user SQLite wrapper (tasks, reminders, messages)
- `src/tools/` — individual tool implementations (search, time parsing)

## Quick start

### 1. Set up environment

```bash
cp .env.example .env
# Edit .env and set TELEGRAM_BOT_TOKEN (from @BotFather)
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

First run: pull the Llama model inside the Ollama container:

```bash
docker exec -it dabbar-ollama ollama pull llama3.1:8b
docker exec -it dabbar-ollama ollama pull qwen2.5:3b
```

### 3. Local dev without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Start Ollama separately: `ollama serve`
export TELEGRAM_BOT_TOKEN=...
python -m src.bot
```

## Example interactions

```
User:  remind me to pay the rent tomorrow at 9am
Dabbar: ✅ Reminder set for Sat 12 Apr, 09:00 — "pay the rent"

User:  add milk, bread, and eggs to my list
Dabbar: ✅ Added task #1: milk
        ✅ Added task #2: bread
        ✅ Added task #3: eggs

User:  what's the weather in Dubai right now
Dabbar: 🔎 Results for "weather in Dubai right now":
        ...
```

## Commands

- `/start` — welcome message (Arabic or English based on input)
- `/reset` — clear conversation history

## Next steps

- [ ] Google OAuth integration (Calendar + Gmail via GWS skills)
- [ ] Payment integration (Telegram Stars or Stripe AED)
- [ ] Admin dashboard in AI Playground Flask app
- [ ] OpenSpace integration for self-evolving skills
- [ ] Voice message support (Whisper transcription)
