#!/usr/bin/env python3
import json, math, os, sys
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont

OUT = os.environ.get('OUTPUT', 'assets/dragon-contribution.gif')
DATA = os.environ.get('DATA', 'contributions.json')
WIDTH = 1000
HEIGHT = 270
BG = (8, 12, 20, 255)
GRID_X = 70
GRID_Y = 55
CELL = 11
GAP = 3
LEVELS = [
    (12, 18, 24, 32),
    (13, 40, 38, 50),
    (14, 66, 55, 62),
    (23, 217, 167, 255),
    (72, 238, 208, 255),
]
CYAN = (0, 217, 255, 255)
WHITE = (240, 248, 255, 255)
DARK = (14, 20, 28, 255)

try:
    font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 12)
    font_bold = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 18)
except Exception:
    font_small = font_bold = ImageFont.load_default()

@dataclass
class Day:
    date: str
    count: int
    level: int


def load_days(path):
    with open(path, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    return [Day(d['date'], int(d['count']), int(d.get('level', 0))) for d in raw]


def build_grid(days):
    # GitHub calendar data is returned chronologically. Pad so the final 7-day
    # column alignment is preserved, then cap at 53 columns.
    if not days:
        return []
    n = len(days)
    pad = (7 - (n % 7)) % 7
    padded = [None] * pad + days
    cols = []
    for i in range(0, len(padded), 7):
        cols.append(padded[i:i+7])
    return cols[-53:]


def contribution_color(level):
    if level <= 0:
        return (22, 27, 34, 255)
    idx = min(level, 4) + 0
    return LEVELS[idx][0:4]


def dragon_points(cx, cy, scale=1.0):
    # Compact pixel-ish dragon silhouette; deliberately uses vector primitives
    # so no external image asset is required.
    s = scale
    body = [
        (cx - 30*s, cy + 5*s), (cx - 20*s, cy - 10*s),
        (cx - 3*s, cy - 9*s), (cx + 7*s, cy - 18*s),
        (cx + 24*s, cy - 13*s), (cx + 32*s, cy - 3*s),
        (cx + 24*s, cy + 8*s), (cx + 8*s, cy + 10*s),
        (cx - 3*s, cy + 18*s), (cx - 20*s, cy + 19*s)
    ]
    wing = [(cx - 2*s, cy - 7*s), (cx + 7*s, cy - 35*s),
            (cx + 26*s, cy - 25*s), (cx + 14*s, cy - 10*s)]
    tail = [(cx - 22*s, cy + 12*s), (cx - 40*s, cy + 20*s),
            (cx - 32*s, cy + 7*s), (cx - 48*s, cy + 4*s),
            (cx - 24*s, cy - 1*s)]
    head = [(cx + 16*s, cy - 5*s), (cx + 33*s, cy - 15*s),
            (cx + 52*s, cy - 9*s), (cx + 58*s, cy + 2*s),
            (cx + 48*s, cy + 12*s), (cx + 30*s, cy + 10*s)]
    jaw = [(cx + 44*s, cy + 7*s), (cx + 61*s, cy + 10*s),
           (cx + 50*s, cy + 18*s), (cx + 36*s, cy + 13*s)]
    return body, wing, tail, head, jaw


def draw_dragon(draw, cx, cy, scale=1.0, facing=1, bite=False):
    # Mirror horizontally when facing left.
    parts = dragon_points(cx, cy, scale)
    if facing == -1:
        parts = [[(2*cx-x, y) for x, y in pts] for pts in parts]
    body, wing, tail, head, jaw = parts
    draw.polygon(body, fill=(17, 196, 155, 255), outline=(0, 242, 210, 255))
    draw.polygon(wing, fill=(13, 150, 135, 255), outline=(0, 242, 210, 255))
    draw.polygon(tail, fill=(12, 152, 126, 255), outline=(0, 220, 190, 255))
    draw.polygon(head, fill=(34, 220, 179, 255), outline=(0, 242, 210, 255))
    draw.polygon(jaw, fill=(21, 188, 151, 255), outline=(0, 242, 210, 255))
    eye_x = cx + 45*scale*facing
    draw.ellipse((eye_x-2*scale, cy-9*scale, eye_x+3*scale, cy-4*scale), fill=(255, 255, 255, 255))
    draw.ellipse((eye_x+1*scale, cy-8*scale, eye_x+3*scale, cy-5*scale), fill=(5, 10, 15, 255))
    if bite:
        mouth_x = cx + 55*scale*facing
        for i in range(3):
            x = mouth_x + i*8*scale*facing
            draw.line((x, cy+11*scale, x-4*scale*facing, cy+3*scale), fill=(255, 236, 140, 255), width=max(1, int(2*scale)))
        draw.ellipse((mouth_x-4*scale, cy+10*scale, mouth_x+6*scale, cy+20*scale), fill=(255, 178, 40, 210))


def main():
    os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
    days = load_days(DATA)
    cols = build_grid(days)
    if not cols:
        raise SystemExit('No contribution data found')

    # Flatten contribution cells in serpentine order so the dragon visibly
    # travels through the calendar rather than only across one row.
    path = []
    for x, col in enumerate(cols):
        rows = range(7) if x % 2 == 0 else range(6, -1, -1)
        for y in rows:
            if col[y] is not None:
                path.append((x, y))

    # 2 passes, skipping some empty cells to keep the GIF small.
    sampled = path[::3]
    frames = []
    durations = []
    eaten = set()
    for frame_index, (gx, gy) in enumerate(sampled):
        eaten.add((gx, gy))
        img = Image.new('RGBA', (WIDTH, HEIGHT), BG)
        d = ImageDraw.Draw(img)
        d.text((GRID_X, 14), 'GITHUB CONTRIBUTIONS', font=font_bold, fill=WHITE)
        d.text((GRID_X + 235, 18), '🐉 DRAGON MODE', font=font_small, fill=(0, 217, 255, 255))
        for x, col in enumerate(cols):
            for y in range(7):
                px = GRID_X + x * (CELL + GAP)
                py = GRID_Y + y * (CELL + GAP)
                day = col[y]
                level = day.level if day else 0
                color = contribution_color(level)
                if (x, y) in eaten:
                    color = (7, 18, 24, 255)
                d.rounded_rectangle((px, py, px+CELL, py+CELL), radius=2, fill=color)
                if (x, y) in eaten and day and day.count > 0:
                    d.line((px+2, py+CELL-3, px+CELL-3, py+2), fill=(0, 90, 110, 255), width=1)
        dx = GRID_X + gx * (CELL + GAP) + 8
        dy = GRID_Y + gy * (CELL + GAP) + 6
        facing = 1 if (gx % 2 == 0) else -1
        # pulse scale during bite
        pulse = 1.0 + 0.08 * math.sin(frame_index * 0.9)
        draw_dragon(d, dx, dy, scale=pulse, facing=facing, bite=True)
        d.text((GRID_X, HEIGHT-30), f'{sum(1 for _ in eaten)} contributions consumed', font=font_small, fill=(170, 190, 205, 255))
        frames.append(img.convert('P', palette=Image.Palette.ADAPTIVE, colors=128))
        durations.append(70)

    # Final hold.
    for _ in range(4):
        frames.append(frames[-1])
        durations.append(150)

    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=False, disposal=2)
    print(f'Wrote {OUT} ({os.path.getsize(OUT):,} bytes, {len(frames)} frames)')


if __name__ == '__main__':
    main()
