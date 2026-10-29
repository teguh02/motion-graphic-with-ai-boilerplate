"""Tile still frames into contact sheets for quick visual review (agents: open these images to self-check).

Usage: python tools/contact.py [build/stills] [build/sheet] [per_sheet]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

from common import BUILD

TILE_W, TILE_H, COLS = 360, 640, 4


def contact_sheets(src: Path, out_stem: Path, per: int = 12) -> list[Path]:
    files = sorted(src.glob("*.png"))
    sheets = []
    for k in range(0, len(files), per):
        group = files[k:k + per]
        rows = (len(group) + COLS - 1) // COLS
        sheet = Image.new("RGB", (TILE_W * COLS, TILE_H * rows), "black")
        for i, f in enumerate(group):
            im = Image.open(f).convert("RGB").resize((TILE_W, TILE_H))
            draw = ImageDraw.Draw(im)
            draw.rectangle((0, 0, 130, 26), fill="black")
            draw.text((8, 6), f.stem, fill="yellow")
            sheet.paste(im, ((i % COLS) * TILE_W, (i // COLS) * TILE_H))
        path = out_stem.parent / f"{out_stem.name}_{k // per}.jpg"
        sheet.save(path, quality=88)
        sheets.append(path)
    return sheets


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else BUILD / "stills"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else BUILD / "sheet"
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    for p in contact_sheets(src, out, per):
        print(p)
