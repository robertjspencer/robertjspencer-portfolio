"""LinkedIn profile cover: 1584x396.

Uniform near-black field. Left ~0–430px stays empty for the profile-photo
overlap (blank, not a separate colour block). Copy is left-aligned in the
main band. A sparse clustered network sits in the right third at low opacity.
"""
from __future__ import annotations

import math
import os
import re
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from linkedin_brand import BG_PAGE, FG, SITE_URL

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("LINKEDIN_BANNER_OUT", str(ROOT / "images" / "linkedin-banner.png")))

# LinkedIn cover (recommended): https://www.linkedin.com/help/linkedin/answer/a568217
W, H = 1584, 396
SCALE = 2

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Inter via Google Fonts css2 (latin subset is the last @font-face block).
INTER_CSS = {
    400: "https://fonts.googleapis.com/css2?family=Inter:wght@400&display=swap",
    500: "https://fonts.googleapis.com/css2?family=Inter:wght@500&display=swap",
    600: "https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap",
}

# Light grey eyebrow; descriptor secondary but readable; URL tertiary.
FG_EYEBROW = (176, 183, 194)
FG_DESCRIPTOR = (132, 140, 152)
FG_URL = (156, 163, 174)

# Figma-style tops (1× px). Clear of the profile-photo overlay; nudged left of
# the 590 band after the type size increase so the block doesn't crowd the right.
X_COPY = 566
X_LOWER = 568
Y_EYEBROW = 82
Y_HERO = 115
Y_DESCRIPTOR = 259
Y_URL = 294

SIZE_EYEBROW = 20
SIZE_HERO = 64
SIZE_DESCRIPTOR = 18
SIZE_URL = 17

EYEBROW = "RESEARCHER + BUILDER"
HERO_LINES = ("Building AI systems for", "real-world complexity.")
DESCRIPTOR = "DIGITAL TWINS  ·  APPLIED ML  ·  ONE HEALTH"

# Tracking as em (Figma +200 ≈ 0.20em).
TRACK_EYEBROW = 0.22
TRACK_DESCRIPTOR = 0.05
TRACK_URL = 0.02
TRACK_HERO = 0.0

# Hand-placed nodes in the right third (x 1250–1550). Three tributaries
# (biological / environmental / agribusiness) feeding a lower-right confluence.
NODES_1X: tuple[tuple[float, float], ...] = (
    # Cluster A — high left
    (1288, 62),
    (1324, 84),
    (1296, 112),
    (1342, 98),
    # Cluster B — high right
    (1478, 52),
    (1522, 70),
    (1496, 98),
    (1542, 108),
    # Cluster C — mid-left branch
    (1268, 198),
    (1304, 224),
    (1282, 258),
    # Cluster D — lower-right confluence
    (1418, 188),
    (1464, 216),
    (1402, 248),
    (1456, 272),
    (1510, 254),
    (1484, 304),
    (1534, 288),
)

EDGES: tuple[tuple[int, int], ...] = (
    # Intra-cluster
    (0, 1),
    (1, 2),
    (1, 3),
    (0, 3),
    (4, 5),
    (5, 6),
    (5, 7),
    (6, 7),
    (8, 9),
    (9, 10),
    (8, 10),
    (11, 12),
    (12, 13),
    (13, 14),
    (12, 14),
    (14, 15),
    (14, 16),
    (15, 16),
    # Tributaries into the confluence
    (2, 11),
    (3, 12),
    (6, 11),
    (7, 14),
    (9, 13),
    (10, 15),
    (3, 6),
    (8, 2),
)


def woff2_to_temp_path(css_url: str) -> str:
    css = urlopen(Request(css_url, headers={"User-Agent": UA})).read().decode()
    urls = re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+\.woff2)\)", css)
    if not urls:
        raise RuntimeError(f"No woff2 URL found in {css_url}")
    data = urlopen(urls[-1]).read()
    font = TTFont(BytesIO(data))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ttf")
    font.save(tmp.name)
    return tmp.name


def draw_tracked_baseline(
    draw: ImageDraw.ImageDraw,
    x: float,
    baseline_y: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking_em: float,
    fill: tuple[int, int, int],
) -> None:
    tracking_px = tracking_em * font.size
    cur_x = x
    for i, ch in enumerate(text):
        draw.text((cur_x, baseline_y), ch, font=font, fill=fill, anchor="ls")
        cur_x += font.getlength(ch)
        if i < len(text) - 1:
            cur_x += tracking_px


def tracked_ink_bbox(
    draw: ImageDraw.ImageDraw,
    x: float,
    baseline_y: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking_em: float,
) -> tuple[float, float, float, float]:
    tracking_px = tracking_em * font.size
    cur_x = x
    boxes: list[tuple[float, float, float, float]] = []
    for i, ch in enumerate(text):
        boxes.append(draw.textbbox((cur_x, baseline_y), ch, font=font, anchor="ls"))
        cur_x += font.getlength(ch)
        if i < len(text) - 1:
            cur_x += tracking_px
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )


def align_baseline_to_top(
    draw: ImageDraw.ImageDraw,
    x: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking_em: float,
    want_top: float,
) -> float:
    baseline_y = want_top + 100.0
    for _ in range(12):
        _l, top, _r, _b = tracked_ink_bbox(draw, x, baseline_y, text, font, tracking_em)
        shift = want_top - top
        baseline_y += shift
        if abs(shift) < 0.25:
            break
    return baseline_y


def quad_bezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    n: int = 28,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(n + 1):
        t = i / n
        u = 1.0 - t
        pts.append(
            (
                u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
            )
        )
    return pts


def draw_systems_network(base: Image.Image, scale: int) -> None:
    """Sparse 4-cluster network, ~20–24% opacity, confined to the right third."""
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    nodes = [(x * scale, y * scale) for x, y in NODES_1X]
    line_alpha = 50  # ~20%
    node_alpha = 61  # ~24%
    stroke = max(1, round(0.9 * scale))
    fill = (214, 220, 230, line_alpha)
    node_fill = (222, 228, 236, node_alpha)

    for i, (a, b) in enumerate(EDGES):
        x0, y0 = nodes[a]
        x1, y1 = nodes[b]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        # Longer bridges bow more so clusters read as feeding into one another.
        bow_em = 0.16 + 0.18 * min(1.0, length / (220.0 * scale))
        bow = length * bow_em * (-1 if i % 2 == 0 else 1)
        ctrl = ((x0 + x1) / 2 + nx * bow, (y0 + y1) / 2 + ny * bow)
        n_pts = 36 if length > 80 * scale else 24
        draw.line(
            quad_bezier((x0, y0), ctrl, (x1, y1), n=n_pts),
            fill=fill,
            width=stroke,
            joint="curve",
        )

    radii = (2.1, 1.7, 2.3, 1.85, 1.65, 2.25, 1.95, 2.05, 1.8, 2.4, 1.7, 2.2, 1.9, 2.15, 1.75, 2.35, 1.85, 2.0)
    for (x, y), r in zip(nodes, radii):
        rr = r * scale
        draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=node_fill)

    # Soften the graphic's left edge so it never competes with copy.
    arr = np.asarray(overlay).copy()
    xs = np.arange(arr.shape[1], dtype=np.float32)
    x0 = 1220.0 * scale
    x1 = 1310.0 * scale
    fade = np.clip((xs - x0) / max(1.0, x1 - x0), 0.0, 1.0)
    arr[:, :, 3] = (arr[:, :, 3].astype(np.float32) * fade[np.newaxis, :]).astype(np.uint8)
    overlay = Image.fromarray(arr, "RGBA")

    composited = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    base.paste(composited)


def main() -> None:
    paths = {wght: woff2_to_temp_path(url) for wght, url in INTER_CSS.items()}
    try:
        sw, sh = W * SCALE, H * SCALE
        img = Image.new("RGB", (sw, sh), BG_PAGE)
        draw_systems_network(img, SCALE)
        draw = ImageDraw.Draw(img)

        font_eyebrow = ImageFont.truetype(paths[500], SIZE_EYEBROW * SCALE)
        font_hero = ImageFont.truetype(paths[600], SIZE_HERO * SCALE)
        font_descriptor = ImageFont.truetype(paths[500], SIZE_DESCRIPTOR * SCALE)
        font_url = ImageFont.truetype(paths[400], SIZE_URL * SCALE)

        x_copy = X_COPY * SCALE
        x_lower = X_LOWER * SCALE

        b_eye = align_baseline_to_top(
            draw, x_copy, EYEBROW, font_eyebrow, TRACK_EYEBROW, Y_EYEBROW * SCALE
        )
        draw_tracked_baseline(draw, x_copy, b_eye, EYEBROW, font_eyebrow, TRACK_EYEBROW, FG_EYEBROW)

        hero_lh = SIZE_HERO * 0.97 * SCALE
        for i, line in enumerate(HERO_LINES):
            want_top = Y_HERO * SCALE + i * hero_lh
            b = align_baseline_to_top(draw, x_copy, line, font_hero, TRACK_HERO, want_top)
            draw_tracked_baseline(draw, x_copy, b, line, font_hero, TRACK_HERO, FG)

        b_desc = align_baseline_to_top(
            draw, x_lower, DESCRIPTOR, font_descriptor, TRACK_DESCRIPTOR, Y_DESCRIPTOR * SCALE
        )
        draw_tracked_baseline(
            draw, x_lower, b_desc, DESCRIPTOR, font_descriptor, TRACK_DESCRIPTOR, FG_DESCRIPTOR
        )

        b_url = align_baseline_to_top(
            draw, x_lower, SITE_URL, font_url, TRACK_URL, Y_URL * SCALE
        )
        draw_tracked_baseline(draw, x_lower, b_url, SITE_URL, font_url, TRACK_URL, FG_URL)

        img = img.resize((W, H), Image.LANCZOS)
        # LANCZOS can undershoot around faint light-on-dark strokes; clip so the
        # field stays a uniform near-black instead of a darker right-hand smear.
        arr = np.maximum(np.asarray(img), np.array(BG_PAGE, dtype=np.uint8))
        img = Image.fromarray(arr, "RGB")
        OUT.parent.mkdir(parents=True, exist_ok=True)
        img.save(OUT, format="PNG", optimize=True)
        print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    finally:
        for p in paths.values():
            os.unlink(p)


if __name__ == "__main__":
    main()
