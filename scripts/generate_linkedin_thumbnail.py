"""LinkedIn Featured / Open Graph image: 1200x627.

Same materials as the cover banner (uniform near-black, Inter, sparse network)
but the share card keeps the name as the hero — OG previews do not already
show it underneath, unlike the LinkedIn profile cover.
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
from linkedin_brand import BG_PAGE, DISPLAY_NAME, FG, SITE_URL

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("LINKEDIN_THUMB_OUT", str(ROOT / "images" / "linkedin-featured.png")))

W, H = 1200, 627
SCALE = 2

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
INTER_CSS = {
    400: "https://fonts.googleapis.com/css2?family=Inter:wght@400&display=swap",
    500: "https://fonts.googleapis.com/css2?family=Inter:wght@500&display=swap",
    600: "https://fonts.googleapis.com/css2?family=Inter:wght@600&display=swap",
}

FG_EYEBROW = (176, 183, 194)
FG_URL = (156, 163, 174)

X_LOWER_NUDGE = 2
Y_EYEBROW = 214
Y_HERO = 256
Y_URL = 392

SIZE_EYEBROW = 22
SIZE_HERO = 104
SIZE_URL = 20

EYEBROW = "RESEARCHER + BUILDER"
HERO = DISPLAY_NAME

TRACK_EYEBROW = 0.22
TRACK_URL = 0.02
TRACK_HERO = -0.03

# Same tributary grammar as the banner, stretched into the taller 1200×627 field.
NODES_1X: tuple[tuple[float, float], ...] = (
    (900, 92),
    (948, 126),
    (888, 166),
    (962, 150),
    (1088, 76),
    (1148, 104),
    (1112, 148),
    (1174, 136),
    (888, 286),
    (938, 328),
    (902, 378),
    (1048, 272),
    (1112, 318),
    (1028, 364),
    (1098, 406),
    (1168, 378),
    (1128, 458),
    (1172, 436),
)

EDGES: tuple[tuple[int, int], ...] = (
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


def tracked_line_width(font: ImageFont.FreeTypeFont, text: str, tracking_em: float) -> float:
    if not text:
        return 0.0
    tracking_px = tracking_em * font.size
    total = 0.0
    for i, ch in enumerate(text):
        total += font.getlength(ch)
        if i < len(text) - 1:
            total += tracking_px
    return total


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
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    nodes = [(x * scale, y * scale) for x, y in NODES_1X]
    line_alpha = 50
    node_alpha = 61
    stroke = max(1, round(0.9 * scale))
    fill = (214, 220, 230, line_alpha)
    node_fill = (222, 228, 236, node_alpha)

    for i, (a, b) in enumerate(EDGES):
        x0, y0 = nodes[a]
        x1, y1 = nodes[b]
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
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

    radii = (2.4, 1.95, 2.6, 2.1, 1.9, 2.55, 2.2, 2.35, 2.05, 2.7, 1.95, 2.5, 2.15, 2.45, 2.0, 2.65, 2.1, 2.3)
    for (x, y), r in zip(nodes, radii):
        rr = r * scale
        draw.ellipse((x - rr, y - rr, x + rr, y + rr), fill=node_fill)

    arr = np.asarray(overlay).copy()
    xs = np.arange(arr.shape[1], dtype=np.float32)
    x0 = 900.0 * scale
    x1 = 1000.0 * scale
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
        font_url = ImageFont.truetype(paths[400], SIZE_URL * SCALE)

        block_w = max(
            tracked_line_width(font_eyebrow, EYEBROW, TRACK_EYEBROW),
            tracked_line_width(font_hero, HERO, TRACK_HERO),
            tracked_line_width(font_url, SITE_URL, TRACK_URL),
        )
        x_copy = (sw - block_w) / 2
        x_lower = x_copy + X_LOWER_NUDGE * SCALE

        b_eye = align_baseline_to_top(
            draw, x_copy, EYEBROW, font_eyebrow, TRACK_EYEBROW, Y_EYEBROW * SCALE
        )
        draw_tracked_baseline(draw, x_copy, b_eye, EYEBROW, font_eyebrow, TRACK_EYEBROW, FG_EYEBROW)

        b_hero = align_baseline_to_top(
            draw, x_copy, HERO, font_hero, TRACK_HERO, Y_HERO * SCALE
        )
        draw_tracked_baseline(draw, x_copy, b_hero, HERO, font_hero, TRACK_HERO, FG)

        b_url = align_baseline_to_top(
            draw, x_lower, SITE_URL, font_url, TRACK_URL, Y_URL * SCALE
        )
        draw_tracked_baseline(draw, x_lower, b_url, SITE_URL, font_url, TRACK_URL, FG_URL)

        img = img.resize((W, H), Image.LANCZOS)
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
