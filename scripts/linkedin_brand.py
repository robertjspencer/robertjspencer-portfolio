"""Shared background and colors for LinkedIn asset scripts.

Background matches :root[data-theme='dark'] body in assets/css/custom.css:
radial-gradient(circle at top left, var(--bg-glow), transparent 32%) over var(--bg-page).
"""

from __future__ import annotations

from PIL import Image

# :root[data-theme='dark'] — assets/css/custom.css
BG_PAGE = (0x0D, 0x11, 0x17)  # --bg-page #0d1117
# --bg-glow: rgba(255, 255, 255, 0.07) painted over BG_PAGE, fading out by transparent 32%
GLOW_ALPHA = 0.07
GLOW_STOP = 0.32

SITE_URL = "robertjspencer.com"
# --text-strong #f5f7fb
FG = (0xF5, 0xF7, 0xFB)
# --text-muted rgba(245, 247, 251, 0.68) over page bg (same blend as on the site)
_FG = (0xF5, 0xF7, 0xFB)
FG_URL = tuple(
    int(_FG[i] * 0.68 + BG_PAGE[i] * 0.32 + 0.5) for i in range(3)
)


def site_body_background(size: tuple[int, int]) -> Image.Image:
    """Radial glow at top-left over page colour (matches dark theme body background)."""
    w, h = size
    r0, g0, b0 = BG_PAGE
    radius = (w * w + h * h) ** 0.5 if (w or h) else 1.0
    stop = GLOW_STOP
    buf = bytearray(w * h * 3)
    i = 0
    for y in range(h):
        yy = y * y
        for x in range(w):
            d = (x * x + yy) ** 0.5
            p = d / radius
            if p >= stop:
                buf[i] = r0
                buf[i + 1] = g0
                buf[i + 2] = b0
            else:
                a = GLOW_ALPHA * (1.0 - p / stop)
                buf[i] = int(r0 + (255 - r0) * a + 0.5)
                buf[i + 1] = int(g0 + (255 - g0) * a + 0.5)
                buf[i + 2] = int(b0 + (255 - b0) * a + 0.5)
            i += 3
    return Image.frombytes("RGB", (w, h), bytes(buf))
