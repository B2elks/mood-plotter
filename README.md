# mood-plotter

PIR-triggad butler-uppringning som plottar mood-kort med AxiDraw.

Se `docs/superpowers/specs/2026-05-09-pir-mood-plotter-design.md` för fullständig design.

## Setup
1. Kopiera `.env.example` → `.env` och fyll i värden
2. `pip install -r server/requirements.txt` (server)
3. `pip install -r pi/requirements.txt` (Pi)
4. `python server/generate_questions.py` (engångskörning)
5. Starta server- och pi-tjänsten via systemd
