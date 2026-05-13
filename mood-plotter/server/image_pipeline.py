"""DALL-E -> PNG -> vpype-vektorisering -> SVG."""
import logging
import subprocess
import tempfile
from pathlib import Path

from openai import OpenAI

log = logging.getLogger(__name__)


def _call_dalle(prompt: str, api_key: str) -> bytes:
    """Generera en PNG fran en prompt med gpt-image-1.

    DALL-E 3 ar borttaget. gpt-image-1 returnerar alltid b64_json (ingen
    response_format-param), och har inte quality='standard' — den vill ha
    low/medium/high/auto. 'low' ger snabbare svar och mindre detaljer,
    vilket passar pen-plottern bra anda.
    """
    import base64

    client = OpenAI(api_key=api_key)
    resp = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
        quality="low",
        n=1,
    )
    return base64.b64decode(resp.data[0].b64_json)


def png_to_svg(png_bytes: bytes) -> str:
    """Vektorisera PNG till SVG via vpype + vpype-vectrace plugin (iread)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        png_path = tmp_path / "in.png"
        svg_path = tmp_path / "out.svg"
        png_path.write_bytes(png_bytes)

        # Aggressiv forenkling for renare plotterskissar:
        # - linemerge 2mm slar ihop nara linjer
        # - filter --min-length 4mm tar bort knottriga sma fragment
        # - linesimplify 0.5mm ger fortfarande mjuka kurvor utan brus
        cmd = [
            "vpype",
            "iread", str(png_path),
            "linemerge", "--tolerance", "2mm",
            "filter", "--min-length", "4mm",
            "linesimplify", "--tolerance", "0.5mm",
            "linesort",
            "layout", "--align", "center", "--valign", "center", "10cmx10cm",
            "write", str(svg_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"vpype failed: {result.stderr}")

        return svg_path.read_text()


def generate_png(prompt: str, api_key: str) -> bytes:
    """Hamta bara PNG-bytes fran DALL-E. Publik wrapper kring _call_dalle."""
    log.info("Genererar bild for prompt: %s", prompt[:80])
    png = _call_dalle(prompt, api_key)
    log.info("DALL-E PNG mottagen, %d bytes", len(png))
    return png


def generate_svg(prompt: str, api_key: str) -> str:
    """Full pipeline: prompt -> DALL-E -> vpype -> SVG-strang."""
    png = generate_png(prompt, api_key)
    svg = png_to_svg(png)
    log.info("SVG genererad, %d tecken", len(svg))
    return svg
