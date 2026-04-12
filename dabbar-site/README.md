# dabbar.ai — Landing Page

Arabic-first (RTL default) bilingual landing page for Dabbar. Single-file HTML — no build step, no framework, no external CSS or JS.

## Design

- **Palette**: editorial black (`#0a0a0a`) + gold (`#c8a84e`) + cream (`#f5f2eb`)
- **Type**: IBM Plex Sans Arabic for Arabic/English body, Space Mono for labels
- **Grain overlay**: SVG fractal noise at 4% opacity (printed-paper feel)
- **Positioning**: UAE-specific services — DEWA bills, RTA fines, restaurant bookings, personal memory
- **Conversion path**: CTA goes straight to `https://t.me/dabbar_ai` (no waitlist form)

## Structure

```
dabbar-site/
├── index.html     — everything (HTML + inline CSS + inline JS, ~20KB)
├── assets/        — favicons, og images (add as needed)
└── README.md      — this file
```

Everything is in one file for fast iteration and cache-friendly delivery.

## Sections

1. **Hero** — brand, tagline, Telegram CTA
2. **What is Dabbar?** — 4 feature cards (DEWA, RTA, Restaurants, Personal memory)
3. **How it works** — 3 steps
4. **Pricing** — single AED 500/month card with founding-price badge
5. **Comparison** — side-by-side table vs human PA
6. **Bottom CTA** — "Let Dabbar sort it out" + Telegram link

## Local preview

```bash
cd dabbar-site
python3 -m http.server 8080
# open http://localhost:8080
```

Or through the AI Playground Flask app:

```bash
cd ai-dashboard
python3 app.py
# open http://localhost:5000/dabbar-preview
```

## Deploy

- **Render** (already configured via `render.yaml`): push to `main`, Render auto-redeploys the Flask app which mounts this page at `/dabbar-preview`
- **Vercel / Netlify**: point at this folder, it's a static site
- **DGX Spark nginx**: copy to `/var/www/dabbar.ai/`

## Language toggle

The `toggleLang()` function swaps between `dir="rtl"` (Arabic) and `dir="ltr"` (English) by reading `data-ar`/`data-en` attributes on every translatable element. Default on load is Arabic. No framework, no state library — vanilla DOM.

## TODO

- [ ] Favicon (gold د on black)
- [ ] OG image at `assets/og.png`
- [ ] Real Telegram bot handle (currently `@dabbar_ai` — wire once BotFather registration is done)
- [ ] Analytics (Plausible recommended — privacy-friendly, one script tag)
- [ ] Arabic copy review by a native Gulf speaker
- [ ] Record demo GIF/video and embed under the hero
