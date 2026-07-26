# Agent Empire — Build Handoff Prompt

Copy the prompt below into a new coding chat that is connected to the **AI_Playground** repository.

---

Work on the existing experimental project at `agent-empire/` in this repository.

First, read these files in full:

- `agent-empire/README.md`
- `agent-empire/BUILD_PLAN.md`

`BUILD_PLAN.md` is the source of truth for Agent Empire v0.1. It fixes the product scope, technical decisions, game rules, data contracts, deterministic simulation, content requirements, UI, export format, build milestones, and acceptance tests. Follow it precisely. Do not ask me to settle routine implementation decisions that this file already resolves.

Build the complete playable v0.1 now. Do not return another plan, static mock-up, or high-level explanation. Implement the project, run it locally, test it, and leave the repository in a state where I can play it in a browser.

Agent Empire is a single-player browser strategy game where the player is the CEO of an AI-run startup. Each run gives them a realistic AI-operable business scenario, budget, deadline, and requirements. They hire managers and specialist agents, define reporting lines, choose tools, then run a simulated company through Research, Planning, Build, Launch, and Growth. Organisation structure, capacity, chemistry, functional coverage, cost, and CEO interventions must materially affect the outcome. The end of every run must provide a result screen and downloadable Markdown and JSON organisational blueprints.

Execution rules:

1. Work only inside `agent-empire/`. Do not create a separate repository.
2. Inspect the current repository first. If `agent-empire/` only contains the specification documents, initialise the React + TypeScript + Vite app there.
3. Implement the game engine and its testable rules before visual refinement.
4. Use the actual data model, five scenarios, roster quantities, formulas, event rules, interventions, outcome score, and export contract in `BUILD_PLAN.md`. Do not replace them with placeholders.
5. Keep v0.1 fully local and browser-only: no backend, account, API key, external database, or live model calls.
6. Use `localStorage` for the active run, run archive, and settings.
7. Build a polished, responsive dark strategic-operations UI. It must work on desktop and phone, but clear gameplay is more important than elaborate animations or drag-and-drop.
8. Add the unit and end-to-end coverage required by the test matrix. Seeded runs must be reproducible.
9. Run and verify the full loop: new run → briefing → organisation builder → approval → five phases/events → results → Markdown and JSON export.
10. Make safe, in-scope local changes and run non-destructive validation autonomously. Stop only for a genuine blocker that cannot be resolved from this prompt or the repository files.

At handoff, provide a concise summary containing:

- What you built
- How to run it
- What you tested and the result
- Any deliberate v0.1 simplifications
- Exact files changed
- Local preview URL, if available

---

The coding chat should start by reading the two specification files above, then execute the prompt without needing separate attachments.
