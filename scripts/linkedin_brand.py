"""Shared background and colors for LinkedIn asset scripts (matches assets/css/main.css body gradient)."""

from __future__ import annotations

from PIL import Image

# Same stops as body { background-image: linear-gradient(180deg, ...) }
GRADIENT_STOPS: list[tuple[float, tuple[int, int, int]]] = [
    (0.0, (0x2B, 0x2B, 0x2B)),
    (0.28, (0x1F, 0x1F, 0x1F)),
    (0.65, (0x0A, 0x0A, 0x0A)),
    (1.0, (0x00, 0x00, 0x00)),
]

SITE_URL = "robertjspencer.com"
FG = (255, 255, 255)
# Site link / accent (main.css)
FG_URL = (140, 201, 240)


def _lerp_rgb(
    stops: list[tuple[float, tuple[int, int, int]]], t: float
) -> tuple[int, int, int]:
    if t <= stops[0][0]:
        return stops[0][1]
    if t >= stops[-1][0]:
        return stops[-1][1]
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        if t0 <= t <= t1:
            span = t1 - t0
            u = (t - t0) / span if span > 0 else 0.0
            return (
                int(c0[0] + (c1[0] - c0[0]) * u),
                int(c0[1] + (c1[1] - c0[1]) * u),
                int(c0[2] + (c1[2] - c0[2]) * u),
            )
    return stops[-1][1]


def vertical_site_gradient(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", (w, h))
    row = Image.new("RGB", (w, 1))
    for y in range(h):
        t = y / (h - 1) if h > 1 else 0.0
        rgb = _lerp_rgb(GRADIENT_STOPS, t)
        row.paste(rgb, (0, 0, w, 1))
        img.paste(row, (0, y))
    return img
