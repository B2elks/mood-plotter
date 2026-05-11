"""HTML-mallar for galleriet och admin-vyn — klassisk 90s-look."""
import html
import time


PAGE_BG = "#fefefe"
ACCENT = "#ff00ff"
LINK_COLOR = "#0000ee"
COMIC = '"Comic Sans MS", "Chalkboard SE", cursive'


def _format_swedish_date(timestamp: float) -> str:
    """Format som '11 maj 2026 — 14:05'."""
    months = [
        "januari", "februari", "mars", "april", "maj", "juni",
        "juli", "augusti", "september", "oktober", "november", "december",
    ]
    t = time.localtime(timestamp)
    return f"{t.tm_mday} {months[t.tm_mon - 1]} {t.tm_year} — {t.tm_hour:02d}:{t.tm_min:02d}"


def _hr() -> str:
    return '<hr style="border:0;height:3px;background:repeating-linear-gradient(90deg,#ff00ff 0 10px,#00ffff 10px 20px);margin:20px 0">'


def gallery_page(cards: list, server_url: str) -> str:
    """Render galleriet. cards: list[card_store.Card]"""
    if cards:
        latest = cards[0]
        latest_url = f"/cards/{latest.png_name}"
        latest_caption = _format_swedish_date(latest.timestamp)
        latest_block = f"""
        <center>
            <h2 style="color:{ACCENT};font-family:{COMIC};font-size:38px;margin-bottom:6px;text-shadow:3px 3px 0 #00ffff">Senaste kortet</h2>
            <table border="6" cellpadding="14" cellspacing="0" style="border-color:#000080;background:#ffff66">
                <tr><td align="center">
                    <img src="{html.escape(latest_url)}" alt="senaste mood-kort" style="max-width:520px;border:3px ridge #888;background:white">
                </td></tr>
                <tr><td align="center" style="font-family:{COMIC};color:#000080;font-size:18px">
                    🕰️ <em>{html.escape(latest_caption)}</em>
                </td></tr>
            </table>
        </center>
        """
        thumbs = ""
        for c in cards[1:25]:
            thumb_url = f"/cards/{c.png_name}"
            svg_url = f"/cards/{c.svg_name}"
            caption = _format_swedish_date(c.timestamp)
            thumbs += f"""
            <td align="center" style="padding:10px;background:#ccffff;border:2px outset #aaaaff;font-family:{COMIC};font-size:11px">
                <a href="{html.escape(svg_url)}" target="_blank"><img src="{html.escape(thumb_url)}" alt="kort" width="180" style="border:2px solid #000080;background:white;display:block;margin-bottom:6px"></a>
                <span style="color:#000080">{html.escape(caption)}</span><br>
                <a href="{html.escape(svg_url)}" style="color:{LINK_COLOR};font-size:10px">SVG</a>
            </td>
            """
        # split into rows of 4
        thumb_cells = thumbs.split("</td>")
        rows = ""
        per_row = 4
        cells = [c + "</td>" for c in thumb_cells if c.strip()]
        for i in range(0, len(cells), per_row):
            rows += "<tr>" + "".join(cells[i:i + per_row]) + "</tr>"

        older_block = "" if not rows else f"""
        <center>
            <h3 style="color:#008000;font-family:{COMIC};font-size:26px">Tidigare kort 📜</h3>
            <table border="0" cellpadding="0" cellspacing="6" style="background:#ddeeff;border:3px ridge #000080;padding:10px">
                {rows}
            </table>
        </center>
        """
    else:
        latest_block = f"""
        <center>
            <p style="font-family:{COMIC};font-size:22px;color:#000080">
                🎩 Inga kort har skapats ännu. Stå by, min herre... 🎩
            </p>
        </center>
        """
        older_block = ""

    body = f"""
<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8">
<title>STÄMNINGS-MASKINEN ✨</title>
<style>
body {{
    background: {PAGE_BG};
    background-image: radial-gradient(#ff00ff 1px, transparent 2px), radial-gradient(#00ffff 1px, transparent 2px);
    background-size: 40px 40px, 40px 40px;
    background-position: 0 0, 20px 20px;
    font-family: {COMIC};
    color: #000080;
    margin: 0;
    padding: 0;
}}
.banner {{
    background: linear-gradient(90deg, #ff00ff, #00ffff, #ffff00, #ff00ff);
    color: white;
    text-align: center;
    padding: 22px;
    border-bottom: 4px double #000080;
    text-shadow: 2px 2px 0 #000080;
}}
.banner h1 {{
    font-size: 52px;
    margin: 0;
    letter-spacing: 4px;
}}
.banner .tag {{
    font-size: 18px;
    color: #ffffaa;
    text-shadow: 1px 1px 0 #000080;
}}
marquee {{
    background: #ffff00;
    color: #c00000;
    font-weight: bold;
    border-top: 2px ridge #000080;
    border-bottom: 2px ridge #000080;
    padding: 6px 0;
    font-size: 17px;
}}
footer {{
    text-align: center;
    padding: 22px;
    color: #000080;
    font-size: 13px;
}}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
.blink {{ animation: blink 1.2s steps(1) infinite; }}
a {{ color: {LINK_COLOR}; }}
</style>
</head>
<body>
<div class="banner">
    <h1>🎩 STÄMNINGS-MASKINEN ✨</h1>
    <div class="tag">Personliga mood-kort, ritade av artificiell intelligens<br>
        <span class="blink">★ NU ÄVEN MED PIR-SENSOR ★</span>
    </div>
</div>
<marquee scrollamount="6">
    🎨 Välkommen till stämnings-maskinen! Här hittar du dagens mood-kort. ☎️ När en sensor utlöses så ringer en butler upp och frågar hur du mår — och så ritas ett uppmuntrande kort med AI. 🤖 Bäst i Netscape Navigator 4.0!
</marquee>
{_hr()}
{latest_block}
{_hr()}
{older_block}
{_hr()}
<footer>
    <em>Driven av 46elks, OpenAI, ElevenLabs och en gammal AxiDraw.</em><br>
    <a href="{html.escape(server_url)}">{html.escape(server_url)}</a>
</footer>
</body>
</html>
"""
    return body


def admin_page(cards: list, cards_dir, recent_metas: list[dict]) -> str:
    """Admin-vy med trigger-knapp + lista över kort med transkribering."""
    rows = ""
    for meta in recent_metas[:25]:
        ts = _format_swedish_date(float(meta.get("timestamp", 0)))
        rows += f"""
        <tr>
            <td style="vertical-align:top;padding:6px"><a href="/cards/{html.escape(meta.get('png',''))}" target="_blank"><img src="/cards/{html.escape(meta.get('png',''))}" width="100"></a></td>
            <td style="vertical-align:top;padding:6px;font-family:monospace;font-size:12px">
                <strong>{html.escape(ts)}</strong><br>
                call_id: <code>{html.escape(meta.get('call_id',''))}</code><br>
                <strong>Transkribering:</strong> {html.escape(meta.get('transcription','') or '—')}<br>
                <strong>Prompt:</strong> {html.escape(meta.get('image_prompt','') or '—')}<br>
                <strong>Ack:</strong> {html.escape(meta.get('butler_ack','') or '—')}<br>
                <a href="/cards/{html.escape(meta.get('svg',''))}" target="_blank">SVG</a>
            </td>
        </tr>
        """
    body = f"""
<!DOCTYPE html>
<html lang="sv">
<head><meta charset="utf-8"><title>Admin — Stämnings-maskinen</title>
<style>
body {{ font-family: {COMIC}; background:#fff8dc; color:#000080; padding:20px; }}
.btn {{
    display:inline-block; font-size:24px; padding:14px 28px;
    background:linear-gradient(180deg,#ff66ff,#9900cc); color:white;
    border:3px outset #ffccff; text-decoration:none; font-family:{COMIC};
    cursor:pointer;
}}
table {{ background:#ffffff; border:3px ridge #000080; margin-top:20px; width:100%; }}
td {{ border-bottom:1px solid #ccc; }}
</style>
</head>
<body>
<h1 style="color:{ACCENT};text-shadow:2px 2px 0 #00ffff">🎩 Admin — Stämnings-maskinen</h1>
<form action="/admin/trigger" method="post">
    <button type="submit" class="btn">☎️ TRIGGA SAMTAL NU</button>
</form>
<p>Det här ringer upp telefonnumret i <code>USER_PHONE_NUMBER</code>. Cooldown gäller.</p>
{_hr()}
<h2>Senaste {min(len(recent_metas), 25)} korten</h2>
<table cellpadding="4" cellspacing="0">
    {rows or '<tr><td>Inga kort än.</td></tr>'}
</table>
</body>
</html>
"""
    return body


def admin_trigger_result(ok: bool, msg: str) -> str:
    color = "#008000" if ok else "#c00000"
    return f"""
<!DOCTYPE html>
<html lang="sv"><head><meta charset="utf-8"><title>Trigger</title>
<style>body{{font-family:{COMIC};background:#fff8dc;padding:30px;color:{color};text-align:center}}</style>
</head><body>
<h1>{'✅' if ok else '❌'} {html.escape(msg)}</h1>
<p><a href="/admin">← Tillbaka till admin</a></p>
</body></html>
"""
