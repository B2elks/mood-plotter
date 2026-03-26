# Elteknik Hudiksvall AB — Website Design Specification

## Overview

A static website for **Elteknik Hudiksvall AB**, a local authorized electrician in Hudiksvall, Hälsingland. The site's primary purpose is to generate phone calls to Thomas Jonsson (070 441 41 51) for booking electrical work.

**Domain:** elteknikihudiksvall.se
**Server:** skyttberg.nu (kumamonwithme@skyttberg.nu), nginx serving static files
**Tech:** Static HTML/CSS/JS — no frameworks, no build pipeline
**Language:** Swedish only
**Design:** Dark (near-black), minimalist, black-and-white only, serif typography

---

## 1. Business Details

- **Company:** Elteknik Hudiksvall AB
- **Contact:** Thomas Jonsson, 070 441 41 51
- **Address:** Larsvägen 2, 824 34 Hudiksvall
- **Services:** Elinstallation (villa/företag/industri), laddbox, solceller, elcentral, felsökning, belysning, smart hem, industri, elbesiktning
- **USP:** Personlig service, trevlig och kompetent personal, lösningsfokuserade
- **Target area:** Hudiksvall, Iggesund, Delsbo, Bergsjö, Nordanstig, and broader Hälsingland

---

## 2. Visual Design

### Color Palette
- **Background:** #0c0c0c (near-black)
- **Text primary:** #e0e0e0 (light gray)
- **Text secondary:** #555 (muted gray)
- **Borders:** #1a1a1a (subtle)
- **Hover borders:** #333
- **CTA band background:** #111

No accent colors. Pure black and white. Elegance through typography and spacing.

### Typography
- **Headings:** Georgia or serif fallback, font-weight 300, generous letter-spacing
- **Body text:** System serif, light weight
- **Labels:** Uppercase, small font-size (11-13px), letter-spacing 3-5px
- **No emojis in production** — service icons will be simple SVG line icons or Unicode symbols

### Spacing
- Large whitespace between sections (80-100px padding)
- Content max-width: 1100px centered
- Generous line-height (1.6-1.8)

---

## 3. Site Structure

### Pages

| Page | URL | Purpose |
|------|-----|---------|
| Startsida | `/` | Hero + services overview + CTA + article preview |
| Tjänster | `/tjanster/` | All 9 services listed with descriptions |
| Elinstallation | `/tjanster/elinstallation/` | Dedicated service page — SEO target |
| Laddbox | `/tjanster/laddbox/` | Dedicated service page — SEO target |
| Solceller | `/tjanster/solceller/` | Dedicated service page — SEO target |
| Elcentral | `/tjanster/elcentral/` | Dedicated service page — SEO target |
| Felsökning | `/tjanster/felsökning/` | Dedicated service page — SEO target |
| Belysning | `/tjanster/belysning/` | Dedicated service page — SEO target |
| Smart hem | `/tjanster/smart-hem/` | Dedicated service page — SEO target |
| Industri | `/tjanster/industri/` | Dedicated service page — SEO target |
| Elbesiktning | `/tjanster/elbesiktning/` | Dedicated service page — SEO target |
| Om oss | `/om-oss/` | About the company, Thomas, team, values |
| Kunskapsbank | `/kunskapsbank/` | Article listing page |
| Artikel 1 | `/kunskapsbank/nar-behover-du-elektriker/` | When you need an electrician |
| Artikel 2 | `/kunskapsbank/byta-elcentral/` | Replacing your electrical panel |
| Artikel 3 | `/kunskapsbank/installera-laddbox/` | Installing an EV charger |
| Artikel 4 | `/kunskapsbank/elsakerhet-hemma/` | Home electrical safety checklist |
| Artikel 5 | `/kunskapsbank/solceller-halsingland/` | Solar panels in Hälsingland |
| Artikel 6 | `/kunskapsbank/renovera-gammalt-hus-el/` | Electrical work in old houses |
| Kontakt | `/kontakt/` | Contact details, map, CTA |

**Total: ~20 pages**

### Navigation
Fixed top navbar:
- Logo: `ELTEKNIK HUDIKSVALL` (text, left)
- Links: TJÄNSTER, OM OSS, KUNSKAPSBANK, KONTAKT (center/right)
- CTA: `RING 070 441 41 51` (right, bordered button)

### Shared Elements
- **Header/Nav:** Same on all pages
- **Footer:** Company info, address, phone, links to key pages
- **CTA band:** Appears on every page — "Behöver du en elektriker?" + phone number + "Thomas Jonsson"

---

## 4. Page Layouts

### Startsida (/)
1. **Hero** — Full viewport height. Tagline "Auktoriserad elfirma i Hälsingland", company name large, subtitle about personal service, phone number as primary CTA, "Ring Thomas för fri offert"
2. **Tjänster-grid** — 6 highlight cards (3x2 grid) with icon, name, one-line description. Link to full service page.
3. **USP section** — Three numbers/stats: years of experience, authorized, customer focus
4. **CTA band** — "Behöver du en elektriker?" + phone + Thomas Jonsson
5. **Kunskapsbank preview** — 3 latest articles as cards
6. **Footer**

### Tjänstesida (/tjanster/[service]/)
Each of the 9 services gets its own page for SEO:
1. **H1:** "[Service] i Hudiksvall" (e.g., "Laddbox-installation i Hudiksvall")
2. **Intro paragraph** with local keywords (Hudiksvall, Hälsingland, nearby towns)
3. **What we do** — 3-5 bullet points of specific work
4. **Why choose us** — personal service, authorized, insured
5. **FAQ section** — 2-3 common questions with answers (schema markup for FAQ)
6. **CTA band** — Ring Thomas

### Artikelsida (/kunskapsbank/[slug]/)
1. **H1** — article title
2. **Article body** — well-structured with H2/H3 subheadings, 600-1000 words
3. **Key takeaway box** — "Det viktigaste att komma ihåg"
4. **CTA** — "Har du frågor? Ring Thomas"
5. **Related articles** — links to 2-3 other articles

### Om oss (/om-oss/)
1. About the company — founded, values, service area
2. Thomas Jonsson — brief personal intro
3. What we stand for — personal service, competence, solution-focused
4. Service area — Hudiksvall, Iggesund, Delsbo, Bergsjö, Nordanstig, Hälsingland

### Kontakt (/kontakt/)
1. Phone number (large, prominent)
2. Thomas Jonsson
3. Address with embedded map or link to Google Maps
4. Service area description

---

## 5. Article Content Strategy

All articles avoid specific prices (to stay evergreen) and always conclude with a CTA to contact Thomas. The tone is helpful and knowledgeable but drives toward professional service.

### Article 1: "När behöver du anlita en elektriker?"
- Swedish law: almost all electrical work requires authorization
- Insurance implications — work done by unqualified person voids insurance
- Safety risks — fire, electric shock
- Conclusion: always call a professional

### Article 2: "Byta elcentral — tecken på att det är dags"
- Warning signs: flickering, tripping breakers, old fuse box, burning smell
- What a modern electrical panel provides (RCD, proper circuits)
- How the process works (no prices)
- ROT-avdrag mention (concept, not amounts)

### Article 3: "Installera laddbox hemma — vad du bör veta"
- Why you need a dedicated charger (not a regular outlet)
- Grönt teknikavdrag (concept)
- Main fuse capacity considerations
- Must be done by authorized electrician

### Article 4: "Elsäkerhet hemma — en checklista"
- 1 in 3 house fires caused by electrical faults
- Check: RCD/jordfelsbrytare, old wiring, overloaded outlets
- When to call for inspection
- Seasonal tips (especially winter in Hälsingland)

### Article 5: "Solceller i Hälsingland — lönar det sig?"
- Sun hours in Hälsingland — more than people think
- How solar panels work (simplified)
- Grid connection and selling back
- Why authorized installation matters

### Article 6: "Renovera gammalt hus i Hälsingland — elen du inte får glömma"
- Old houses in Hälsingland — charming but often outdated wiring
- Common issues: aluminum wiring, ungrounded outlets, undersized panels
- What to check before renovation
- Working with heritage buildings

---

## 6. SEO & Technical

### On-page SEO
- **Title tags:** "[Service/Article] | Elteknik Hudiksvall — Elektriker i Hälsingland"
- **Meta descriptions:** Unique per page, include phone number, location keywords
- **H1:** One per page, includes primary keyword + location
- **Internal linking:** Service pages link to related articles and vice versa
- **Image alt texts:** Descriptive, include location when relevant

### Schema Markup (JSON-LD)
- **LocalBusiness** on every page: name, address, phone, opening hours, service area, geo coordinates
- **FAQ** on service pages with common questions
- **Article** on blog posts with author, date, description
- **BreadcrumbList** on all subpages

### Technical SEO
- `robots.txt` allowing all
- `sitemap.xml` with all pages
- Canonical URLs
- Open Graph tags for social sharing
- Fast loading — no JavaScript frameworks, minimal CSS, optimized images
- Mobile-responsive (CSS media queries)
- HTTPS via Let's Encrypt (certbot on skyttberg.nu)

### Local SEO Keywords
Every service page naturally includes variations of:
- "elektriker hudiksvall"
- "elfirma hudiksvall"
- "elektriker hälsingland"
- "[service] hudiksvall"
- "[service] hälsingland"
- Nearby town mentions: Iggesund, Delsbo, Bergsjö, Nordanstig

---

## 7. Deployment

### Server Setup
- **Location:** `/home/kumamonwithme/elteknik-hudiksvall/` on skyttberg.nu
- **Nginx:** Static file serving, no proxy needed
- **Domain:** elteknikihudiksvall.se → A record pointing to skyttberg.nu IP
- **SSL:** certbot for HTTPS

### Nginx Config Pattern
```
server {
    server_name elteknikihudiksvall.se www.elteknikihudiksvall.se;
    root /home/kumamonwithme/elteknik-hudiksvall;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # Certbot will add SSL config
}
```

### Deploy Process
```bash
rsync -avz --delete ./site/ kumamonwithme@skyttberg.nu:/home/kumamonwithme/elteknik-hudiksvall/
```

### File Structure on Server
```
elteknik-hudiksvall/
├── index.html
├── tjanster/
│   ├── index.html
│   ├── elinstallation/index.html
│   ├── laddbox/index.html
│   ├── solceller/index.html
│   ├── elcentral/index.html
│   ├── felsökning/index.html
│   ├── belysning/index.html
│   ├── smart-hem/index.html
│   ├── industri/index.html
│   └── elbesiktning/index.html
├── om-oss/index.html
├── kunskapsbank/
│   ├── index.html
│   ├── nar-behover-du-elektriker/index.html
│   ├── byta-elcentral/index.html
│   ├── installera-laddbox/index.html
│   ├── elsakerhet-hemma/index.html
│   ├── solceller-halsingland/index.html
│   └── renovera-gammalt-hus-el/index.html
├── kontakt/index.html
├── css/style.css
├── js/main.js          # minimal — schema injection, mobile menu toggle
├── robots.txt
├── sitemap.xml
└── favicon.ico
```

---

## 8. Build System

A simple Python script (`build.py`) to avoid duplicating header/footer across 20 HTML files:

- **Templates:** `templates/base.html` with `{{content}}`, `{{title}}`, `{{description}}` placeholders
- **Pages:** `pages/` directory with individual page content
- **Output:** `site/` directory with complete HTML files
- **No dependencies** — pure Python string replacement, no pip packages

Run: `python build.py` → outputs to `site/`
Deploy: `rsync site/ → server`

---

## 9. MVP Scope

**In:**
- All 20 pages (home, 9 service pages, about, contact, knowledge base index, 6 articles)
- Responsive design (mobile + tablet + desktop)
- Full SEO (schema, sitemap, meta tags)
- Build script for templating
- Deploy script
- Dark minimalist design (black & white)

**Out:**
- Contact form (phone is the CTA — simpler, more direct)
- Google Maps embed (link to Google Maps instead)
- Analytics (can add later)
- Cookie consent (no cookies = no consent needed)
- Multi-language
- Blog CMS / admin interface
