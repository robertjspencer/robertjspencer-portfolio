"""Write images/favicon.svg as a refined Inter RJS monogram."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images" / "favicon.svg"

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

    inner = 64.0 - (2 * PAD)
    scale = inner / max(max_x - min_x, max_y - min_y)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Robert J. Spencer">
  <rect width="64" height="64" rx="14" fill="#000000" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>
  <g fill="#ffffff" transform="translate(32,32) scale({scale:.6f},{-scale:.6f}) translate({-cx:.3f},{-cy:.3f})">
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
