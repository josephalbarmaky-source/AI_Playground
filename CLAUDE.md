# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository layout

This repo is a monorepo of three **independent** projects that share nothing but git history. There is no root package manager and no cross-project imports — each is run from its own directory.

- `ai-dashboard/` — Flask app (AI project tracker **and** family home dashboard). This is the service Render deploys.
- `dabbar-bot/` — Telegram bot (`aiogram` + Ollama), packaged with Docker Compose.
- `dabbar-site/` — Static Arabic-first bilingual landing page for dabbar.ai. No build step.
- `tools/` — README-only index of AI tooling installed at `~/tools/` on the host machine; nothing in this folder is executed by the repo itself.
- `render.yaml` — Render blueprint. Only `ai-dashboard` is deployed.
- `.github/workflows/dabbar-site-pages.yml` — Deploys `dabbar-site/` to GitHub Pages on pushes to `main` that touch `dabbar-site/**`.

## ai-dashboard (Flask)

**Run locally:**
```bash
cd ai-dashboard
pip install -r requirements.txt
python app.py                       # binds 0.0.0.0:5000 so iPhone/iPad on the LAN can hit it
```

**Production (Render):** `gunicorn app:app --bind 0.0.0.0:$PORT` (see `render.yaml`). Python 3.11.

Routes worth knowing:
- `/` → AI agent project tracker (`dashboard.html` + `/kanban`, `/project/<id>`)
- `/family` → standalone full-screen family dashboard (schedule, calendar, grocery, house info, photos)
- `/spinner`, `/tools` → standalone pages
- `/dabbar-preview` → serves `../dabbar-site/index.html` from the Flask process (lets you preview the landing page via the same server)
- `/api/...` and `/api/family/...` — JSON CRUD for every model in `models.py`
- `/api/family/g4s/*` — Go4Schools proxy (requires `GO4SCHOOLS_API_KEY`)
- `/api/family/photos/*` — Google Photos OAuth + read-only integration (requires `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`)

### Architecture notes (multi-file context)

- **`init_db()` runs at import time** (called at the bottom of `app.py`, not inside `if __name__ == "__main__"`). Importing `app` creates `database.db` and auto-seeds agents, `ScheduleEvent` via `seed_timetable.seed()`, and `CalendarEvent` via `seed_tutoring.seed_tutoring()`. Gunicorn imports `app`, so seeding happens on every fresh Render deploy.
- **Seed modules import lazily from inside the seed function**, not at module top level. This is deliberate — top-level `from app import app` caused a circular import on boot from an empty DB (see commit `4a23bd5`). Keep it that way when adding new seeders.
- `models.py` defines two unrelated domains in one file: the AI-projects domain (`Agent`, `Project`, `Task`, `ActivityLog`) and the family dashboard domain (`ScheduleEvent`, `CalendarEvent`, `GroceryItem`, `HouseInfo`, `FamilyActivity`). They share the same SQLite DB but are not related by foreign keys.
- `ScheduleEvent.week_type` is `'A'` or `'B'` — the timetable is a rotating two-week schedule. Friday only has 4 periods (see `PERIODS_FRIDAY` in `seed_timetable.py`).
- Google Photos tokens are stored in `ai-dashboard/.google_photos_token.json` (git-ignored via `.env`/instance patterns — verify new secret files are ignored before committing). Go4Schools key is persisted to `ai-dashboard/.env` by `/api/family/g4s/setup`.
- `DABBAR_SITE_DIR` is resolved relative to `ai-dashboard/app.py` (`../dabbar-site`) — so `/dabbar-preview` only works when the two folders sit side-by-side, as they do in this repo.
- Templates and static assets are plain Jinja + vanilla JS/CSS. No bundler, no framework, no TypeScript. `family-dashboard.html` and its JS are the largest surface.

## dabbar-bot (Telegram bot)

**Run (Docker, recommended):**
```bash
cd dabbar-bot
cp .env.example .env        # set TELEGRAM_BOT_TOKEN from @BotFather
docker compose up --build
# first boot only — pull models into the Ollama container:
docker exec -it dabbar-ollama ollama pull llama3.1:8b
docker exec -it dabbar-ollama ollama pull qwen2.5:3b
```

**Run (local, no Docker):**
```bash
cd dabbar-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama serve                 # in another shell
export TELEGRAM_BOT_TOKEN=...
python -m src.bot            # must use module form; src/ is a package
```

### Architecture notes

- **Per-user SQLite** (`src/db.py`): every Telegram user gets an isolated `user_<telegram_id>.db` under `DABBAR_DATA_DIR` (default `/data` in Docker, `./data` locally). Tables: `tasks`, `reminders`, `messages`, `profile`. Never share rows across users.
- **Tool-calling contract** (`src/llm.py`): the system prompt instructs the LLM to emit a single-line JSON object `{"tool": "...", "args": {...}}` when a tool is needed, or plain text otherwise. `parse_tool_call()` parses the first balanced JSON object from the response. When adding a new tool you must: (1) document it in `SYSTEM_PROMPT`, (2) add a branch in `dispatcher.dispatch()`, (3) implement the helper (usually under `src/tools/`).
- **Reminders** are dispatched via APScheduler (`DateTrigger`). `bot.restore_pending_reminders()` scans every `user_*.db` on startup and re-arms jobs that haven't fired; overdue reminders fire once immediately. Reminder rows store `fire_at` as **ISO 8601 UTC** even though the user timezone defaults to `Asia/Dubai` — conversion happens in `dispatcher.py` via `ZoneInfo(timezone)`.
- `config.py` raises at import time if `TELEGRAM_BOT_TOKEN` is unset, unless `DABBAR_SKIP_CONFIG=1`. Use that env var for tooling/tests that import the package without launching the bot.
- Arabic vs English replies are picked by `_is_arabic()` (presence of any `U+0600..U+06FF` code point in the user's text), not a stored preference.

## dabbar-site (static landing page)

Single-file site: `index.html` contains HTML + inline CSS + inline JS (~22KB). No framework, no build step.

**Preview:**
```bash
cd dabbar-site && python3 -m http.server 8080     # http://localhost:8080
# or, from the Flask app:
cd ai-dashboard && python3 app.py                  # http://localhost:5000/dabbar-preview
```

**Deploy:** pushing to `main` with any change under `dabbar-site/**` triggers the GitHub Pages workflow. `.nojekyll` is present and required — do not delete it or Jekyll will strip the `assets/_*` convention. Render also serves the page at `/dabbar-preview` via the Flask app.

Language toggle is vanilla DOM: every translatable element carries `data-ar` and `data-en`, and `toggleLang()` flips `dir` on `<html>` and swaps text content. Default load is Arabic (`dir="rtl"`).

## Conventions

- **Dates/times:** UTC in the database, local (`Asia/Dubai` for Dabbar, browser-local for the family dashboard) only at display time. `CalendarEvent.date` is `YYYY-MM-DD`, `start_time`/`end_time` are `HH:MM` — both stored as strings, not timestamps.
- **Secrets:** `.env` files per subproject (`ai-dashboard/.env`, `dabbar-bot/.env`); the dashboard also writes to its own `.env` from the UI setup endpoints. `.gitignore` already excludes both, plus `dabbar-bot/data/`, `ai-dashboard/database.db`, and `ai-dashboard/dabbar_waitlist.jsonl`.
- **No test suite** exists in any subproject. Don't claim tests pass — there are none to run. Validate changes by exercising the relevant route/command manually.
- **No linter config** is checked in. Match surrounding style (PEP 8-ish Python, two-space-ish HTML/JS in the single-file pages).
