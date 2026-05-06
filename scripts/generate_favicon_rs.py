"""Write images/favicon.svg as a refined Inter RJS monogram."""
from __future__ import annotations

import sys
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from linkedin_brand import BG_PAGE, GLOW_ALPHA, GLOW_STOP

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images" / "favicon.svg"

ICON = 64.0
# Same radial metric as scripts/linkedin_brand.site_body_background: p = distance / hypot(w,h), fade over p<GLOW_STOP
_BG_HEX = "#{0:02x}{1:02x}{2:02x}".format(*BG_PAGE)
_GLOW_RADIUS = GLOW_STOP * (ICON**2 + ICON**2) ** 0.5

FONT_URL = (
    "https://fonts.gstatic.com/s/inter/v20/"
    "UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfAZ9hiA.woff2"
)
LETTERS = ("R", "J", "S")
TRACKING = -105.0
PAD = 10.0


def main() -> None:
    font = TTFont(BytesIO(urlopen(FONT_URL).read()))
    gs = font.getGlyphSet()
    glyf = font["glyf"]
    hmtx = font["hmtx"]

    offsets: dict[str, float] = {}
    paths: dict[str, str] = {}
    placed_bounds: list[tuple[float, float, float, float]] = []
    cursor_x = 0.0

    for idx, letter in enumerate(LETTERS):
        offset = cursor_x + (TRACKING * idx)
        offsets[letter] = offset
        pen = SVGPathPen(gs)
        gs[letter].draw(pen)
        paths[letter] = pen.getCommands()
        glyph = glyf[letter]
        placed_bounds.append(
            (
                float(glyph.xMin) + offset,
                float(glyph.yMin),
                float(glyph.xMax) + offset,
                float(glyph.yMax),
            )
        )
        advance_width, _ = hmtx[letter]
        cursor_x += float(advance_width)

    min_x = min(p[0] for p in placed_bounds)
    max_x = max(p[2] for p in placed_bounds)
    min_y = min(p[1] for p in placed_bounds)
    max_y = max(p[3] for p in placed_bounds)
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2

    inner = ICON - (2 * PAD)
    scale = inner / max(max_x - min_x, max_y - min_y)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ICON:.0f} {ICON:.0f}" role="img" aria-label="Robert J. Spencer">
  <defs>
    <radialGradient id="bg-glow" gradientUnits="userSpaceOnUse" cx="0" cy="0" r="{_GLOW_RADIUS:.4f}">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="{GLOW_ALPHA}"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{ICON:.0f}" height="{ICON:.0f}" rx="14" fill="{_BG_HEX}"/>
  <rect width="{ICON:.0f}" height="{ICON:.0f}" rx="14" fill="url(#bg-glow)"/>
  <rect width="{ICON:.0f}" height="{ICON:.0f}" rx="14" fill="none" stroke="rgba(245,247,251,0.12)" stroke-width="1"/>
  <g fill="#f5f7fb" transform="translate({ICON/2:.0f},{ICON/2:.0f}) scale({scale:.6f},{-scale:.6f}) translate({-cx:.3f},{-cy:.3f})">
    <path d="{paths["R"]}"/>
    <path transform="translate({offsets["J"]:.3f} 0)" d="{paths["J"]}"/>
    <path transform="translate({offsets["S"]:.3f} 0)" d="{paths["S"]}"/>
  </g>
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
