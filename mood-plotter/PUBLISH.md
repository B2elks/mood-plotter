# Publicera mood-plotter som eget repo

Projektet ligger nu på branchen `mood-plotter` i worktreet
`/Users/b2/Documents/Proj/LLM/.worktrees/mood-plotter/` som en undermapp i
LLM-monorepot. När det är dags att gå live ska det extraheras till ett eget
git-repo, t.ex. under `b2elk/mood-plotter` eller `46elks/mood-plotter`.

## Förslag på namn

- `b2elk/mood-plotter` (ditt namespace)
- `46elks/mood-plotter` (om det ska in under 46elks-org-en — kolla med 46elks
  om de vill ha den som showcase, annars ditt eget)
- `b2elk/elkplotter-mood` (markerar ursprung tydligare)

Originalprojektet `46elks/elkplotter` har MIT/BSD-license — kolla `LICENSE.txt`
i originalrepot innan du publicerar din variant. Om du forkar via GitHub:s
fork-funktion får du license-arvet automatiskt; om du gör fresh repo behöver
du bevara upphovsmännens copyright-rad.

## Steg-för-steg när du är redo

### 1. Skapa GitHub-repot

```bash
# T.ex. via gh CLI
gh repo create b2elk/mood-plotter --public --description \
  "PIR-triggad butler-uppringning som plottar mood-kort med AxiDraw"
```

Eller via webben på <https://github.com/new>.

### 2. Kopiera projekt-undermappen till ny plats

```bash
# Kopiera hela mood-plotter/-undermappen som rotnivå för det nya repot
cp -r /Users/b2/Documents/Proj/LLM/.worktrees/mood-plotter/mood-plotter \
      ~/Documents/Proj/LLM/b2elk-mood-plotter

cd ~/Documents/Proj/LLM/b2elk-mood-plotter
```

### 3. Initialisera git och commita

```bash
git init
git add .
git commit -m "Initial commit — fork of 46elks/elkplotter as PIR-triggered mood plotter

Replaces SMS-in trigger with PIR sensor on Raspberry Pi. PIR triggers
outbound call where a butler asks how the user feels; answer steers
both a butler ack phrase and a DALL·E-generated mood card that plots
on the AxiDraw.

Original: https://github.com/46elks/elkplotter"

git branch -M main
git remote add origin git@github.com:b2elk/mood-plotter.git
git push -u origin main
```

### 4. Bevara historiken (alternativ)

Om du vill behålla de 17 commits-stegvisa historian (TDD-cykler, fix-deps,
post-review-fix etc.), använd `git filter-repo` istället för en squash:

```bash
# Behöver pip install git-filter-repo
cd /tmp
git clone --no-local /Users/b2/Documents/Proj/LLM/.worktrees/mood-plotter mood-plotter-extract
cd mood-plotter-extract
git checkout mood-plotter
git filter-repo --subdirectory-filter mood-plotter
git remote add origin git@github.com:b2elk/mood-plotter.git
git push -u origin mood-plotter:main
```

Detta bevarar alla 17 commits men flyttar `mood-plotter/`-undermappen till
rotnivå.

### 5. Lägg till LICENSE och CREDITS

Kopiera in MIT-license med din copyright + behåll attributering till 46elks
om du forkar:

```
LICENSE.txt
---
MIT License

Copyright (c) 2026 Björn Skyttberg
Original work: Copyright (c) 46elks AB

Permission is hereby granted, free of charge, ...
[standard MIT-text]
```

### 6. Städa worktreet (efter publicering)

När det nya repot är på GitHub kan worktreet i LLM-monorepot tas bort:

```bash
cd /Users/b2/Documents/Proj/LLM
git worktree remove .worktrees/mood-plotter
git branch -D mood-plotter
```

`docs/superpowers/specs/2026-05-09-pir-mood-plotter-design.md` och
`docs/superpowers/plans/2026-05-09-pir-mood-plotter.md` ligger kvar på `main`
i monorepot. Antingen lämna kvar dem som referens, eller flytta in i nya
repots `docs/`-mapp.

## Innan du publicerar

Gå igenom `TODO.md` — minst punkt 1 (signaturkontroll på 46elks-webhooks) bör
vara fixad innan repot är publikt och servern är live, eftersom URL:en kan
hittas och utnyttjas.

Säkerställ att `.env` INTE är med (`.gitignore` sköter det redan, men dubbelkolla).

## Setup på server och Pi

Se `README.md` för detaljerade setup-anvisningar.

Kort: deploya till `skyttberg.nu` under `moodplotter.skyttberg.nu`-subdomän,
plus en Raspberry Pi med PIR + AxiDraw vid skrivbordet.

## Smoke-test innan live

Med `DRY_RUN=true` i serverns env:

```bash
curl -X POST https://moodplotter.skyttberg.nu/trigger \
  -H "Authorization: Bearer $PI_TOKEN" \
  -d '{"pi_id":"desk1"}'
```

Ska ge 200 + JSON med `call_id` och `dry_run: true`. Inga riktiga samtal.

Stäng av DRY_RUN, trigga manuellt en gång till — telefonen ska ringa, butlern
fråga, AxiDraw börja rita.
