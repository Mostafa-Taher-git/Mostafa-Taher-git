#!/usr/bin/env python3
"""Dragon contribution eater — Game of Thrones style.

A Drogon-like obsidian dragon (the same beast that guards
assets/dragon-banner.png) flies across the GitHub contribution calendar and
burns it away with blue dragonfire.

Usage:
    DATA=contributions.json OUTPUT=assets/dragon-contribution.gif \
        SPRITE=assets/dragon-sprite.png python generate_dragon.py

If DATA is missing a demo calendar is generated, so the script can be run
locally to preview the animation.
"""
import json
import math
import os
import random
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.environ.get("OUTPUT", "assets/dragon-contribution.gif")
DATA = os.environ.get("DATA", "contributions.json")
SPRITE = os.environ.get("SPRITE", "assets/dragon-sprite.png")

WIDTH, HEIGHT = 1000, 320

# Palette lifted from the banner: obsidian night, dragonfire cyan, ember gold.
BG_TOP = (7, 11, 22)
BG_BOTTOM = (12, 18, 34)
EMBER = (255, 146, 48)
CYAN = (0, 200, 255)
ICE = (150, 226, 255)
WHITE = (226, 240, 255)
MUTED = (116, 142, 174)

GRID_X, GRID_Y = 62, 118
CELL, GAP = 11, 3

LEVELS = [
    (20, 28, 46),
    (14, 60, 96),
    (16, 104, 158),
    (24, 156, 214),
    (120, 220, 255),
]

DRAGON_H = 132          # rendered dragon height in px
MOUTH = (0.985, 0.47)   # mouth position as a fraction of the sprite box


def _font(names, size):
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


SERIF_B = ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
SANS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
SANS_B = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]

font_title = _font(SERIF_B, 20)
font_small = _font(SANS, 11)
font_label = _font(SANS_B, 11)


@dataclass
class Day:
    date: str
    count: int
    level: int


def load_days(path):
    if not os.path.exists(path):
        random.seed(11)
        return [
            Day(f"demo-{i}", random.randint(0, 16), random.choice([0, 0, 1, 1, 2, 2, 3, 4]))
            for i in range(371)
        ]
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Day(d["date"], int(d["count"]), int(d.get("level", 0))) for d in raw]


def build_grid(days):
    if not days:
        return []
    pad = (7 - (len(days) % 7)) % 7
    padded = [None] * pad + days
    cols = [padded[i:i + 7] for i in range(0, len(padded), 7)]
    return cols[-53:]


def contribution_color(level):
    return LEVELS[max(0, min(level, 4))]


def load_sprite():
    img = Image.open(SPRITE).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    scale = DRAGON_H / img.height
    return img.resize((max(1, int(img.width * scale)), DRAGON_H), Image.LANCZOS)


def breathe(canvas, x, y, facing, phase, length=120):
    """Blue dragonfire jet leaving the dragon's jaws."""
    fire = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(fire)
    for i in range(14):
        t = i / 13
        fx = x + facing * (6 + t * length)
        fy = y + math.sin(phase * 1.6 + t * 3.4) * 7 + t * 10
        r = (13 - i * 0.75) * (1.0 + 0.12 * math.sin(phase * 3))
        a = int(230 - t * 190)
        fd.ellipse((fx - r, fy - r, fx + r, fy + r),
                   fill=(90 + int(t * 140), 200 + int(t * 50), 255, max(0, a)))
    canvas.alpha_composite(fire.filter(ImageFilter.GaussianBlur(4)))


def background():
    bg = Image.new("RGBA", (WIDTH, HEIGHT))
    d = ImageDraw.Draw(bg)
    for y in range(HEIGHT):
        t = y / HEIGHT
        d.line([(0, y), (WIDTH, y)], fill=(
            int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t),
            int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t),
            int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t), 255))

    haze = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    hd = ImageDraw.Draw(haze)
    hd.ellipse((-220, HEIGHT - 46, WIDTH + 220, HEIGHT + 130), fill=(255, 118, 26, 64))
    hd.ellipse((-180, 150, 460, 340), fill=(0, 128, 220, 40))
    hd.ellipse((640, -80, 1180, 180), fill=(0, 110, 200, 34))
    bg.alpha_composite(haze.filter(ImageFilter.GaussianBlur(46)))

    d = ImageDraw.Draw(bg)
    d.rectangle((6, 6, WIDTH - 7, HEIGHT - 7), outline=(28, 56, 92), width=1)
    d.line((6, 6, 210, 6), fill=CYAN, width=2)
    d.line((WIDTH - 211, HEIGHT - 8, WIDTH - 7, HEIGHT - 8), fill=EMBER, width=2)

    d.text((GRID_X, 28), "THE DRAGON FEEDS", font=font_title, fill=WHITE)
    d.text((GRID_X, 56), "MOSTAFA  TAHER   ·   SULTAN  OF  TECH", font=font_small, fill=MUTED)
    return bg


def main():
    cols = build_grid(load_days(DATA))
    if not cols:
        raise SystemExit("no contribution data")

    sprite = load_sprite()
    sprite_flip = sprite.transpose(Image.FLIP_LEFT_RIGHT)

    path = []
    for x, col in enumerate(cols):
        rows = range(7) if x % 2 == 0 else range(6, -1, -1)
        for y in rows:
            if col[y] is not None:
                path.append((x, y))
    sampled = path[::8]

    bg = background()
    frames, durations = [], []
    eaten = set()
    burned = 0

    for i, (gx, gy) in enumerate(sampled):
        eaten.add((gx, gy))
        day = cols[gx][gy]
        burned += day.count if day else 0

        img = bg.copy()
        d = ImageDraw.Draw(img)

        for x, col in enumerate(cols):
            for y in range(7):
                px = GRID_X + x * (CELL + GAP)
                py = GRID_Y + y * (CELL + GAP)
                cell = col[y]
                if (x, y) in eaten:
                    d.rounded_rectangle((px, py, px + CELL, py + CELL), radius=2,
                                        fill=(13, 17, 30), outline=(30, 48, 74))
                    if cell and cell.count:
                        d.line((px + 3, py + CELL - 3, px + CELL - 3, py + 3),
                               fill=(56, 94, 132), width=1)
                else:
                    d.rounded_rectangle((px, py, px + CELL, py + CELL), radius=2,
                                        fill=contribution_color(cell.level if cell else 0))

        gx_px = GRID_X + gx * (CELL + GAP) + CELL // 2
        gy_px = GRID_Y + gy * (CELL + GAP) + CELL // 2
        facing = 1 if (gx % 2 == 0) else -1

        # Wing-beat bob.
        bob = math.sin(i * 0.6) * 5
        art = sprite if facing == 1 else sprite_flip
        mouth_dx = (MOUTH[0] if facing == 1 else 1 - MOUTH[0]) * art.width
        mouth_dy = MOUTH[1] * art.height
        mouth_x = gx_px - facing * 96
        mouth_y = gy_px - 14 + bob
        ox = min(max(int(mouth_x - mouth_dx), 8), WIDTH - art.width - 8)
        mouth_x = ox + mouth_dx
        img.alpha_composite(art, (ox, int(mouth_y - mouth_dy)))
        breathe(img, mouth_x, mouth_y, facing, i * 0.7,
                length=max(30.0, abs(gx_px - mouth_x) + 14))

        d = ImageDraw.Draw(img)
        d.text((GRID_X, HEIGHT - 36), f"{len(eaten)} DAYS CONSUMED", font=font_label, fill=ICE)
        d.text((GRID_X + 160, HEIGHT - 36), f"{burned} CONTRIBUTIONS BURNED",
               font=font_small, fill=MUTED)
        d.text((WIDTH - 250, HEIGHT - 36), "BUILD · BREAK · LEARN · REPEAT",
               font=font_small, fill=MUTED)

        frames.append(img.convert("RGB").convert(
            "P", palette=Image.Palette.ADAPTIVE, colors=128))
        durations.append(70)

    for _ in range(6):
        frames.append(frames[-1])
        durations.append(140)

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    frames[0].save(OUT, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True, disposal=2)
    print(f"Wrote {OUT} ({os.path.getsize(OUT):,} bytes, {len(frames)} frames)")


if __name__ == "__main__":
    main()
