# AI Playground - Skills & Conventions

## Project Overview

This repository is a playground for AI-powered projects. Currently contains:

- **ai-dashboard/** — A Flask web app for tracking AI agents and their projects/tasks. Includes a Kanban board, project detail views, activity logging, and dashboard stats.

**Tech stack:** Python 3, Flask 3.0, Flask-SQLAlchemy, SQLite, vanilla JavaScript, custom CSS (dark theme)

## Project Structure

```
AI_Playground/
├── ai-dashboard/
│   ├── app.py              # Flask routes and API endpoints
│   ├── models.py           # SQLAlchemy models (Agent, Project, Task, ActivityLog)
│   ├── requirements.txt    # Python dependencies
│   ├── static/
│   │   ├── css/style.css   # Global styles, CSS variables, responsive design
│   │   └── js/app.js       # Frontend logic, API calls, modals, utilities
│   └── templates/
│       ├── base.html       # Layout shell with sidebar and modals
│       ├── dashboard.html  # Project list, stats, activity feed
│       ├── kanban.html     # 5-column Kanban board
│       └── project.html    # Project detail with tasks and timeline
└── try.py                  # Scratch file
```

## Coding Conventions

### Python / Backend

- **Routes**: RESTful, grouped by resource (Agents, Projects, Tasks, Activities, Stats)
- **Activity logging**: Always use the `log_activity()` helper in `app.py` when state changes occur
- **Serialization**: Models expose `to_dict()` methods for JSON responses; use `include_tasks=True` for nested data
- **Relationships**: Define SQLAlchemy relationships with `cascade="all, delete-orphan"` for parent-child data
- **Status values**: Projects use `planning | in_progress | review | complete | on_hold`; Tasks use `pending | in_progress | completed`; Priorities use `low | medium | high | critical`
- **Database**: SQLite via `database.db` — keep queries simple, no raw SQL unless necessary

### JavaScript / Frontend

- **No frameworks** — vanilla JS only, keep it lightweight
- **API calls**: Use the `apiRequest(url, options)` wrapper in `app.js` for consistent error handling
- **Modals**: Manage via DOM class toggling (`show`/hide pattern); support Escape key to close
- **Date formatting**: Use existing utility functions (`formatDate`, `timeAgo`) in `app.js`

### CSS

- **CSS custom properties** for all colors and theming — never hardcode color values
- **Dark theme** with indigo accents is the design system
- **Class naming**: BEM-inspired (e.g., `.card-header`, `.status-badge`)
- **Responsive breakpoints**: 1200px, 900px, 768px — test that new UI works at all sizes
- **Layout**: CSS Grid for page structure, Flexbox for component internals

### General

- No linters or formatters are configured — match the style of surrounding code
- Keep dependencies minimal; avoid adding heavy libraries when vanilla solutions work
- Environment variables via `python-dotenv` — sensitive config goes in `.env` (gitignored)

## Task Checklists

### Before Starting

- [ ] Read the files you plan to modify — understand existing code before changing it
- [ ] Check `models.py` for the data schema before any database-related changes
- [ ] Look for existing utilities/helpers that can be reused (e.g., `log_activity()`, `apiRequest()`, CSS variables)

### During Development

- [ ] Follow existing naming conventions and file organization
- [ ] Log activities via `log_activity()` for any project or task state changes
- [ ] Keep API endpoints RESTful and consistent with existing routes
- [ ] Use CSS variables from `style.css` — do not hardcode colors or spacing
- [ ] New templates should extend `base.html`

### After Completing

- [ ] Verify no hardcoded values that should use variables or constants
- [ ] Ensure new routes match the existing URL and response patterns
- [ ] Check that database relationships and cascading deletes are correct
- [ ] Confirm new UI is responsive and doesn't break at defined breakpoints
- [ ] Test that activity logging captures relevant state changes
