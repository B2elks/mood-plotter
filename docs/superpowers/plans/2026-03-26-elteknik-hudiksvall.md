# Elteknik Hudiksvall Website — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy a 20-page static website for Elteknik Hudiksvall AB that generates phone calls to Thomas Jonsson (070 441 41 51).

**Architecture:** Python build script (`build.py`) renders page content into a shared base template, outputs complete HTML to `site/`. No pip dependencies. Deploy via rsync to skyttberg.nu where nginx serves static files.

**Tech Stack:** HTML, CSS, vanilla JS, Python 3 (build script), nginx, certbot

**Spec:** `docs/superpowers/specs/2026-03-26-elteknik-hudiksvall-design.md`

**Project location:** `/Users/b2/Documents/Proj/LLM/elteknik-hudiksvall/`

---

## File Map

```
elteknik-hudiksvall/
├── build.py                          # Template engine — renders pages/ into site/
├── deploy.sh                         # rsync to server
├── templates/
│   └── base.html                     # Shared layout: nav, footer, CTA band, schema
├── pages/
│   ├── index.html                    # Homepage content
│   ├── tjanster/
│   │   ├── index.html                # Services overview
│   │   ├── elinstallation.html       # Individual service pages
│   │   ├── laddbox.html
│   │   ├── solceller.html
│   │   ├── elcentral.html
│   │   ├── felsokning.html
│   │   ├── belysning.html
│   │   ├── smart-hem.html
│   │   ├── industri.html
│   │   └── elbesiktning.html
│   ├── om-oss.html
│   ├── kontakt.html
│   └── kunskapsbank/
│       ├── index.html                # Article listing
│       ├── nar-behover-du-elektriker.html
│       ├── byta-elcentral.html
│       ├── installera-laddbox.html
│       ├── elsakerhet-hemma.html
│       ├── solceller-halsingland.html
│       └── renovera-gammalt-hus-el.html
├── static/
│   ├── css/style.css                 # All styles
│   ├── js/main.js                    # Mobile menu toggle
│   └── favicon.ico                   # Simple favicon
├── site/                             # BUILD OUTPUT — generated, not edited
│   ├── index.html
│   ├── css/style.css
│   ├── js/main.js
│   ├── robots.txt
│   ├── sitemap.xml
│   └── ... (all rendered pages)
└── seo/
    ├── robots.txt                    # Copied to site/ on build
    └── sitemap.xml                   # Copied to site/ on build
```

---

### Task 1: Project Setup + Build System

**Files:**
- Create: `elteknik-hudiksvall/build.py`
- Create: `elteknik-hudiksvall/templates/base.html`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p /Users/b2/Documents/Proj/LLM/elteknik-hudiksvall/{templates,pages/{tjanster,kunskapsbank},static/{css,js},seo,site}
```

- [ ] **Step 2: Create build.py**

Create `elteknik-hudiksvall/build.py`:
```python
#!/usr/bin/env python3
"""
Build script for Elteknik Hudiksvall website.
Renders page content files into the base template and outputs to site/.
No dependencies — pure Python.
"""
import os
import shutil
import re
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
TEMPLATES_DIR = PROJECT_DIR / "templates"
PAGES_DIR = PROJECT_DIR / "pages"
STATIC_DIR = PROJECT_DIR / "static"
SEO_DIR = PROJECT_DIR / "seo"
SITE_DIR = PROJECT_DIR / "site"

def read_file(path):
    return path.read_text(encoding="utf-8")

def extract_meta(content):
    """Extract <!-- meta: key=value --> comments from page content."""
    meta = {}
    for match in re.finditer(r'<!--\s*meta:\s*(\w+)=(.*?)\s*-->', content):
        meta[match.group(1)] = match.group(2).strip()
    # Remove meta comments from content
    clean = re.sub(r'<!--\s*meta:\s*\w+=.*?\s*-->\n?', '', content)
    return meta, clean

def render_page(template, content, meta):
    """Replace {{placeholders}} in template with content and meta values."""
    result = template
    result = result.replace("{{content}}", content)
    for key, value in meta.items():
        result = result.replace("{{" + key + "}}", value)
    # Remove any unreplaced placeholders
    result = re.sub(r'\{\{(\w+)\}\}', '', result)
    return result

def get_output_path(page_path):
    """Convert pages/foo/bar.html → site/foo/bar/index.html"""
    rel = page_path.relative_to(PAGES_DIR)
    if rel.name == "index.html":
        return SITE_DIR / rel
    else:
        # foo.html → foo/index.html
        return SITE_DIR / rel.with_suffix('') / "index.html"

def build():
    # Clean site dir
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir()

    # Read base template
    template = read_file(TEMPLATES_DIR / "base.html")

    # Render all pages
    page_count = 0
    for page_path in sorted(PAGES_DIR.rglob("*.html")):
        content = read_file(page_path)
        meta, clean_content = extract_meta(content)
        rendered = render_page(template, clean_content, meta)

        output_path = get_output_path(page_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        page_count += 1
        print(f"  Built: {output_path.relative_to(SITE_DIR)}")

    # Copy static files
    if STATIC_DIR.exists():
        for item in STATIC_DIR.iterdir():
            dest = SITE_DIR / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        print(f"  Copied static files")

    # Copy SEO files
    if SEO_DIR.exists():
        for item in SEO_DIR.iterdir():
            shutil.copy2(item, SITE_DIR / item.name)
        print(f"  Copied SEO files")

    print(f"\nDone! Built {page_count} pages → site/")

if __name__ == "__main__":
    build()
```

- [ ] **Step 3: Create base template**

Create `elteknik-hudiksvall/templates/base.html`:
```html
<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}} | Elteknik Hudiksvall — Elektriker i Hälsingland</title>
    <meta name="description" content="{{description}}">
    <link rel="canonical" href="https://elteknikihudiksvall.se{{canonical}}">

    <!-- Open Graph -->
    <meta property="og:title" content="{{title}} | Elteknik Hudiksvall">
    <meta property="og:description" content="{{description}}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://elteknikihudiksvall.se{{canonical}}">
    <meta property="og:locale" content="sv_SE">

    <link rel="stylesheet" href="/css/style.css">
    <link rel="icon" href="/favicon.ico">

    <!-- LocalBusiness Schema -->
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Electrician",
        "name": "Elteknik Hudiksvall AB",
        "telephone": "+46704414151",
        "image": "",
        "url": "https://elteknikihudiksvall.se",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "Larsvägen 2",
            "addressLocality": "Hudiksvall",
            "postalCode": "824 34",
            "addressCountry": "SE"
        },
        "geo": {
            "@type": "GeoCoordinates",
            "latitude": "61.7282",
            "longitude": "17.1056"
        },
        "areaServed": [
            {"@type": "City", "name": "Hudiksvall"},
            {"@type": "City", "name": "Iggesund"},
            {"@type": "City", "name": "Delsbo"},
            {"@type": "City", "name": "Bergsjö"},
            {"@type": "City", "name": "Nordanstig"}
        ],
        "priceRange": "$$",
        "openingHoursSpecification": {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"],
            "opens": "07:00",
            "closes": "17:00"
        }
    }
    </script>

    {{schema}}
</head>
<body>

    <nav class="nav" id="nav">
        <a href="/" class="nav-logo">ELTEKNIK HUDIKSVALL</a>
        <button class="nav-toggle" id="nav-toggle" aria-label="Meny">
            <span></span><span></span><span></span>
        </button>
        <div class="nav-links" id="nav-links">
            <a href="/tjanster/">TJÄNSTER</a>
            <a href="/om-oss/">OM OSS</a>
            <a href="/kunskapsbank/">KUNSKAPSBANK</a>
            <a href="/kontakt/">KONTAKT</a>
        </div>
        <a href="tel:+46704414151" class="nav-cta">RING 070 441 41 51</a>
    </nav>

    <main>
        {{content}}
    </main>

    <section class="cta-band">
        <h2>Behöver du en elektriker?</h2>
        <p>Ring för en kostnadsfri offert. Vi återkommer samma dag.</p>
        <a href="tel:+46704414151" class="cta-phone">070 441 41 51</a>
        <div class="cta-name">THOMAS JONSSON</div>
    </section>

    <footer class="footer">
        <div class="footer-inner">
            <div class="footer-col">
                <div class="footer-logo">ELTEKNIK HUDIKSVALL</div>
                <p>Auktoriserad elfirma i Hälsingland.<br>Personlig service sedan 2020.</p>
            </div>
            <div class="footer-col">
                <h4>TJÄNSTER</h4>
                <a href="/tjanster/elinstallation/">Elinstallation</a>
                <a href="/tjanster/laddbox/">Laddbox</a>
                <a href="/tjanster/solceller/">Solceller</a>
                <a href="/tjanster/elcentral/">Elcentral</a>
                <a href="/tjanster/felsokning/">Felsökning</a>
            </div>
            <div class="footer-col">
                <h4>MER</h4>
                <a href="/tjanster/belysning/">Belysning</a>
                <a href="/tjanster/smart-hem/">Smart hem</a>
                <a href="/tjanster/industri/">Industri</a>
                <a href="/tjanster/elbesiktning/">Elbesiktning</a>
                <a href="/kunskapsbank/">Kunskapsbank</a>
            </div>
            <div class="footer-col">
                <h4>KONTAKT</h4>
                <a href="tel:+46704414151">070 441 41 51</a>
                <p>Thomas Jonsson</p>
                <p>Larsvägen 2<br>824 34 Hudiksvall</p>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; 2026 Elteknik Hudiksvall AB</p>
        </div>
    </footer>

    <script src="/js/main.js"></script>
</body>
</html>
```

- [ ] **Step 4: Create placeholder page to test build**

Create `elteknik-hudiksvall/pages/index.html`:
```html
<!-- meta: title=Elektriker i Hudiksvall -->
<!-- meta: description=Elteknik Hudiksvall AB — auktoriserad elfirma i Hälsingland. Ring Thomas Jonsson 070 441 41 51 för fri offert. -->
<!-- meta: canonical=/ -->

<section class="hero">
    <div class="hero-inner">
        <div class="hero-tag">AUKTORISERAD ELFIRMA I HÄLSINGLAND</div>
        <h1>ELTEKNIK HUDIKSVALL</h1>
        <div class="hero-line"></div>
        <p class="hero-sub">Personlig service och lösningsfokuserad elinstallation<br>för villa, företag och industri i Hudiksvall med omnejd.</p>
        <a href="tel:+46704414151" class="hero-phone">070 441 41 51</a>
        <div class="hero-phone-label">RING THOMAS FÖR FRI OFFERT</div>
    </div>
</section>

<p style="padding:100px 48px; text-align:center; color:#555;">Fler sektioner kommer...</p>
```

- [ ] **Step 5: Create minimal CSS and JS**

Create `elteknik-hudiksvall/static/css/style.css`:
```css
/* Temporary minimal styles for build test */
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #0c0c0c; color: #e0e0e0; font-family: Georgia, serif; }
```

Create `elteknik-hudiksvall/static/js/main.js`:
```javascript
// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    var toggle = document.getElementById('nav-toggle');
    var links = document.getElementById('nav-links');
    if (toggle && links) {
        toggle.addEventListener('click', function() {
            links.classList.toggle('open');
            toggle.classList.toggle('open');
        });
    }
});
```

- [ ] **Step 6: Test build**

```bash
cd /Users/b2/Documents/Proj/LLM/elteknik-hudiksvall && python3 build.py
```
Expected: `Done! Built 1 pages → site/`

Verify: `cat site/index.html | head -5` should show rendered HTML with title filled in.

- [ ] **Step 7: Init git and commit**

```bash
cd /Users/b2/Documents/Proj/LLM/elteknik-hudiksvall
git init
cat > .gitignore << 'EOF'
site/
__pycache__/
.DS_Store
EOF
git add -A
git commit -m "feat: project setup with build system and base template"
```

---

### Task 2: Complete CSS Stylesheet

**Files:**
- Create: `elteknik-hudiksvall/static/css/style.css` (replace minimal version)

- [ ] **Step 1: Write the full stylesheet**

Replace `elteknik-hudiksvall/static/css/style.css` with a complete dark minimalist stylesheet. The design is pure black-and-white — no accent colors. The reference mockup is at `.superpowers/brainstorm/3180-1774517488/homepage-layout.html`.

**Design system values:**
- Background: `#0c0c0c`, Text: `#e0e0e0`, Secondary: `#555`, Borders: `#1a1a1a`, Hover: `#333`, CTA-bg: `#111`
- Font: `Georgia, 'Times New Roman', serif`, weight `300`, headings letter-spacing `2-4px`
- Labels: `11-13px`, uppercase, letter-spacing `3-5px`, color `#555`
- Sections: `80-100px` vertical padding, max-width `1100px` centered
- Line-height: `1.6-1.8`

**Required components (write full CSS for each):**

1. **Reset + base** — box-sizing, body bg/color/font, a tags, html smooth-scroll
2. **Nav** — `.nav` fixed top, transparent-black bg with backdrop-filter, `.nav-logo` left, `.nav-links` center with `gap:32px`, `.nav-cta` bordered button right, `.nav-toggle` hamburger (hidden desktop, 3 spans for hamburger icon)
3. **Hero** — `.hero` full viewport height, flex centered, `.hero-tag` small uppercase, `h1` ~48-52px weight 300, `.hero-line` 50px × 1px, `.hero-sub` max-width 500px, `.hero-phone` large bordered CTA, `.hero-phone-label` small muted
4. **Sections** — `.section` padding 80-100px, `.section-label` small uppercase, `.section-title` ~32px weight 300, `.divider` 30px line
5. **Service cards** — `.services-grid` CSS grid 3 columns gap 32px, `.service-card` border `#1a1a1a`, padding 32px, hover border `#333`, `h3` 16px uppercase
6. **USP** — `.usp-grid` 3 columns centered, `.usp-number` large 48px, `.usp-label` small uppercase
7. **CTA band** — `.cta-band` bg `#111`, centered, `.cta-phone` 28-32px, `.cta-name` small muted
8. **Article cards** — `.articles-grid` 3 columns, `.article-card` border, `.article-img` placeholder bg `#151515`, `.article-body` padding
9. **Service page** — `.service-page` max-width 800px, `.service-list` styled bullets, `.faq details` with summary styled, border-bottom
10. **Article page** — `.article-page` max-width 750px centered, `h2/h3` styling, `.takeaway-box` border-left accent, `.related-articles` links
11. **Knowledge base** — article listing grid
12. **Contact page** — `.contact-info` large phone, address block
13. **Footer** — `.footer` border-top `#1a1a1a`, `.footer-inner` 4-column grid, `.footer-col h4` small uppercase, links styled, `.footer-bottom` centered small
14. **Responsive** — `@media (max-width: 768px)`: single columns, nav hamburger visible, `.nav-links` vertical slide-down, hero text smaller. `@media (max-width: 480px)`: further size reductions, padding reduction

Write the complete CSS — every selector, every property. No placeholders.

- [ ] **Step 2: Rebuild and verify in browser**

```bash
cd /Users/b2/Documents/Proj/LLM/elteknik-hudiksvall && python3 build.py
```

Open `site/index.html` in browser — verify dark background, serif font, hero styling.

- [ ] **Step 3: Commit**

```bash
git add static/css/style.css
git commit -m "feat: complete dark minimalist stylesheet"
```

---

### Task 3: Homepage

**Files:**
- Modify: `elteknik-hudiksvall/pages/index.html` (replace placeholder)

- [ ] **Step 1: Write complete homepage content**

Replace `elteknik-hudiksvall/pages/index.html` with full homepage:
1. Hero — tagline, company name, subtitle, phone CTA
2. Services grid — 6 featured services (elinstallation, laddbox, solceller, elcentral, felsökning, industri) with SVG line icons, one-line descriptions, links to `/tjanster/[slug]/`
3. USP section — "5+ Års erfarenhet", "100% Auktoriserad", "Alltid personlig service"
4. Kunskapsbank preview — 3 article cards linking to actual article pages

- [ ] **Step 2: Build and verify**

```bash
python3 build.py
```
Open `site/index.html` — verify all sections render, links point correctly, CTA band appears.

- [ ] **Step 3: Commit**

```bash
git add pages/index.html
git commit -m "feat: complete homepage with hero, services, USP, and article preview"
```

---

### Task 4: All 9 Service Pages + Services Index

**Files:**
- Create: `elteknik-hudiksvall/pages/tjanster/index.html`
- Create: `elteknik-hudiksvall/pages/tjanster/elinstallation.html`
- Create: `elteknik-hudiksvall/pages/tjanster/laddbox.html`
- Create: `elteknik-hudiksvall/pages/tjanster/solceller.html`
- Create: `elteknik-hudiksvall/pages/tjanster/elcentral.html`
- Create: `elteknik-hudiksvall/pages/tjanster/felsokning.html`
- Create: `elteknik-hudiksvall/pages/tjanster/belysning.html`
- Create: `elteknik-hudiksvall/pages/tjanster/smart-hem.html`
- Create: `elteknik-hudiksvall/pages/tjanster/industri.html`
- Create: `elteknik-hudiksvall/pages/tjanster/elbesiktning.html`

Each service page follows the same structure:
1. Meta comments (title, description, canonical with "[Service] i Hudiksvall" pattern)
2. H1: "[Service] i Hudiksvall"
3. Intro paragraph with location keywords (Hudiksvall, Hälsingland, nearby towns)
4. "Vad vi gör" — 3-5 bullet points
5. "Varför välja oss" — personal service, authorized, insured
6. FAQ section — 2-3 questions with `<details>` elements
7. FAQ schema markup as inline `<script type="application/ld+json">` block in the page content (this lands inside `{{content}}` in the template — no build.py changes needed). Same approach for BreadcrumbList on every subpage — add a `<script type="application/ld+json">` block at the bottom of each page's content

The services index (`/tjanster/`) lists all 9 services as a grid with links.

- [ ] **Step 1: Write services index page**

- [ ] **Step 2: Write elinstallation service page (template for others)**

- [ ] **Step 3: Write remaining 8 service pages**

Each page has unique content — not copy-paste. Different FAQ questions, different bullet points, different intro text with varied keyword usage.

- [ ] **Step 4: Build and verify**

```bash
python3 build.py
```
Expected: 12 pages built (1 homepage + 1 services index + 9 service pages + 1 placeholder from earlier tasks).
Verify: Open several service pages, check H1 tags, FAQ sections, internal links.

- [ ] **Step 5: Commit**

```bash
git add pages/tjanster/
git commit -m "feat: all 9 service pages with SEO-optimized content and FAQ schemas"
```

---

### Task 5: About + Contact Pages

**Files:**
- Create: `elteknik-hudiksvall/pages/om-oss.html`
- Create: `elteknik-hudiksvall/pages/kontakt.html`

- [ ] **Step 1: Write Om oss page**

Content:
1. H1: "Om Elteknik Hudiksvall"
2. Company story — founded 2020, local Hudiksvall
3. Thomas Jonsson — personal intro, passion for electrical work
4. Values — personlig service, kompetent personal, lösningsfokuserade
5. Service area — Hudiksvall, Iggesund, Delsbo, Bergsjö, Nordanstig, hela Hälsingland
6. BreadcrumbList schema

- [ ] **Step 2: Write Kontakt page**

Content:
1. H1: "Kontakta Elteknik Hudiksvall"
2. Phone number (large, linked with tel:)
3. Thomas Jonsson
4. Address: Larsvägen 2, 824 34 Hudiksvall
5. Link to Google Maps
6. Service area list
7. Opening hours mention

- [ ] **Step 3: Build and verify**

```bash
python3 build.py
```

- [ ] **Step 4: Commit**

```bash
git add pages/om-oss.html pages/kontakt.html
git commit -m "feat: about and contact pages"
```

---

### Task 6: Knowledge Base — 6 Articles

**Files:**
- Create: `elteknik-hudiksvall/pages/kunskapsbank/index.html`
- Create: `elteknik-hudiksvall/pages/kunskapsbank/nar-behover-du-elektriker.html`
- Create: `elteknik-hudiksvall/pages/kunskapsbank/byta-elcentral.html`
- Create: `elteknik-hudiksvall/pages/kunskapsbank/installera-laddbox.html`
- Create: `elteknik-hudiksvall/pages/kunskapsbank/elsakerhet-hemma.html`
- Create: `elteknik-hudiksvall/pages/kunskapsbank/solceller-halsingland.html`
- Create: `elteknik-hudiksvall/pages/kunskapsbank/renovera-gammalt-hus-el.html`

- [ ] **Step 1: Write kunskapsbank index page**

Lists all 6 articles as cards with title, short description, and link.

- [ ] **Step 2: Write Article 1 — "När behöver du anlita en elektriker?"**

600-1000 words. Sections:
- Intro: the short answer is almost always
- Swedish law and Elsäkerhetsverket rules
- Insurance implications (hemförsäkring gäller inte vid oauktoriserat elarbete)
- Safety risks (brand, elchock)
- What you CAN do yourself (byta glödlampa, basically)
- Key takeaway box
- CTA: Ring Thomas
- Related articles links
- Article schema markup (JSON-LD)

- [ ] **Step 3: Write Article 2 — "Byta elcentral — tecken på att det är dags"**

600-1000 words. Warning signs, modern panel benefits, the process, ROT-avdrag concept.

- [ ] **Step 4: Write Article 3 — "Installera laddbox hemma — vad du bör veta"**

600-1000 words. Why dedicated charger, grönt teknikavdrag concept, fuse capacity, authorized requirement.

- [ ] **Step 5: Write Article 4 — "Elsäkerhet hemma — en checklista"**

600-1000 words. Fire statistics, RCD check, old wiring, overloaded outlets, winter in Hälsingland.

- [ ] **Step 6: Write Article 5 — "Solceller i Hälsingland — lönar det sig?"**

600-1000 words. Sun hours (more than people think), how it works, grid connection, authorized installation.

- [ ] **Step 7: Write Article 6 — "Renovera gammalt hus i Hälsingland — elen du inte får glömma"**

600-1000 words. Old Hälsingland houses, aluminum wiring, ungrounded outlets, undersized panels, heritage considerations.

- [ ] **Step 8: Build and verify**

```bash
python3 build.py
```
Expected: 7 kunskapsbank pages built. Verify article content, related links, schema markup.

- [ ] **Step 9: Commit**

```bash
git add pages/kunskapsbank/
git commit -m "feat: knowledge base with 6 SEO-optimized articles"
```

---

### Task 7: SEO Files + Final Polish

**Files:**
- Create: `elteknik-hudiksvall/seo/robots.txt`
- Create: `elteknik-hudiksvall/seo/sitemap.xml`
- Create: `elteknik-hudiksvall/static/favicon.ico`
- Modify: `elteknik-hudiksvall/build.py` (if needed for BreadcrumbList on subpages)

- [ ] **Step 1: Create robots.txt**

Create `elteknik-hudiksvall/seo/robots.txt`:
```
User-agent: *
Allow: /
Sitemap: https://elteknikihudiksvall.se/sitemap.xml
```

- [ ] **Step 2: Create sitemap.xml**

Create `elteknik-hudiksvall/seo/sitemap.xml` with all 20 page URLs, `lastmod` date, `priority` (1.0 for home, 0.9 for services, 0.8 for articles, 0.7 for others).

- [ ] **Step 3: Create favicon**

Generate a minimal favicon — a simple "E" or lightning bolt in white on dark background. Can be a small 32x32 PNG converted to .ico, or use a data URI.

- [ ] **Step 4: Verify BreadcrumbList schema on subpages**

Every subpage should already have a BreadcrumbList `<script type="application/ld+json">` block in its page content (added in Tasks 4, 5, 6). Spot-check a service page, an article page, and the contact page to verify the breadcrumbs are correct. The `{{schema}}` placeholder in `base.html` can be removed since all per-page schema is inline in content.

- [ ] **Step 5: Verify all meta tags, Open Graph, and schema**

Run build, then for each page verify:
- `<title>` is unique and follows the "[Page] | Elteknik Hudiksvall — Elektriker i Hälsingland" pattern
- `<meta name="description">` is unique and includes phone/location
- Schema markup is valid (spot-check with https://validator.schema.org/)
- Canonical URLs are correct

- [ ] **Step 6: Full build and link check**

```bash
python3 build.py
```

Check all internal links work:
```bash
grep -roh 'href="[^"]*"' site/ | sort -u
```
Verify no broken links.

- [ ] **Step 7: Commit**

```bash
git add seo/ static/favicon.ico
git commit -m "feat: SEO files — robots.txt, sitemap.xml, favicon, schema markup"
```

---

### Task 8: Deploy to Server

**Files:**
- Create: `elteknik-hudiksvall/deploy.sh`
- Create: nginx config on server

- [ ] **Step 1: Create deploy script**

Create `elteknik-hudiksvall/deploy.sh`:
```bash
#!/bin/bash
set -e

echo "Building site..."
python3 build.py

echo "Ensuring target directory exists..."
ssh kumamonwithme@skyttberg.nu "mkdir -p /home/kumamonwithme/elteknik-hudiksvall"

echo "Deploying to skyttberg.nu..."
rsync -avz --delete site/ kumamonwithme@skyttberg.nu:/home/kumamonwithme/elteknik-hudiksvall/

echo "Done! Site deployed."
```

```bash
chmod +x deploy.sh
```

- [ ] **Step 2: Create nginx config on server**

```bash
ssh kumamonwithme@skyttberg.nu "sudo tee /etc/nginx/sites-available/elteknik-hudiksvall << 'EOF'
server {
    listen 80;
    server_name elteknikihudiksvall.se www.elteknikihudiksvall.se;

    root /home/kumamonwithme/elteknik-hudiksvall;
    index index.html;

    location / {
        try_files \$uri \$uri/ =404;
    }

    # Gzip compression
    gzip on;
    gzip_types text/html text/css application/javascript text/xml application/xml;
    gzip_min_length 256;

    # Cache static assets
    location ~* \.(css|js|ico|png|jpg|jpeg|svg|woff2)$ {
        expires 30d;
        add_header Cache-Control \"public, immutable\";
    }

    # Security headers
    add_header X-Frame-Options \"SAMEORIGIN\" always;
    add_header X-Content-Type-Options \"nosniff\" always;
    add_header Referrer-Policy \"strict-origin-when-cross-origin\" always;
}
EOF"
```

- [ ] **Step 3: Enable site and reload nginx**

```bash
ssh kumamonwithme@skyttberg.nu "sudo ln -sf /etc/nginx/sites-available/elteknik-hudiksvall /etc/nginx/sites-enabled/ && sudo nginx -t && sudo systemctl reload nginx"
```

- [ ] **Step 4: Deploy the site**

```bash
cd /Users/b2/Documents/Proj/LLM/elteknik-hudiksvall && ./deploy.sh
```

- [ ] **Step 5: Set up SSL with certbot (once DNS propagates)**

```bash
ssh kumamonwithme@skyttberg.nu "sudo certbot --nginx -d elteknikihudiksvall.se -d www.elteknikihudiksvall.se --non-interactive --agree-tos -m kumamonwithme@skyttberg.nu"
```

If DNS hasn't propagated yet, skip this step and run it later.

- [ ] **Step 6: Verify live site**

```bash
curl -sI http://elteknikihudiksvall.se | head -10
```

Or if DNS isn't ready, test via IP:
```bash
curl -sH "Host: elteknikihudiksvall.se" http://77.42.91.173/ | head -20
```

- [ ] **Step 7: Commit deploy script**

```bash
git add deploy.sh
git commit -m "feat: deploy script and server configuration"
```
