"""Generate LinkedIn Featured image (1200x627) matching site hero + banner styling (dark theme body background)."""
from __future__ import annotations

import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen

from fontTools.ttLib import TTFont
import numpy as np
from PIL import Image, ImageDraw, ImageFont

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from linkedin_brand import DISPLAY_NAME, FG, FG_URL, SITE_URL, site_body_background

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("LINKEDIN_THUMB_OUT", str(ROOT / "images" / "linkedin-featured.png")))

WOFF2_IBM_PLEX_600 = (
    "https://fonts.gstatic.com/s/ibmplexsans/v23/"
    "zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSDNF5DB6g4.woff2"
)
WOFF2_IBM_PLEX_400 = (
    "https://fonts.gstatic.com/s/ibmplexsans/v23/"
    "zYXGKVElMYYaJe8bpLHnCwDKr932-G7dytD-Dmu1swZSAXcomDVmadSD6llDB6g4.woff2"
)
WOFF2_SPACE_GROTESK_700 = (
    "https://fonts.gstatic.com/s/spacegrotesk/v22/"
    "V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj4PVnskPMA.woff2"
)

W, H = 1200, 627
# Render at 2× then downscale with LANCZOS for crisp sub-pixel anti-aliasing.
SCALE = 2
# Between original 180 (too far right) and 140 (still a touch left for the card).
MARGIN_X = 160


def woff2_to_temp_path(url: str) -> str:
    data = urlopen(url).read()
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
    """Union of per-glyph ink boxes (anchor=left baseline)."""
    tracking_px = tracking_em * font.size
    cur_x = x
    boxes: list[tuple[float, float, float, float]] = []
    for i, ch in enumerate(text):
        b = draw.textbbox((cur_x, baseline_y), ch, font=font, anchor="ls")
        boxes.append(b)
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
    """Return baseline_y so the ink top of the tracked line equals want_top."""
    baseline_y = want_top + 100.0
    for _ in range(12):
        _l, top, _r, _b = tracked_ink_bbox(draw, x, baseline_y, text, font, tracking_em)
        shift = want_top - top
        baseline_y += shift
        if abs(shift) < 0.25:
            break
    return baseline_y


def align_x_to_ink_left(
    draw: ImageDraw.ImageDraw,
    target_left: float,
    baseline_y: float,
    text: str,
    font: ImageFont.FreeTypeFont,
    tracking_em: float,
) -> float:
    """Return x so the line's visible ink starts at target_left on this baseline."""
    x = target_left
    for _ in range(12):
        left, _top, _right, _bottom = tracked_ink_bbox(
            draw, x, baseline_y, text, font, tracking_em
        )
        shift = target_left - left
        x += shift
        if abs(shift) < 0.25:
            break
    return x


def layout_featured_block(
    draw: ImageDraw.ImageDraw,
    margin_x: float,
    font_eyebrow: ImageFont.FreeTypeFont,
    font_name: ImageFont.FreeTypeFont,
    font_url: ImageFont.FreeTypeFont,
    eyebrow: str,
    name: str,
    gap: float,
    gap_after_name: float,
    track_eye: float,
    track_name: float,
    track_url: float,
    canvas_h: float,
) -> tuple[float, float, float, float, float, float]:
    """Lay out eyebrow, name, and URL with a shared ink-left edge from the name line."""
    x_name = align_x_to_ink_left(draw, margin_x, 0.0, name, font_name, track_name)
    b_eye = tracked_ink_bbox(draw, x_name, 0.0, eyebrow, font_eyebrow, track_eye)
    b_name = tracked_ink_bbox(draw, x_name, 0.0, name, font_name, track_name)
    b_url = tracked_ink_bbox(draw, x_name, 0.0, SITE_URL, font_url, track_url)
    block_h = (
        (b_eye[3] - b_eye[1])
        + gap
        + (b_name[3] - b_name[1])
        + gap_after_name
        + (b_url[3] - b_url[1])
    )
    y_top = (canvas_h - block_h) / 2

    baseline_eye = align_baseline_to_top(
        draw, x_name, eyebrow, font_eyebrow, track_eye, y_top
    )
    ink_eye = tracked_ink_bbox(draw, x_name, baseline_eye, eyebrow, font_eyebrow, track_eye)
    want_name_top = ink_eye[3] + gap
    baseline_name = align_baseline_to_top(
        draw, x_name, name, font_name, track_name, want_name_top
    )
    ink_name = tracked_ink_bbox(draw, x_name, baseline_name, name, font_name, track_name)
    ref_left = ink_name[0]
    x_eye = align_x_to_ink_left(
        draw, ref_left, baseline_eye, eyebrow, font_eyebrow, track_eye
    )
    x_name = align_x_to_ink_left(
        draw, ref_left, baseline_name, name, font_name, track_name
    )
    want_url_top = ink_name[3] + gap_after_name
    baseline_url = align_baseline_to_top(
        draw, x_name, SITE_URL, font_url, track_url, want_url_top
    )
    x_url = align_x_to_ink_left(
        draw, ref_left, baseline_url, SITE_URL, font_url, track_url
    )
    return x_eye, baseline_eye, x_name, baseline_name, x_url, baseline_url


def pixel_left_edge(
    img: Image.Image,
    ink_bbox: tuple[float, float, float, float],
    *,
    pad: int = 2,
    threshold: int | None = None,
) -> float | None:
    """Leftmost bright pixel in a text band (matches what the eye sees after rasterisation)."""
    y0 = max(0, int(ink_bbox[1]) - pad)
    y1 = min(img.height, int(ink_bbox[3]) + pad)
    if y1 <= y0:
        return None
    if threshold is None:
        threshold = 200
    band = np.asarray(img)[y0:y1]
    if band.ndim == 3:
        bright = band.max(axis=2) > threshold
    else:
        bright = band > threshold
    cols = np.where(bright)
    if not cols[0].size:
        return None
    return float(cols[1].min())


def render_featured(
    sw: int,
    sh: int,
    margin_x: float,
    font_eyebrow: ImageFont.FreeTypeFont,
    font_name: ImageFont.FreeTypeFont,
    font_url: ImageFont.FreeTypeFont,
    eyebrow: str,
    name: str,
    gap: float,
    gap_after_name: float,
    track_eye: float,
    track_name: float,
    track_url: float,
    *,
    shift_x: float = 0.0,
    shift_x_url: float = 0.0,
) -> tuple[
    Image.Image,
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]:
    """Render the featured frame; shift_x nudges name, shift_x_url nudges the URL line."""
    img = site_body_background((sw, sh))
    draw = ImageDraw.Draw(img)
    x_eye, baseline_eye, x_name, baseline_name, x_url, baseline_url = layout_featured_block(
        draw,
        margin_x,
        font_eyebrow,
        font_name,
        font_url,
        eyebrow,
        name,
        gap,
        gap_after_name,
        track_eye,
        track_name,
        track_url,
        sh,
    )
    x_name += shift_x
    x_url += shift_x + shift_x_url
    draw_tracked_baseline(draw, x_eye, baseline_eye, eyebrow, font_eyebrow, track_eye, FG)
    draw_tracked_baseline(draw, x_name, baseline_name, name, font_name, track_name, FG)
    draw_tracked_baseline(draw, x_url, baseline_url, SITE_URL, font_url, track_url, FG_URL)
    ink_eye = tracked_ink_bbox(draw, x_eye, baseline_eye, eyebrow, font_eyebrow, track_eye)
    ink_name = tracked_ink_bbox(draw, x_name, baseline_name, name, font_name, track_name)
    ink_url = tracked_ink_bbox(draw, x_url, baseline_url, SITE_URL, font_url, track_url)
    return img, ink_eye, ink_name, ink_url


def main() -> None:
    plex_600 = woff2_to_temp_path(WOFF2_IBM_PLEX_600)
    plex_400 = woff2_to_temp_path(WOFF2_IBM_PLEX_400)
    sg_path = woff2_to_temp_path(WOFF2_SPACE_GROTESK_700)
    try:
        sw, sh = W * SCALE, H * SCALE
        margin_x = float(MARGIN_X * SCALE)

        eyebrow_size = 23 * SCALE
        name_size = 128 * SCALE
        url_size = 28 * SCALE
        font_eyebrow = ImageFont.truetype(plex_600, eyebrow_size)
        font_name = ImageFont.truetype(sg_path, name_size)
        font_url = ImageFont.truetype(plex_400, url_size)

        eyebrow = "RESEARCHER + BUILDER"
        name = DISPLAY_NAME
        gap = 26 * SCALE
        gap_after_name = 16 * SCALE

        track_eye = 0.16
        track_name = -0.06
        track_url = 0.05

        shift_x = 0.0
        shift_x_url = 0.0
        img, ink_eye, ink_name, _ink_url = render_featured(
            sw,
            sh,
            margin_x,
            font_eyebrow,
            font_name,
            font_url,
            eyebrow,
            name,
            gap,
            gap_after_name,
            track_eye,
            track_name,
            track_url,
        )
        pl_eye = pixel_left_edge(img, ink_eye)
        pl_name = pixel_left_edge(img, ink_name)
        if pl_eye is not None and pl_name is not None:
            dx = pl_name - pl_eye
            if abs(dx) >= 2:
                shift_x = -dx
        if shift_x:
            img, ink_eye, ink_name, ink_url = render_featured(
                sw,
                sh,
                margin_x,
                font_eyebrow,
                font_name,
                font_url,
                eyebrow,
                name,
                gap,
                gap_after_name,
                track_eye,
                track_name,
                track_url,
                shift_x=shift_x,
            )
        else:
            ink_url = _ink_url
        url_threshold = int(min(FG_URL) * 0.72)
        pl_eye = pixel_left_edge(img, ink_eye)
        pl_url = pixel_left_edge(img, ink_url, threshold=url_threshold)
        if pl_eye is not None and pl_url is not None:
            dx_url = pl_url - pl_eye
            if abs(dx_url) >= 2:
                shift_x_url = -dx_url
        if shift_x_url:
            img, _, _, _ = render_featured(
                sw,
                sh,
                margin_x,
                font_eyebrow,
                font_name,
                font_url,
                eyebrow,
                name,
                gap,
                gap_after_name,
                track_eye,
                track_name,
                track_url,
                shift_x=shift_x,
                shift_x_url=shift_x_url,
            )

        img = img.resize((W, H), Image.LANCZOS)

        OUT.parent.mkdir(parents=True, exist_ok=True)
        img.save(OUT, format="PNG", optimize=True)
        print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    finally:
        os.unlink(plex_600)
        os.unlink(plex_400)
        os.unlink(sg_path)


if __name__ == "__main__":
    main()
