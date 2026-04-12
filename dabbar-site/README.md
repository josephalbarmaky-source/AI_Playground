# dabbar.ai — Landing Page

Bilingual (Arabic / English) landing page for Dabbar. Zero-framework — pure HTML/CSS/JS, deploys anywhere.

## Tech

- HTML + CSS + vanilla JS — no build step
- Inter (English) + Tajawal (Arabic) via Google Fonts
- Language toggle with `dir="rtl"` switching
- Waitlist form (client-side only — wire to a backend endpoint for production)
- Dark premium theme inspired by Superhuman / Linear

## Local preview

```bash
cd dabbar-site
python3 -m http.server 8080
# open http://localhost:8080
```

## Structure

```
dabbar-site/
├── index.html     — page structure with data-i18n markers
├── style.css      — all styling, dark theme, RTL-aware
├── script.js      — i18n dictionary, language toggle, waitlist handler
└── assets/        — images, favicons (add as needed)
```

## Deploy

- **Vercel / Netlify**: point at this folder, it's static
- **DGX Spark (nginx)**: copy to `/var/www/dabbar.ai/`
- **AI Playground Flask**: mounted at `/dabbar-preview` (see `ai-dashboard/app.py`)

## TODO for production

- [ ] Replace waitlist localStorage with real backend (POST to Flask endpoint)
- [ ] Add Plausible/Fathom analytics
- [ ] Open Graph image at `assets/og.png`
- [ ] Favicon (Arabic د mark on purple gradient)
- [ ] Add actual demo video (once recorded with Remotion)
- [ ] Translations reviewed by a native Gulf Arabic speaker
