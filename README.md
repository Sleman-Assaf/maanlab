# MAAN LAB — website

Creative technology studio from Ma'an, Jordan. Server-rendered Django site (EN `/en/` + AR `/ar/`, full RTL), with GSAP/ScrollTrigger/Lenis motion added as progressive enhancement. Design and motion language follow the approved ORYN study (`../ORYN_ANALYSIS.md`).

---

## 1. Project structure

```
maanlab/
├── config/                 settings (env-driven), urls (i18n_patterns), wsgi/asgi
├── core/                   homepage, SEO, i18n helpers, image pipeline, HeroMedia
│   ├── content.py          services copy + service visual paths (gettext)
│   ├── imaging.py          upload paths + automatic WebP/AVIF responsive variants
│   ├── i18n.py             bilingual field helper → {{ obj.t.title }}
│   ├── sitemaps.py         i18n sitemap with hreflang alternates
│   ├── templatetags/maan.py  {% picture %}, {% anchor %}, |pad2
│   └── management/commands/compile_translations.py   .po → .mo without GNU gettext
├── projects/               Project + ProjectMedia models, admin, detail view
│   ├── placeholders.py     Pillow-generated, clearly-labelled placeholder covers
│   └── management/commands/seed_demo.py
├── contact/                ContactMessage model, ModelForm, POST view, admin
├── templates/
│   ├── base.html           <html lang dir>, fonts, SEO, scripts
│   ├── home.html           section composition
│   ├── partials/           navbar, footer, seo, picture, field, project_card, section_head, icons, lang_switch
│   ├── sections/           hero, services, reel, projects, about, contact
│   ├── projects/detail.html
│   └── 404.html / 500.html
├── static/
│   ├── css/main.css        tokens → components → motion states → RTL/reduced-motion
│   ├── js/main.js          entry (ES module) + js/modules/*.js
│   ├── vendor/             gsap, ScrollTrigger, Flip, SplitText, CustomEase (3.13), lenis (1.3.11) — local copies
│   ├── img/                hero object, service visuals, brand assets (PLACEHOLDERS)
│   └── video/              placeholder film loops + posters
├── locale/ar/LC_MESSAGES/  django.po / django.mo (Arabic catalog, 269 strings)
├── locale_src/translations_ar.py   Arabic source dictionary used to build django.po
├── tools/                  dev-only: asset generator, string extractor, browser QA scripts
├── requirements.txt
└── .env.example
```

Homepage order: **Navigation → Hero → Our Services → (AI video reel band) → Our Projects → Who We Are → Contact Us → Footer**. The reel is a short transition band that gives AI video production its visual weight; there is no FAQ.

---

## 2. Setup

```bash
cd maanlab
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env  → set DJANGO_SECRET_KEY
python manage.py migrate
python manage.py compile_translations
python manage.py seed_demo        # 7 labelled sample projects with placeholder media
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ → redirects to `/en/` (or `/ar/` from the browser language / last choice).

Run the checks:

```bash
python manage.py check
python manage.py test
```

Production build:

```bash
set DJANGO_DEBUG=False
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Static files are served by WhiteNoise (hashed + compressed, ES-module imports rewritten). **Uploaded media** (`/media/`) is only served by Django in DEBUG — in production serve `MEDIA_ROOT` from the web server (nginx `location /media/`) or object storage.

---

## 3. Environment variables

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | **required** when DEBUG is False | dev key only in DEBUG |
| `DJANGO_DEBUG` | `True` / `False` | `False` |
| `DJANGO_ALLOWED_HOSTS` | comma-separated hosts | `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | e.g. `https://maanlab.com` | — |
| `SITE_URL` | canonical origin for canonical/hreflang/OG/sitemap | `http://127.0.0.1:8000` |
| `DB_ENGINE` | `sqlite` or `postgres` | `sqlite` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | PostgreSQL (install `psycopg[binary]`) | — |
| `CONTACT_EMAIL` | public email shown on the site | `hello@maanlab.com` (placeholder) |
| `CONTACT_NOTIFY_EMAIL` | optional: email a copy of each inquiry | — |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL` | SMTP | console backend |
| `SOCIAL_INSTAGRAM`, `SOCIAL_FACEBOOK`, `SOCIAL_LINKEDIN` | footer links | placeholders |
| `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SECURE_HSTS_SECONDS`, `DJANGO_BEHIND_PROXY` | production security | `True`, `0`, `False` |

A local `.env` file is loaded automatically (real environment variables take precedence).

---

## 4. Django Admin

`/admin/` (language-neutral). After `createsuperuser`:

- **Projects → Projects** — English and Arabic fieldsets, category, year, client, featured, display order and published status (editable directly in the list), search, category/published/featured/year filters, cover **image or video** (either is enough; with both, the image is the video poster), optional card thumbnail, SEO fields, and an inline **gallery** (images/videos, full/half layout). Bulk actions: publish, unpublish, feature. WebP/AVIF responsive versions are generated on save.
- **Contact → Contact messages** — list shows name, email, phone, company, service, language, received date and read state; search by name/email/company/phone/message; filters for read/unread, service, language, date; date hierarchy; mark read/unread actions and an inline read toggle. Opening a message marks it read. Submissions are read-only.
- **Site → Hero media** — upload the final hero object (transparent PNG/WebP, ~1600px) or a short muted loop + poster. The newest active entry is used; without one the bundled placeholder object is shown.

Arabic fields are optional: an empty Arabic field falls back to English on `/ar/`.

---

## 5. Animation implementation

All motion is progressive enhancement over complete SSR HTML. `<head>` adds `html.js` (and `html.rm` for reduced motion) before first paint; hidden initial states only exist under `html.js:not(.rm)`, and a 3-second safety net (`html.anim-fallback`) reveals everything if scripts fail. Each JS module is isolated (`main.js → safely()`).

Easing tokens are the exact ORYN curves (CSS variables + GSAP `CustomEase`): `io .44,0,.56,1` · `accent .5,0,.88,.77` · `out .22,1,.36,1` · `bg .68,0,.2,.89` · `land .16,1,.3,1`.

| Effect | Where | How |
|---|---|---|
| Smooth scroll | global, ≥810px | Lenis `lerp 0.11`, driven by `gsap.ticker`, synced to ScrollTrigger; off for reduced motion. Custom anchor handler resolves sticky sections correctly. |
| Hero entrance | hero | GSAP timeline — bg push (1.3→1), navbar drop, **object lands** (scale 1.4, x/y offset → rest, 2.4s), text fade-ups at 0.4/0.6/1.0/1.3s, stats stagger 0.3s, shutter reveal on the featured film. x-offset mirrors in RTL. |
| Hero curtain | hero, ≥1200px | CSS `position: sticky; top: min(vh − h, −300px)` (set by `pins.js`); Services (`z-index 2`, opaque) slides over it. |
| Hero scroll | hero, ≥1200px | ScrollTrigger scrub 0.6 over the hero range: object scale 1→1.45 toward camera, bg 1→1.15, text parallax −140px, darkening shade. Tablet/mobile: gentle 1→1.08 only. |
| Headline blur-in | every section heading | English: SplitText chars from `blur(10px)`, opacity 0, y 10 → rest, 0.05s stagger. **Arabic**: a soft mask sweeps each line right→left while it un-blurs and settles — same letter-by-letter wave, without splitting (character splitting breaks Arabic letter joining). Triggers use `clamp()` and re-measure whenever page height changes (fonts, accordion, filtering). |
| Fade-up reveals | copy, cards, lists | One IntersectionObserver per threshold toggles `.is-in`; CSS transitions with per-element delay/offset via `data-reveal-*`. |
| Shutter image reveal | project cards, detail media, gallery, about | Two `::before/::after` panels `scaleY(1→0)` (start half up, end half down), 1.3s — transform-only version of ORYN's "Image reveal". |
| Services storyteller | services, ≥1024px | Tall wrapper + sticky viewport; ScrollTrigger progress selects the active service (panel opens with `grid-template-rows 0fr→1fr`, stage layers crossfade + scale 1.06→1, progress line fills). Buttons scroll to their segment; ↑/↓/Home/End keys. <1024px: single-open accordion with inline media; no JS: everything open. |
| AI video reel | between services and projects | ScrollTrigger scrub: `clip-path: inset(9% 11% round 28px) → inset(0)`, video 1.18→1; film UI with live 24fps timecode. |
| Project filter | projects | Links work without JS (`?category=`); JS filters the already-rendered cards via `hidden` + GSAP **Flip** (fade/scale in/out, grid height eased), updates URL, `aria-pressed`, live count. |
| Card media | project cards | Hover/focus: image zoom 1.045, category label slides in, title nudges (RTL-aware), arrow rotates; cursor "View/Play" badge (fine pointers only). Video cards play muted on hover (desktop) or the single most-visible card (touch); one video at a time. |
| Counters | Who We Are | Digit roller (0→value per digit, 1.76s, 0.1s stagger); SSR number stays as the accessible label. |
| Who We Are → Contact curtain | ≥1024px | Bottom-pinned sticky light section; dark Contact (rounded top, shadow) slides over it. |
| Navbar | global | Glass state after 24px, theme switches to light over light sections, active section indicator, centre-grow underline; mobile menu expands in place (0.4s open / 0.6s close) with focus trap, Esc, scroll lock. |
| Videos | global | Sources lazy-load near the viewport, autoplay only while visible, pause offscreen / hidden tab; accessible play/pause toggles; no autoplay with reduced motion or Save-Data. |

Reduced motion: no Lenis, no pins' scroll effects, no split text, no autoplay, all content visible immediately; sticky layout is kept.

---

## 6. Pages & routes

| Route | Description |
|---|---|
| `/` | redirects to `/en/` or `/ar/` |
| `/en/`, `/ar/` | homepage (`?category=ai_video` etc. filters server-side without JS) |
| `/en/projects/<slug>/`, `/ar/projects/<slug>/` | project detail |
| `/en/projects/`, `/ar/projects/` | redirects to the homepage projects section |
| `/en/contact/`, `/ar/contact/` | contact form POST (GET redirects to `#contact`) |
| `/admin/` | Django admin |
| `/sitemap.xml` | i18n sitemap with hreflang alternates |
| `/robots.txt` | robots with sitemap link |

---

## 7. Tests & checks performed

- `python manage.py check` — no issues. `check --deploy` (DEBUG=False) — only the optional HSTS-preload advisory.
- `python manage.py test` — **37 tests pass**: EN/AR homepage, `lang`/`dir`, Arabic content, hreflang/canonical, language-switch URL, sitemap/robots, 404; project validation (image **or** video, unsafe extension rejected), responsive variants, Arabic fallback, SSR filter + `hidden`, invalid category, detail EN/AR, unpublished → 404; contact valid/invalid/phone/honeypot/**CSRF enforced**/CSRF token flow/rate limit/redirects; admin changelist, search, filters, mark read/unread, project + hero admin pages.
- `collectstatic` with manifest storage + production-settings render of every route.
- Browser QA (headless Edge via `tools/qa_screens.py` + `tools/qa_flows.py`), EN and AR at 1440, 1280, 1024, 768, 430, 390: no console errors, no failed requests/404 assets, no horizontal overflow; mobile menu (aria-expanded, inert, focus, Esc, scroll lock); project filter by mouse and keyboard; detail pages; contact invalid (inline errors, summary focus, `aria-invalid`/`aria-describedby`, values kept) and valid (stored, success message); reduced motion (no hidden content, no Lenis/split/autoplay); JavaScript disabled (full content, server-side filter).

---

## 8. Assets to replace (all current ones are placeholders)

| Asset | Where | Replace with |
|---|---|---|
| Hero object | Admin → Site → Hero media (fallback: `static/img/hero/placeholder-object.{png,webp}`) | final transparent object render (~1600×1600) or a muted loop + poster |
| Showreel / AI video service visual | done — the reel and hero card use the first AI Video project with a video (“What Does Royal Mean?”); the services panel uses `static/video/ai-film-services.{mp4,webp}` | — |
| Service visuals | `static/img/services/{automation,web,transformation}.svg` | final artwork (4:3, dark) |
| "Who we are" visual | `static/img/brand/contours.svg` (+ label in `sections/about.html`) | studio photography or final artwork |
| Sample projects | created by `seed_demo` — remove with `python manage.py seed_demo --delete` | real case studies via the admin |
| Social image | `static/img/brand/og-default.jpg` (1200×630) | final share image |
| Icons | `static/img/brand/favicon.svg`, `apple-touch-icon.png` | final logo mark |
| Wordmark | text "MAAN LAB" in Satoshi (navbar, footer) | final logo if different |
| Email & socials | `CONTACT_EMAIL`, `SOCIAL_*` env vars | real addresses |

Fonts load from Fontshare (Satoshi) and Google Fonts (Geist; Arabic: Readex Pro). Self-host them later if you prefer no third-party requests.

---

## Video performance

High-quality masters never go on the page. Each use gets its own encode (H.264, `+faststart`, made with
ffmpeg from `pip install imageio-ffmpeg`), and a poster image always shows first:

| Use | File | Desktop / phone | Loads |
|---|---|---|---|
| Hero card, project card, reel, project cover | project **cover video** + **phone version** — 10 s silent loop, 1080p / 960px | ~2.8 MB / ~0.9 MB | after page load once on screen (hero), on hover, or when scrolled into view |
| Services → AI Video panel | `static/video/ai-film-services{,-mobile}.mp4` — 8 s silent loop, 720p / 854px | ~1.6 MB / ~0.75 MB | when the panel is shown |
| Project page player | project **full film** + **phone version** — with sound, 1080p / 720p | ~27 MB / ~11 MB | only when the visitor presses play |

Phones (below 810px) get the phone version whenever one is uploaded (`videoSource()` in `env.js`; `<source media>` for the film player).

Nothing autoplays with reduced motion, Save-Data or 2G connections. `python manage.py add_ai_film` imports the
film project from `content/portfolio/royal-film/`. In development, `/media/` is served by a Range-aware view
(`core/media.py`) so Safari can play and seek; in production serve `/media/` from nginx or a CDN, which handle
Range requests and caching. For long films, a streaming host (Vimeo, Cloudflare Stream, Bunny) with adaptive
bitrate is the next step.

## Deploying to PythonAnywhere (free)

1. **Web tab → Add a new web app → Manual configuration → Python 3.13** (default domain `<username>.pythonanywhere.com`).
2. **Bash console:**
   ```bash
   git clone --depth 1 https://github.com/Sleman-Assaf/maanlab.git ~/maanlab
   bash ~/maanlab/deploy/pythonanywhere_setup.sh
   cd ~/maanlab && .venv/bin/python manage.py createsuperuser
   ```
   The script creates `.venv`, a private `.env` with a freshly generated secret key, migrates, loads the
   projects from `deploy/site_data.json` (first run only), compiles translations, collects static files and
   writes the WSGI file.
3. **Web tab:** Virtualenv `/home/<username>/maanlab/.venv`; Static files `/static/` → `/home/<username>/maanlab/staticfiles`
   and `/media/` → `/home/<username>/maanlab/media`; turn on **Force HTTPS**; **Reload**.

Paths use your username exactly as written (`/home/Sleman159/…` — Linux paths are case-sensitive); the domain is
lowercase. Update later with `cd ~/maanlab && git pull && bash deploy/pythonanywhere_setup.sh`. Free accounts must
press "Run until 1 month from today" on the Web tab once a month, or the site is switched off.

## Notes

- **Translations**: interface strings use `{% translate %}`/`gettext`. The Arabic catalog is built from `locale_src/translations_ar.py`: `python tools/extract_strings.py && python manage.py compile_translations` (works without GNU gettext; `makemessages`/`compilemessages` also work if gettext is installed).
- **Dev tools** in `tools/` need extras not in `requirements.txt`: `numpy`, `imageio-ffmpeg` (asset generation) and `playwright` (browser QA).
