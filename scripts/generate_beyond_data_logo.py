"""Beyond Data wordmark banner for the Journey section (images/beyond-data-logo.png).

Recreates the Beyond Data brand banner: large grotesque wordmark on dark charcoal,
micro mono text block right-aligned, registration crosses and ruler ticks as accents.
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("BEYOND_DATA_LOGO_OUT", str(ROOT / "images" / "beyond-data-logo.png")))

# Sampled from the Beyond Data brand banner
BG = (0x1B, 0x1E, 0x25)
FG = (0xF2, 0xF3, 0xF5)
ACCENT = (0x55, 0x59, 0x62)

W, H = 1800, 500
SCALE = 2

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def woff2_to_temp_path(css_url: str) -> str:
    """Resolve a Google Fonts css2 URL to a temp .ttf (woff2 → ttf via fontTools)."""
    css = urlopen(Request(css_url, headers={"User-Agent": UA})).read().decode()
    # css2 emits one @font-face per unicode-range subset; latin is the last block
    urls = re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", css)
    if not urls:
        raise RuntimeError(f"No woff2 URL found in {css_url}")
    data = urlopen(urls[-1]).read()
    font = TTFont(BytesIO(data))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ttf")
    font.save(tmp.name)
    return tmp.name


def fit_font(path: str, text: str, target_width: float, start_size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(path, start_size)
    size = int(start_size * target_width / max(font.getlength(text), 1.0))
    return ImageFont.truetype(path, size)


def draw_cross(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, width: int) -> None:
    draw.line([(cx - r, cy), (cx + r, cy)], fill=ACCENT, width=width)
    draw.line([(cx, cy - r), (cx, cy + r)], fill=ACCENT, width=width)


def main() -> None:
    inter = woff2_to_temp_path(
        "https://fonts.googleapis.com/css2?family=Inter:wght@400&display=swap"
    )
    mono = woff2_to_temp_path(
        "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@600&display=swap"
    )
    try:
        sw, sh = W * SCALE, H * SCALE
        img = Image.new("RGB", (sw, sh), BG)
        draw = ImageDraw.Draw(img)

        # Wordmark: ~60% of canvas width, centred left of middle to clear the mono column
        wordmark = "Beyond Data"
        font_word = fit_font(inter, wordmark, 0.60 * sw, 200 * SCALE)
        bbox = draw.textbbox((0, 0), wordmark, font=font_word)
        wm_w = bbox[2] - bbox[0]
        wm_h = bbox[3] - bbox[1]
        wm_x = 0.47 * sw - wm_w / 2 - bbox[0]
        wm_y = sh / 2 - wm_h / 2 - bbox[1]
        draw.text((wm_x, wm_y), wordmark, font=font_word, fill=FG)

        # Micro mono blocks, left-aligned column near the right edge
        font_mono = ImageFont.truetype(mono, int(12 * SCALE))
        mono_x = 0.84 * sw
        line_h = font_mono.size * 1.4
        blocks = [
            ("INTELLIGENT OPERATING SYSTEMS", "EST. 2003—AUS"),
            ("AI-POWERED OPERATIONS FOR", "EVERY AUSTRALIAN BUSINESS"),
            ("© BEYOND DATA ANALYTICAL SERVICES",),
        ]
        block_tops = [0.415 * sh, 0.545 * sh, 0.655 * sh]
        for top, lines in zip(block_tops, blocks):
            y = top
            for line in lines:
                draw.text((mono_x, y), line, font=font_mono, fill=FG)
                y += line_h

        # Registration crosses (right edge) and ruler ticks (left edge)
        cross_x = 0.983 * sw
        for cy in (0.24 * sh, 0.80 * sh):
            draw_cross(draw, cross_x, cy, 13 * SCALE, SCALE)

        tick_x = 0.011 * sw
        n_ticks = 14
        y0, y1 = 0.26 * sh, 0.74 * sh
        for i in range(n_ticks):
            y = y0 + (y1 - y0) * i / (n_ticks - 1)
            length = (16 if i % 4 == 0 else 9) * SCALE
            draw.line([(tick_x, y), (tick_x + length, y)], fill=ACCENT, width=SCALE)

        img = img.resize((W, H), Image.LANCZOS)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        img.save(OUT, format="PNG", optimize=True)
        print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    finally:
        os.unlink(inter)
        os.unlink(mono)


if __name__ == "__main__":
    main()
