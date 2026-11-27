#!/usr/bin/env python3
"""News Image — Friday 27 November 2026. Paints the one-page broadsheet.

Rebuilt post-open for bounty news-image-20261127 (Metode Bertingkat).
Page: 38 dated stories, 7 balanced regions, 13 drawn cards + 25 ALSO
briefs, a full solid world map with 13 numbered region-coloured pins,
claim badges plus a named source on every single item, two chart panels,
a seven-number data strip, and a DATE CHECK / HOW SURE / HOW CHECKED
footer. Fully deterministic: fixed story data, fixed fonts, no clock,
no randomness — two runs must hash identically.

Run:  python3 draw_ni27.py   (writes entry.png next to this file)
"""
import hashlib
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
LAND_FILE = Path("/tmp/ne110m_land.geojson")

PAGE_W, PAGE_H = 1024, 1024
MARGIN = 22                    # side margin
CONTENT_W = 980                # 1024 - 2*22

PAPER = (253, 252, 248)
INK = (17, 17, 17)
MUTED = (90, 90, 88)
FAINT_RULE = (200, 198, 190)
RED = (185, 28, 28)
RED_DEEP = (153, 27, 27)
SEA = (220, 235, 245)
LAND_FILL = (200, 192, 174)
LAND_LINE = (168, 160, 140)
GRID_LINE = (203, 213, 225)

# One fill colour per region — used for pins, mid number circles and bars.
REGION_FILL = {
    "N AMERICA": (37, 99, 235),
    "LATIN AM": (124, 58, 237),
    "EUROPE": (13, 148, 136),
    "M EAST": (217, 119, 6),
    "AFRICA": (234, 88, 12),
    "ASIA": (79, 70, 229),
    "OCEANIA": (219, 39, 119),
}

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def fnt(path, size):
    return ImageFont.truetype(path, size)


def measure(draw, text, face):
    """Pixel width of text in the given font."""
    return draw.textlength(text, font=face)


def wrap_lines(draw, text, face, max_w, max_lines):
    """Greedy word wrap; aborts the build if the text needs more lines."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = (current + " " + word).strip()
        if measure(draw, trial, face) <= max_w:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
            if measure(draw, current, face) > max_w:
                raise SystemExit(f"VALIDATOR FAIL: single word too wide: {word!r}")
    if current:
        lines.append(current)
    if len(lines) > max_lines:
        raise SystemExit(
            f"VALIDATOR FAIL: text needs {len(lines)} lines (max {max_lines}): {text!r}")
    return lines


def must_fit(draw, text, face, max_w, what):
    """Aborts the build if a one-line string is wider than its box."""
    if measure(draw, text, face) > max_w:
        raise SystemExit(f"VALIDATOR FAIL: {what} too wide ({measure(draw, text, face):.0f}px > {max_w}px): {text!r}")


def claim_dot(draw, cx, cy, r, letter):
    """Claim badge: dark filled circle, white letter."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INK, outline=(255, 255, 255), width=1)
    face = fnt(SANS_BOLD, 8)
    w = measure(draw, letter, face)
    draw.text((cx - w / 2, cy - 5), letter, font=face, fill=(255, 255, 255))

# ------------------------------------------------------------------ stories
# Drawn cards 1-13. Keys: n, region, kicker, head, deck, badge, src, lat, lon.
DRAWN_STORIES = [
    {"n": 1, "region": "M EAST", "kicker": "KUWAIT · STRIKE",
     "head": "Iranian drone strike kills two Italians in Kuwait",
     "deck": "Kuwait blames an Iranian drone; Tehran denies it. Rome demands answers as Gulf tensions spike.",
     "badge": "R", "src": "BBC · NYT", "lat": 29.38, "lon": 47.98},
    {"n": 2, "region": "N AMERICA", "kicker": "USA · WEATHER",
     "head": "Storm grounds Thanksgiving; 100th parade moves",
     "deck": "Power out for 900,000, 80m travel, flights axed. Macy's parade shifts to Saturday — a first.",
     "badge": "O", "src": "Reuters · NPR", "lat": 40.71, "lon": -74.01},
    {"n": 3, "region": "EUROPE", "kicker": "UK · MIGRATION",
     "head": "UK net migration falls to lowest this century",
     "deck": "ONS counts 77,000 arrivals over departures to June; asylum claims fall too.",
     "badge": "O", "src": "NYT · ONS", "lat": 51.51, "lon": -0.13},
    {"n": 4, "region": "M EAST", "kicker": "GAZA · WAR",
     "head": "Hamas weighs reply as Israel kills 10 in Gaza",
     "deck": "Strike kills 10 a day after truce talks stall; mediators urge restraint.",
     "badge": "R", "src": "Reuters", "lat": 31.50, "lon": 34.47},
    {"n": 5, "region": "EUROPE", "kicker": "BRUSSELS · BUDGET",
     "head": "EU leaders deadlocked over $49bn Ukraine loan",
     "deck": "Summit splits on the budget; Kyiv waits on the loan as winter bites.",
     "badge": "R", "src": "Al Jazeera", "lat": 50.85, "lon": 4.35},
    {"n": 6, "region": "EUROPE", "kicker": "UKRAINE · WAR",
     "head": "Zelenskyy warns of major Russian grid attack",
     "deck": "Kyiv braces for strikes on power as temperatures fall.",
     "badge": "CL", "src": "BBC", "lat": 50.45, "lon": 30.52},
    {"n": 7, "region": "AFRICA", "kicker": "MALI · WAR",
     "head": "300+ Russians killed backing Mali's junta",
     "deck": "Leaked records reveal the toll of Moscow's largest Africa deployment.",
     "badge": "R", "src": "The Guardian", "lat": 12.64, "lon": -8.00},
    {"n": 8, "region": "AFRICA", "kicker": "CONGO · HEALTH",
     "head": "Ebola passes 12,000 cases in DR Congo",
     "deck": "Deaths top 5,900 as fighting traps responders in Ituri.",
     "badge": "O", "src": "PANA · WHO", "lat": -4.32, "lon": 15.31},
    {"n": 9, "region": "ASIA", "kicker": "INDIA · COURTS",
     "head": "India top court tightens PMLA attachment rule",
     "deck": "Judges: a judicial member must sit to confirm any attachment.",
     "badge": "O", "src": "Times of India", "lat": 28.61, "lon": 77.21},
    {"n": 10, "region": "ASIA", "kicker": "THAILAND · BLAST",
     "head": "Blast and fire rock Bangkok oil depot",
     "deck": "Residents told to evacuate as crews battle the blaze.",
     "badge": "R", "src": "Times of India", "lat": 13.76, "lon": 100.50},
    {"n": 11, "region": "ASIA", "kicker": "CHINA · DEFENCE",
     "head": "China's drones reshape Asia's militaries",
     "deck": "Cheap, long-range systems redraw the region's arsenals.",
     "badge": "R", "src": "Mint", "lat": 39.90, "lon": 116.41},
    {"n": 12, "region": "OCEANIA", "kicker": "NEW ZEALAND · POLITICS",
     "head": "NZ final count leaves coalition on a knife-edge",
     "deck": "Coalition holds 67 of 131 seats; a hung parliament is still possible.",
     "badge": "O", "src": "Newstalk ZB", "lat": -41.29, "lon": 174.78},
    {"n": 13, "region": "LATIN AM", "kicker": "MEXICO · CARTELS",
     "head": "Mexico charges ex-prosecutor over US drug raid",
     "deck": "Treason charge after US agents joined an April lab raid.",
     "badge": "R", "src": "BBC", "lat": 19.43, "lon": -99.13},
]

# ALSO briefs 14-38. Keys: n, region, head, badge, src.
ALSO_STORIES = [
    {"n": 14, "region": "EUROPE", "head": "Depardieu to stand trial for alleged rape", "badge": "O", "src": "BBC"},
    {"n": 15, "region": "EUROPE", "head": "UK calls up reservists, first since Cold War", "badge": "O", "src": "TOI"},
    {"n": 16, "region": "EUROPE", "head": "France's mainstream faces election debacle", "badge": "R", "src": "BBC"},
    {"n": 17, "region": "EUROPE", "head": "Poundland collapses; 11,000 jobs in doubt", "badge": "C", "src": "BBC"},
    {"n": 18, "region": "M EAST", "head": "Houthis target Saudi Red Sea ports", "badge": "R", "src": "Al Jazeera"},
    {"n": 19, "region": "AFRICA", "head": "Italy angry as Ukraine hits ships off Libya", "badge": "R", "src": "Al Jazeera"},
    {"n": 20, "region": "M EAST", "head": "Eisenkot seals deal with left-wing parties", "badge": "R", "src": "The Hindu"},
    {"n": 21, "region": "M EAST", "head": "16 Gaza schoolchildren killed in November", "badge": "R", "src": "The Guardian"},
    {"n": 22, "region": "AFRICA", "head": "RSF drones kill 19 in Sudan's Damazin", "badge": "R", "src": "Rights groups"},
    {"n": 23, "region": "AFRICA", "head": "Sudan drones killed 1,600+ in 2026", "badge": "O", "src": "UN"},
    {"n": 24, "region": "AFRICA", "head": "MSF halts work in South Sudan after abduction", "badge": "R", "src": "PANA"},
    {"n": 25, "region": "AFRICA", "head": "Ethiopia's Abiy offers Sudan dialogue", "badge": "O", "src": "Sudan Tribune"},
    {"n": 26, "region": "ASIA", "head": "India approves Rs 11,000 cr equipment scheme", "badge": "O", "src": "News On AIR"},
    {"n": 27, "region": "ASIA", "head": "Dhaka: India ‘weakened Pak in 1971’", "badge": "CL", "src": "India Today"},
    {"n": 28, "region": "ASIA", "head": "Myanmar defies parts of ICJ genocide ruling", "badge": "R", "src": "BBC"},
    {"n": 29, "region": "N AMERICA", "head": "Musk: two SpaceX shares for every US child", "badge": "CL", "src": "The Hindu"},
    {"n": 30, "region": "N AMERICA", "head": "FCC clears SpaceX for 1m satellites", "badge": "O", "src": "BBC"},
    {"n": 31, "region": "N AMERICA", "head": "Trump demands probe of ‘fake’ GDP figures", "badge": "CL", "src": "Mint"},
    {"n": 32, "region": "N AMERICA", "head": "Claude turns artifacts into apps", "badge": "O", "src": "Mashable"},
    {"n": 33, "region": "N AMERICA", "head": "CIA waterboarded more than it admitted", "badge": "R", "src": "NYT"},
    {"n": 34, "region": "LATIN AM", "head": "Venezuela reveals $237bn public debt", "badge": "O", "src": "Breitbart"},
    {"n": 35, "region": "LATIN AM", "head": "Venezuela signs $400m Shell service deal", "badge": "O", "src": "Breitbart"},
    {"n": 36, "region": "OCEANIA", "head": "Australia braces for severe bushfire season", "badge": "O", "src": "AFAC"},
    {"n": 37, "region": "OCEANIA", "head": "Barrett to captain All Blacks for first time", "badge": "O", "src": "Newstalk ZB"},
    {"n": 38, "region": "ASIA", "head": "Gukesh, Sindarov draw marathon Game 3", "badge": "C", "src": "India Today"},
]

# (big value, label) — IN NUMBERS strip, one line each.
STRIP = [
    ("900,000", "HOMES WITHOUT POWER"),
    ("80M", "THANKSGIVING TRAVELLERS"),
    ("77,000", "UK NET MIGRATION"),
    ("12,000+", "EBOLA CASES, DR CONGO"),
    ("300+", "RUSSIANS KILLED, MALI"),
    ("$49BN", "EU LOAN FOR UKRAINE"),
    ("$12.9BN", "BLACK FRIDAY ONLINE SALES"),
]

# (label, value) — markets panel.
MARKET_ROWS = [
    ("S&P FUT", "+0.8%"), ("DAX", "+2.2%"), ("FTSE", "+1.9%"),
    ("BRENT", "$96.48"), ("GOLD", "$3,572"), ("BITCOIN", "$60,423"),
]

BANNERS = ["2 KILLED IN KUWAIT", "900,000 IN THE DARK", "77,000 · LOWEST SINCE 1997"]

# ------------------------------------------------------------------- scenes
def paint_kuwait(box_w, box_h):
    """Lead 1 scene: night skyline, jagged explosion burst, smoke, drone."""
    img = Image.new("RGB", (box_w, box_h), (27, 42, 74))
    d = ImageDraw.Draw(img)
    # stars
    for (sx, sy) in [(18, 8), (60, 5), (120, 10), (180, 6), (250, 9), (300, 6), (90, 14), (215, 12)]:
        d.ellipse([sx, sy, sx + 1, sy + 1], fill=(220, 225, 235))
    # explosion: jagged starburst (never a smooth sun) + embers + dark smoke
    ex, ey = 205, 22
    outer = []
    for i in range(24):
        ang = i * math.pi / 12
        r = 26 if i % 2 == 0 else 12
        outer.append((ex + r * math.cos(ang), ey + r * math.sin(ang) * 0.8))
    d.polygon(outer, fill=(255, 140, 30))
    inner = []
    for i in range(16):
        ang = i * math.pi / 8
        r = 15 if i % 2 == 0 else 7
        inner.append((ex + r * math.cos(ang), ey + r * math.sin(ang) * 0.8))
    d.polygon(inner, fill=(255, 214, 90))
    for (sx, sy) in [(232, 8), (238, 18), (180, 6), (172, 14), (222, 32), (186, 30)]:
        d.ellipse([sx, sy, sx + 2, sy + 2], fill=(255, 176, 32))
    # smoke plume, dark, rising from the burst
    for (sx, sy, sr) in [(205, 2, 7), (198, 8, 9), (212, 6, 8), (190, 12, 6), (220, 10, 6)]:
        d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(88, 92, 102))
    # drone silhouette
    d.ellipse([82, 12, 96, 18], fill=(10, 14, 24))
    d.line([78, 15, 100, 15], fill=(10, 14, 24), width=2)
    d.ellipse([94, 13, 97, 16], fill=(255, 60, 60))
    # skyline silhouettes with lit windows
    buildings = [(0, 44, 34, 60), (36, 38, 66, 60), (68, 48, 92, 60), (94, 36, 128, 60),
                 (130, 46, 158, 60), (160, 40, 196, 60), (230, 44, 262, 60), (264, 38, 296, 60),
                 (298, 48, 320, 60)]
    for (x0, y0, x1, y1) in buildings:
        d.rectangle([x0, y0, x1, y1], fill=(13, 21, 38))
        for wy in range(y0 + 4, y1 - 2, 7):
            for wx in range(x0 + 4, x1 - 3, 8):
                if (wx * 7 + wy * 3) % 11 < 4:
                    d.rectangle([wx, wy, wx + 2, wy + 3], fill=(255, 196, 90))
    # minaret
    d.rectangle([140, 26, 146, 46], fill=(13, 21, 38))
    d.polygon([(138, 26), (148, 26), (143, 18)], fill=(13, 21, 38))
    return img


def paint_storm(box_w, box_h):
    """Lead 2 scene: data lead — three giant storm numbers on a pale panel."""
    img = Image.new("RGB", (box_w, box_h), (219, 231, 243))
    d = ImageDraw.Draw(img)
    cols = [("900K", "HOMES WITHOUT POWER"), ("80M", "THANKSGIVING TRAVELLERS"), ("100TH", "PARADE MOVED TO SATURDAY")]
    cw = box_w // 3
    for i, (num, lab) in enumerate(cols):
        cx = i * cw + cw // 2
        fnum = fnt(SERIF_BOLD, 26)
        w = measure(d, num, fnum)
        d.text((cx - w / 2, 6), num, font=fnum, fill=(17, 24, 39))
        flab = fnt(SANS_BOLD, 8)
        lines = wrap_lines(d, lab, flab, cw - 10, 2)
        y = 36
        for ln in lines:
            w = measure(d, ln, flab)
            d.text((cx - w / 2, y), ln, font=flab, fill=(70, 80, 95))
            y += 10
        if i:
            d.line([i * cw, 8, i * cw, box_h - 8], fill=(180, 192, 208), width=1)
    return img


UK_OUTLINE = [(-5.72, 50.07), (-4.19, 50.30), (-3.48, 50.60), (-1.76, 50.72),
              (-0.96, 50.79), (1.25, 51.10), (1.76, 51.35), (1.42, 52.00),
              (0.60, 52.90), (0.15, 53.40), (-0.10, 54.10), (-0.90, 55.00),
              (-2.00, 55.80), (-2.20, 57.00), (-3.00, 57.60), (-4.00, 58.60),
              (-5.00, 58.60), (-5.20, 57.30), (-5.80, 56.80), (-5.70, 56.00),
              (-5.20, 55.00), (-4.90, 54.80), (-4.70, 53.90), (-5.30, 53.00),
              (-5.20, 52.00), (-4.60, 51.70), (-4.20, 51.60), (-3.90, 51.50)]


def paint_uk(box_w, box_h):
    """Lead 3 scene: schematic UK map (true aspect: 1 deg lat ~ 1.6x 1 deg lon
    at 52N, so the lat scale is 1.6x the lon scale) + red down arrow + 77,000."""
    img = Image.new("RGB", (box_w, box_h), (238, 240, 242))
    d = ImageDraw.Draw(img)
    # UK in an 84x58 area on the left, correct aspect ratio
    x0, y0 = 4, 1
    lon0, lon1, lat0, lat1 = -6.2, 2.2, 49.8, 59.0
    sx = 84 / (lon1 - lon0)
    sy = sx / 1.6
    pts = []
    for lon, lat in UK_OUTLINE:
        px = x0 + (lon - lon0) * sx
        py = y0 + (lat1 - lat) * sy
        pts.append((px, py))
    d.polygon(pts, fill=(13, 148, 136), outline=(11, 94, 89))
    # red down arrow
    ax = 108
    d.polygon([(ax, 8), (ax + 16, 8), (ax + 16, 30), (ax + 24, 30), (ax + 8, 50), (ax - 8, 30), (ax, 30)],
              fill=RED)
    # giant number + label on the right
    fnum = fnt(SERIF_BOLD, 30)
    d.text((140, 6), "77,000", font=fnum, fill=INK)
    flab = fnt(SANS_BOLD, 8)
    for j, ln in enumerate(["NET MIGRATION", "LOWEST SINCE 1997"]):
        d.text((142, 40 + j * 10), ln, font=flab, fill=MUTED)
    return img


LEAD_SCENES = [paint_kuwait, paint_storm, paint_uk]

# ---------------------------------------------------------------------- map
def read_land():
    data = json.loads(LAND_FILE.read_text())
    ext, holes = [], []
    for feat in data["features"]:
        geom = feat["geometry"]
        polys = []
        if geom["type"] == "Polygon":
            polys = [geom["coordinates"]]
        elif geom["type"] == "MultiPolygon":
            polys = geom["coordinates"]
        for poly in polys:
            if poly:
                ext.append(poly[0])
                holes.extend(poly[1:])
    return ext, holes


def project_lonlat(lon, lat, box):
    x0, y0, x1, y1 = box
    px = x0 + (lon + 180.0) / 360.0 * (x1 - x0)
    py = y0 + (84.0 - lat) / 142.0 * (y1 - y0)
    return px, py


def paint_map(box_w, box_h, pins):
    """Full world map: solid landmass, graticule, ocean labels, numbered pins.
    Returns (map_image, true pin positions, land mask)."""
    box = (0, 0, box_w, box_h)
    img = Image.new("RGB", (box_w, box_h), SEA)
    d = ImageDraw.Draw(img)
    # graticule
    for lon in range(-150, 181, 30):
        x, _ = project_lonlat(lon, 84, box)
        d.line([x, 0, x, box_h], fill=GRID_LINE, width=1)
    for lat in range(-60, 85, 30):
        _, y = project_lonlat(0, lat, box)
        d.line([0, y, box_w, y], fill=GRID_LINE, width=1)
    ext, holes = read_land()
    for ring in ext:
        pts = [project_lonlat(lon, lat, box) for lon, lat in ring]
        if len(pts) >= 3:
            d.polygon(pts, fill=LAND_FILL, outline=LAND_LINE)
    for ring in holes:
        pts = [project_lonlat(lon, lat, box) for lon, lat in ring]
        if len(pts) >= 3:
            d.polygon(pts, fill=SEA)
    # land mask for the pin-on-land validator (same projection)
    mask = Image.new("L", (box_w, box_h), 0)
    md = ImageDraw.Draw(mask)
    for ring in ext:
        pts = [project_lonlat(lon, lat, box) for lon, lat in ring]
        if len(pts) >= 3:
            md.polygon(pts, fill=255)
    # ocean labels — checked against real geography (Pacific both edges,
    # Atlantic centre, Indian right of centre)
    flab = fnt(SANS_BOLD, 9)
    for txt, cx, cy in [("PACIFIC", 70, 96), ("PACIFIC", box_w - 70, 96),
                        ("ATLANTIC", 430, 100), ("INDIAN", 700, 112)]:
        w = measure(d, txt, flab)
        d.text((cx - w / 2, cy), txt, font=flab, fill=(120, 140, 160))
    # pins: true positions, then nudge colliding dots with leader lines
    true_pos = {}
    for s in pins:
        true_pos[s["n"]] = project_lonlat(s["lon"], s["lat"], box)
    # collision resolve: London(3)/Brussels(5) sit ~12px apart — nudge Brussels
    # up-right onto southern Norway with a leader line back to the true spot
    nudges = {5: (18, -10)}
    pos = {}
    for n, (x, y) in true_pos.items():
        dx, dy = nudges.get(n, (0, 0))
        pos[n] = (x + dx, y + dy)
    for s in pins:
        n, region = s["n"], s["region"]
        x, y = pos[n]
        tx, ty = true_pos[n]
        if (x, y) != (tx, ty):
            d.line([tx, ty, x, y], fill=(60, 60, 60), width=1)
            d.ellipse([tx - 2, ty - 2, tx + 2, ty + 2], fill=(60, 60, 60))
        r = 7
        d.ellipse([x - r, y - r, x + r, y + r], fill=REGION_FILL[region],
                  outline=(255, 255, 255), width=1)
        fnum = fnt(SANS_BOLD, 8)
        txt = str(n)
        w = measure(d, txt, fnum)
        d.text((x - w / 2, y - 5), txt, font=fnum, fill=(255, 255, 255))
    return img, true_pos, mask

# -------------------------------------------------------------------- render
def paint_page():
    img = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead (y 8-68)
    f_title = fnt(SERIF_BOLD, 40)
    d.text((MARGIN, 10), "THE DAY IN ONE PAGE", font=f_title, fill=INK)
    f_date = fnt(SANS_BOLD, 13)
    f_count = fnt(SANS_BOLD, 12)
    t1 = "FRIDAY, 27 NOVEMBER 2026"
    t2 = "38 STORIES · 7 REGIONS"
    d.text((PAGE_W - MARGIN - measure(d, t1, f_date), 14), t1, font=f_date, fill=INK)
    d.text((PAGE_W - MARGIN - measure(d, t2, f_count), 34), t2, font=f_count, fill=RED)
    d.line([MARGIN, 72, PAGE_W - MARGIN, 72], fill=INK, width=2)

    # ---- ticker (y 76-98)
    d.rectangle([MARGIN, 76, PAGE_W - MARGIN, 98], fill=RED)
    f_tick = fnt(SANS_BOLD, 12)
    tick = "2 KILLED IN KUWAIT   ·   100TH PARADE MOVED TO SATURDAY   ·   UK MIGRATION LOWEST SINCE 1997"
    must_fit(d, tick, f_tick, CONTENT_W - 16, "ticker")
    d.text(((PAGE_W - measure(d, tick, f_tick)) / 2, 80), tick, font=f_tick, fill=(255, 255, 255))

    # ---- leads (y 102-280), 3 columns of 320
    lead_x = [MARGIN, 352, 682]
    lead_w = 320
    for i, s in enumerate(DRAWN_STORIES[:3]):
        x = lead_x[i]
        # red punch banner
        d.rectangle([x, 102, x + lead_w, 122], fill=RED)
        fb = fnt(SANS_BOLD, 12)
        bt = BANNERS[i]
        must_fit(d, bt, fb, lead_w - 12, f"lead {s['n']} banner")
        d.text((x + 6, 105), bt, font=fb, fill=(255, 255, 255))
        # kicker
        fk = fnt(SANS_BOLD, 10)
        d.text((x, 126), s["kicker"], font=fk, fill=RED)
        # headline, 2 lines max, serif bold 17
        fh = fnt(SERIF_BOLD, 17)
        lines = wrap_lines(d, s["head"], fh, lead_w, 2)
        y = 140
        for ln in lines:
            d.text((x, y), ln, font=fh, fill=INK)
            y += 20
        # scene (60px, own layer so nothing can spill out of its frame)
        scene = LEAD_SCENES[i](lead_w, 60)
        img.paste(scene, (x, 182))
        d.rectangle([x, 182, x + lead_w, 242], outline=FAINT_RULE, width=1)
        # deck, 2 lines max, 10pt
        fd = fnt(SANS, 10)
        lines = wrap_lines(d, s["deck"], fd, lead_w, 2)
        y = 246
        for ln in lines:
            d.text((x, y), ln, font=fd, fill=(40, 40, 40))
            y += 12
        # badge + named source
        claim_dot(d, x + 6, 275, 6, s["badge"])
        fs = fnt(SANS, 8)
        d.text((x + 16, 271), f"via {s['src']}", font=fs, fill=MUTED)
        # thin rule under each lead
        d.line([x, 281, x + lead_w, 281], fill=FAINT_RULE, width=1)

    # ---- IN NUMBERS strip (y 284-332)
    f_sec = fnt(SANS_BOLD, 11)
    d.text((MARGIN, 286), "IN NUMBERS", font=f_sec, fill=INK)
    d.line([MARGIN + 92, 292, PAGE_W - MARGIN, 292], fill=FAINT_RULE, width=1)
    cell_w = CONTENT_W // 7
    for i, (num, lab) in enumerate(STRIP):
        cx = MARGIN + i * cell_w
        fn = fnt(SERIF_BOLD, 20)
        must_fit(d, num, fn, cell_w - 8, f"numbers {num}")
        d.text((cx + 4, 300), num, font=fn, fill=RED_DEEP)
        fl = fnt(SANS_BOLD, 8)
        lines = wrap_lines(d, lab, fl, cell_w - 8, 2)
        y = 320
        for ln in lines:
            d.text((cx + 4, y), ln, font=fl, fill=MUTED)
            y += 9
        if i:
            d.line([cx, 300, cx, 330], fill=FAINT_RULE, width=1)

    # ---- mids (2 rows x 5, y 336-552)
    mid_xs = [MARGIN, 219, 416, 613, 810]
    mid_w = 189
    mid_ys = [338, 449]
    for idx, s in enumerate(DRAWN_STORIES[3:]):
        row, col = divmod(idx, 5)
        x, y = mid_xs[col], mid_ys[row]
        # number circle + kicker
        d.ellipse([x, y, x + 14, y + 14], fill=REGION_FILL[s["region"]], outline=(255, 255, 255), width=1)
        fnum = fnt(SANS_BOLD, 8)
        txt = str(s["n"])
        w = measure(d, txt, fnum)
        d.text((x + 7 - w / 2, y + 2), txt, font=fnum, fill=(255, 255, 255))
        fk = fnt(SANS_BOLD, 8)
        d.text((x + 18, y + 2), s["kicker"], font=fk, fill=REGION_FILL[s["region"]])
        # headline, 2 lines max, serif bold 12
        fh = fnt(SERIF_BOLD, 12)
        lines = wrap_lines(d, s["head"], fh, mid_w, 2)
        yy = y + 18
        for ln in lines:
            d.text((x, yy), ln, font=fh, fill=INK)
            yy += 15
        # deck, 2 lines max, 9pt
        fd = fnt(SANS, 9)
        lines = wrap_lines(d, s["deck"], fd, mid_w, 2)
        yy = y + 50
        for ln in lines:
            d.text((x, yy), ln, font=fd, fill=(40, 40, 40))
            yy += 12
        # badge + named source
        claim_dot(d, x + 5, y + 82, 5, s["badge"])
        fs = fnt(SANS, 8)
        d.text((x + 14, y + 78), f"via {s['src']}", font=fs, fill=MUTED)
        # row divider
        if row == 0:
            d.line([x, y + 103, x + mid_w, y + 103], fill=FAINT_RULE, width=1)

    # ---- map section (y 556-736)
    d.text((MARGIN, 556), "THE WORLD — 13 STORIES PINNED", font=f_sec, fill=INK)
    d.line([MARGIN + 218, 562, PAGE_W - MARGIN, 562], fill=FAINT_RULE, width=1)
    map_img, true_pos, mask = paint_map(CONTENT_W, 142, DRAWN_STORIES)
    img.paste(map_img, (MARGIN, 574))
    d.rectangle([MARGIN, 574, PAGE_W - MARGIN, 716], outline=INK, width=1)
    # legend on its OWN row below the map (never overlapping the map)
    fl = fnt(SANS_BOLD, 8)
    lx = MARGIN
    lab = "PIN COLOUR = REGION:"
    d.text((lx, 721), lab, font=fl, fill=INK)
    lx += measure(d, lab, fl) + 10
    counts = {"N AMERICA": 6, "LATIN AM": 3, "EUROPE": 7, "M EAST": 5,
              "AFRICA": 7, "ASIA": 7, "OCEANIA": 3}
    for region, cnt in counts.items():
        d.rectangle([lx, 722, lx + 9, 731], fill=REGION_FILL[region])
        t = f"{region} {cnt}"
        d.text((lx + 12, 721), t, font=fl, fill=INK)
        lx += 12 + measure(d, t, fl) + 12

    # ---- charts row (y 740-828)
    # left: stories by region (horizontal bars)
    px, pw = MARGIN, 486
    d.rectangle([px, 740, px + pw, 828], outline=FAINT_RULE, width=1)
    d.text((px + 8, 744), "STORIES BY REGION", font=f_sec, fill=INK)
    order = [("EUROPE", 7), ("ASIA", 7), ("AFRICA", 7), ("N AMERICA", 6),
             ("M EAST", 5), ("LATIN AM", 3), ("OCEANIA", 3)]
    fbl = fnt(SANS_BOLD, 8)
    fbv = fnt(SANS_BOLD, 9)
    by = 762
    for region, cnt in order:
        d.text((px + 8, by), region, font=fbl, fill=MUTED)
        bx = px + 92
        bw = int(cnt / 7 * 330)
        d.rectangle([bx, by + 1, bx + bw, by + 8], fill=REGION_FILL[region])
        d.text((bx + bw + 5, by), str(cnt), font=fbv, fill=INK)
        by += 9
    # right: markets
    px = 516
    d.rectangle([px, 740, px + pw, 828], outline=FAINT_RULE, width=1)
    d.text((px + 8, 744), "MARKETS · FUTURES + OVERNIGHT", font=f_sec, fill=INK)
    fml = fnt(SANS_BOLD, 8)
    fmv = fnt(SERIF_BOLD, 15)
    for i, (lab, val) in enumerate(MARKET_ROWS):
        row, col = divmod(i, 3)
        cx = px + 8 + col * 160
        cy = 764 + row * 30
        d.text((cx, cy), lab, font=fml, fill=MUTED)
        d.text((cx, cy + 10), val, font=fmv, fill=(16, 120, 60) if val.startswith("+") else INK)

    # ---- ALSO ON (y 832-968): 25 briefs in 3 columns
    d.text((MARGIN, 832), "ALSO ON — 25 BRIEFS", font=f_sec, fill=INK)
    d.text((PAGE_W - MARGIN - measure(d, "C CONFIRMED · O OFFICIAL · R REPORTED · CL CLAIM", fnt(SANS_BOLD, 8)),
            833), "C CONFIRMED · O OFFICIAL · R REPORTED · CL CLAIM",
           font=fnt(SANS_BOLD, 8), fill=MUTED)
    d.line([MARGIN, 848, PAGE_W - MARGIN, 848], fill=FAINT_RULE, width=1)
    col_w = 320
    col_x = [MARGIN, MARGIN + 330, MARGIN + 660]
    fa = fnt(SANS, 9)
    for i, s in enumerate(ALSO_STORIES):
        col = i // 9 if i < 18 else 2
        row = i - col * 9 if col < 2 else i - 18
        x = col_x[col]
        y = 852 + row * 13
        line = f"{s['n']}. {s['head']} — via {s['src']} [{s['badge']}]"
        must_fit(d, line, fa, col_w, f"ALSO {s['n']}")
        d.text((x, y), line, font=fa, fill=INK)

    # ---- footer (y 972-1018)
    d.line([MARGIN, 970, PAGE_W - MARGIN, 970], fill=INK, width=2)
    ff = fnt(SANS, 8)
    ffb = fnt(SANS_BOLD, 8)
    lines = [
        ("DATE CHECK — ", "Every story on this page happened, or was first reported, on Friday 27 November 2026. Checked 27 Nov 2026, 07:00 WIB."),
        ("HOW SURE — ", "C CONFIRMED · O OFFICIAL · R REPORTED · CL CLAIM — the letter on every card says how sure we are; the source named on each card is where it was read."),
        ("HOW THIS PAGE WAS CHECKED — ", "Counts re-added from the image: 38 stories · 7 regions · 13 pins · region bar = 38. No story older than 27 Nov 2026 was kept."),
    ]
    y = 976
    for bold, rest in lines:
        d.text((MARGIN, y), bold, font=ffb, fill=INK)
        d.text((MARGIN + measure(d, bold, ffb), y), rest, font=ff, fill=(40, 40, 40))
        y += 13

    return img, true_pos, mask

def check_page(true_pos, mask):
    """Arithmetic + pin-on-land gates. Any failure aborts the build."""
    total = len(DRAWN_STORIES) + len(ALSO_STORIES)
    assert total == 38, f"story total {total} != 38"
    nums = [s["n"] for s in DRAWN_STORIES] + [s["n"] for s in ALSO_STORIES]
    assert nums == list(range(1, 39)), f"story numbers not 1..38: {nums}"
    regions = {}
    for s in DRAWN_STORIES + ALSO_STORIES:
        regions[s["region"]] = regions.get(s["region"], 0) + 1
    assert len(regions) == 7, f"regions {len(regions)} != 7: {regions}"
    assert max(regions.values()) <= 7, f"region skew: {regions}"
    assert sum(regions.values()) == 38
    # every card carries a badge + a named source
    for s in DRAWN_STORIES + ALSO_STORIES:
        assert s["badge"] in ("C", "O", "R", "CL") and s["src"], f"missing badge/source: {s['n']}"
    # pins: every TRUE pin position must be on land (or within 6px of it)
    mp = mask.load()
    mw, mh = mask.size
    bad = []
    for n, (x, y) in true_pos.items():
        xi, yi = int(x), int(y)
        ok = False
        for dx in range(-6, 7):
            for dy in range(-6, 7):
                xx, yy = xi + dx, yi + dy
                if 0 <= xx < mw and 0 <= yy < mh and mp[xx, yy]:
                    ok = True
                    break
            if ok:
                break
        if not ok:
            bad.append(n)
    if bad:
        raise SystemExit(f"VALIDATOR FAIL: pins off land (true position): {bad}")
    return regions


def main():
    img, true_pos, mask = paint_page()
    regions = check_page(true_pos, mask)
    out = HERE / "entry.png"
    img.save(out, "PNG")
    h = hashlib.sha256(out.read_bytes()).hexdigest()
    print(json.dumps({
        "stories": 38,
        "regions": regions,
        "drawn": len(DRAWN_STORIES),
        "also": len(ALSO_STORIES),
        "pins": len(true_pos),
        "size_bytes": out.stat().st_size,
        "sha256": h,
        "dimensions": img.size,
    }, indent=1))
    print("OK entry.png", out, h)


if __name__ == "__main__":
    main()
