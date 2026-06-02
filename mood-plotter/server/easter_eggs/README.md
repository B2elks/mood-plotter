# Easter Eggs

Lägg `.svg`-filer i denna mapp. Filnamnet är trigger-ordet.

## Regler

- Lowercase a–z, 0–9, underscore
- Inga mellanslag eller specialtecken (de hanteras vid matchning)
- SVG-storlek: `100mm x 100mm` med `viewBox="0 0 100 100"` (matchar
  vanlig kort-storlek)
- Bara `stroke` — `fill="none"` — eftersom pennan ritar linjer
- Klar stroke-width runt `0.5mm` brukar bli bra

## Exempel

Fil: `marfar.svg` triggas av SMS:n `marfar`, `Marfar`, `MARFAR!`, eller
`  marfar  `.

Easter eggs visas **inte** i kiosk-galleriet och konsumerar **inte**
DALL-E-credits.
