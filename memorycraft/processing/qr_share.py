"""QR-code sharing card.

Generates a themed QR poster pointing at wherever the user hosts the
video (YouTube link, Google Drive, family website...). Guests scan the
card at the party and land on the memory instantly.
"""

from __future__ import annotations

from pathlib import Path

import qrcode
from PIL import Image, ImageDraw

from ..core.themes import Theme
from ..utils.fonts import load_font


def build_qr_card(link: str, theme: Theme, title: str, output_path: Path,
                  size: int = 900) -> Path:
    """Render a share card: heading, QR code and the link caption."""
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=2)
    qr.add_data(link)
    qr.make(fit=True)
    code = qr.make_image(fill_color=theme.hex(theme.background),
                         back_color="#ffffff").convert("RGB")

    card = Image.new("RGB", (size, round(size * 1.25)), theme.background)
    draw = ImageDraw.Draw(card)

    heading = load_font(theme.heading_font, round(size * 0.07))
    caption = load_font(theme.body_font, round(size * 0.03))

    draw.text((size // 2, round(size * 0.1)), title or "Scan to Relive",
              font=heading, fill=theme.primary, anchor="mm")
    draw.text((size // 2, round(size * 0.18)), "Point your camera at the code",
              font=caption, fill=theme.text, anchor="mm")

    qr_size = round(size * 0.62)
    code = code.resize((qr_size, qr_size), Image.Resampling.NEAREST)
    qx = (size - qr_size) // 2
    qy = round(size * 0.26)
    # white mat behind the code keeps it scannable on dark themes
    pad = round(size * 0.02)
    draw.rectangle([qx - pad, qy - pad, qx + qr_size + pad, qy + qr_size + pad],
                   fill="#ffffff")
    card.paste(code, (qx, qy))
    draw.rectangle([qx - pad, qy - pad, qx + qr_size + pad, qy + qr_size + pad],
                   outline=theme.primary, width=4)

    shown = link if len(link) <= 60 else link[:57] + "..."
    draw.text((size // 2, qy + qr_size + round(size * 0.08)), shown,
              font=caption, fill=theme.accent, anchor="mm")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    card.save(output_path)
    return output_path
