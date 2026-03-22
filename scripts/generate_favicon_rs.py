"""Write images/favicon.svg using outlined Space Grotesk 700 glyphs (no embedded fonts)."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images" / "favicon.svg"

FONT_URL = (
    "https://fonts.gstatic.com/s/spacegrotesk/v22/"
    "V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj4PVnskPMA.woff2"
)


def main() -> None:
    font = TTFont(BytesIO(urlopen(FONT_URL).read()))
    gs = font.getGlyphSet()

    pen_r = SVGPathPen(gs)
    gs["R"].draw(pen_r)
    d_r = pen_r.getCommands()

    pen_s = SVGPathPen(gs)
    gs["S"].draw(pen_s)
    d_s = pen_s.getCommands()

    # Horizontal offset for "S" (~-0.06em kerning vs separate default spacing)
    s_offset_x = 494.0

    rb = (66.0, 0.0, 588.0, 700.0)
    sb = (34.0 + s_offset_x, -14.0, 574.0 + s_offset_x, 714.0)
    min_x = min(rb[0], sb[0])
    max_x = max(rb[2], sb[2])
    min_y = min(rb[1], sb[1])
    max_y = max(rb[3], sb[3])
    w = max_x - min_x
    h = max_y - min_y
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2

    pad = 6.0
    inner = 64.0 - 2 * pad
    scale = inner / max(w, h)

    # Negative Y scale: TrueType outlines use y-up; SVG uses y-down.
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Robert Spencer">
  <rect width="64" height="64" rx="14" fill="#ffffff" stroke="rgba(0,0,0,0.14)" stroke-width="1"/>
  <g fill="#000000" transform="translate(32,32) scale({scale:.6f},{-scale:.6f}) translate({-cx:.3f},{-cy:.3f})">
    <path d="{d_r}"/>
    <path transform="translate({s_offset_x:.3f} 0)" d="{d_s}"/>
  </g>
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
