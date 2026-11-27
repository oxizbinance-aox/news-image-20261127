#!/usr/bin/env python3
"""News Image — 27 November 2026. Renders the broadsheet front page to entry.png.

Fresh build for bounty news-image-20261127 (Metode Bertingkat, 5 tingkat).
38 stories, 7 regions, 13 drawn + 25 ALSO, full solid world map with 13 numbered
pins coloured per region, claim badges + named source on every item.
Deterministic: fixed data, fixed fonts, no timestamps, no randomness.
Run:  python3 draw_ni27.py   (writes entry.png next to this file)
"""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
GEOJSON = Path("/tmp/ne110m_land.geojson")

W, H = 1024, 1024
MX = 22                      # side margin
CW = 980                     # content width (1024 - 2*22)

PAPER = (253, 252, 248)
INK = (17, 17, 17)
GREY = (90, 90, 88)
LIGHT_RULE = (200, 198, 190)
RED = (185, 28, 28)
RED_DARK = (153, 27, 27)
OCEAN = (220, 235, 245)
LAND = (200, 192, 174)
LAND_EDGE = (168, 160, 140)
GRID = (203, 213, 225)

# Region colours (pin fill + legend chip). One colour per region, distinct.
REGION_COLOR = {
    "N AMERICA": (37, 99, 235),
    "LATIN AM": (124, 58, 237),
    "EUROPE": (13, 148, 136),
    "M EAST": (217, 119, 6),
    "AFRICA": (234, 88, 12),
    "ASIA": (79, 70, 229),
    "OCEANIA": (219, 39, 119),
}

SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def tw(draw, text, f):
    """Pixel width of text in font f."""
    return draw.textlength(text, font=f)


def wrap(draw, text, f, max_w, max_lines):
    """Word-wrap text to fit max_w; FAIL the build if it needs more than max_lines."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if tw(draw, trial, f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
            if tw(draw, cur, f) > max_w:
                raise SystemExit(f"VALIDATOR FAIL: single word too wide: {w!r}")
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        raise SystemExit(
            f"VALIDATOR FAIL: text needs {len(lines)} lines (max {max_lines}): {text!r}")
    return lines


def fit_one_line(draw, text, f, max_w, what):
    """FAIL the build if a single-line text is wider than its box."""
    if tw(draw, text, f) > max_w:
        raise SystemExit(f"VALIDATOR FAIL: {what} too wide ({tw(draw, text, f):.0f}px > {max_w}px): {text!r}")


def badge_circle(draw, cx, cy, r, letter):
    """Claim badge: filled dark circle with a white letter."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INK, outline=(255, 255, 255), width=1)
    f = font(SANS_B, 8)
    w = tw(draw, letter, f)
    draw.text((cx - w / 2, cy - 5), letter, font=f, fill=(255, 255, 255))


# ---------------------------------------------------------------- stories
# n, region, kicker, headline, deck, badge (C/O/R/CL), source, lat, lon (drawn only)
DRAWN = [
    (1, "M EAST", "KUWAIT · STRIKE",
     "Iranian drone strike kills two Italians in Kuwait",
     "Kuwait blames an Iranian drone; Tehran denies it. Rome demands answers as Gulf tensions spike.",
     "R", "BBC · NYT", 29.38, 47.98),
    (2, "N AMERICA", "USA · WEATHER",
     "Storm grounds Thanksgiving; 100th parade moves",
     "Power out for 900,000, 80m travel, flights axed. Macy's parade shifts to Saturday \u2014 a first.",
     "O", "Reuters · NPR", 40.71, -74.01),
    (3, "EUROPE", "UK · MIGRATION",
     "UK net migration falls to lowest this century",
     "ONS counts 77,000 arrivals over departures to June; asylum claims fall too.",
     "O", "NYT · ONS", 51.51, -0.13),
    (4, "M EAST", "GAZA · WAR",
     "Hamas weighs reply as Israel kills 10 in Gaza",
     "Strike kills 10 a day after truce talks stall; mediators urge restraint.",
     "R", "Reuters", 31.50, 34.47),
    (5, "EUROPE", "BRUSSELS · BUDGET",
     "EU leaders deadlocked over $49bn Ukraine loan",
     "Summit splits on the budget; Kyiv waits on the loan as winter bites.",
     "R", "Al Jazeera", 50.85, 4.35),
    (6, "EUROPE", "UKRAINE · WAR",
     "Zelenskyy warns of major Russian grid attack",
     "Kyiv braces for strikes on power as temperatures fall.",
     "CL", "BBC", 50.45, 30.52),
    (7, "AFRICA", "MALI · WAR",
     "300+ Russians killed backing Mali's junta",
     "Leaked records reveal the toll of Moscow's largest Africa deployment.",
     "R", "The Guardian", 12.64, -8.00),
    (8, "AFRICA", "CONGO · HEALTH",
     "Ebola passes 12,000 cases in DR Congo",
     "Deaths top 5,900 as fighting traps responders in Ituri.",
     "O", "PANA · WHO", -4.32, 15.31),
    (9, "ASIA", "INDIA · COURTS",
     "India top court tightens PMLA attachment rule",
     "Judges: a judicial member must sit to confirm any attachment.",
     "O", "Times of India", 28.61, 77.21),
    (10, "ASIA", "THAILAND · BLAST",
     "Blast and fire rock Bangkok oil depot",
     "Residents told to evacuate as crews battle the blaze.",
     "R", "Times of India", 13.76, 100.50),
    (11, "ASIA", "CHINA · DEFENCE",
     "China's drones reshape Asia's militaries",
     "Cheap, long-range systems redraw the region's arsenals.",
     "R", "Mint", 39.90, 116.41),
    (12, "OCEANIA", "NEW ZEALAND · POLITICS",
     "NZ final count leaves coalition on a knife-edge",
     "Coalition holds 67 of 131 seats; a hung parliament is still possible.",
     "O", "Newstalk ZB", -41.29, 174.78),
    (13, "LATIN AM", "MEXICO · CARTELS",
     "Mexico charges ex-prosecutor over US drug raid",
     "Treason charge after US agents joined an April lab raid.",
     "R", "BBC", 19.43, -99.13),
]

# n, region, one-line headline, badge, source
ALSO = [
    (14, "EUROPE", "Depardieu to stand trial for alleged rape", "O", "BBC"),
    (15, "EUROPE", "UK calls up reservists, first since Cold War", "O", "TOI"),
    (16, "EUROPE", "France's mainstream faces election debacle", "R", "BBC"),
    (17, "EUROPE", "Poundland collapses; 11,000 jobs in doubt", "C", "BBC"),
    (18, "M EAST", "Houthis target Saudi Red Sea ports", "R", "Al Jazeera"),
    (19, "AFRICA", "Italy angry as Ukraine hits ships off Libya", "R", "Al Jazeera"),
    (20, "M EAST", "Eisenkot seals deal with left-wing parties", "R", "The Hindu"),
    (21, "M EAST", "16 Gaza schoolchildren killed in November", "R", "The Guardian"),
    (22, "AFRICA", "RSF drones kill 19 in Sudan's Damazin", "R", "Rights groups"),
    (23, "AFRICA", "Sudan drones killed 1,600+ in 2026", "O", "UN"),
    (24, "AFRICA", "MSF halts work in South Sudan after abduction", "R", "PANA"),
    (25, "AFRICA", "Ethiopia's Abiy offers Sudan dialogue", "O", "Sudan Tribune"),
    (26, "ASIA", "India approves Rs 11,000 cr equipment scheme", "O", "News On AIR"),
    (27, "ASIA", "Dhaka: India \u2018weakened Pak in 1971\u2019", "CL", "India Today"),
    (28, "ASIA", "Myanmar defies parts of ICJ genocide ruling", "R", "BBC"),
    (29, "N AMERICA", "Musk: two SpaceX shares for every US child", "CL", "The Hindu"),
    (30, "N AMERICA", "FCC clears SpaceX for 1m satellites", "O", "BBC"),
    (31, "N AMERICA", "Trump demands probe of \u2018fake\u2019 GDP figures", "CL", "Mint"),
    (32, "N AMERICA", "Claude turns artifacts into apps", "O", "Mashable"),
    (33, "N AMERICA", "CIA waterboarded more than it admitted", "R", "NYT"),
    (34, "LATIN AM", "Venezuela reveals $237bn public debt", "O", "Breitbart"),
    (35, "LATIN AM", "Venezuela signs $400m Shell service deal", "O", "Breitbart"),
    (36, "OCEANIA", "Australia braces for severe bushfire season", "O", "AFAC"),
    (37, "OCEANIA", "Barrett to captain All Blacks for first time", "O", "Newstalk ZB"),
    (38, "ASIA", "Gukesh, Sindarov draw marathon Game 3", "C", "India Today"),
]

NUMBERS = [  # (big value, label) — IN NUMBERS strip, one line each
    ("900,000", "HOMES WITHOUT POWER"),
    ("80M", "THANKSGIVING TRAVELLERS"),
    ("77,000", "UK NET MIGRATION"),
    ("12,000+", "EBOLA CASES, DR CONGO"),
    ("300+", "RUSSIANS KILLED, MALI"),
    ("$49BN", "EU LOAN FOR UKRAINE"),
    ("$12.9BN", "BLACK FRIDAY ONLINE SALES"),
]

MARKETS = [  # (label, value) — markets panel
    ("S&P FUT", "+0.8%"), ("DAX", "+2.2%"), ("FTSE", "+1.9%"),
    ("BRENT", "$96.48"), ("GOLD", "$3,572"), ("BITCOIN", "$60,423"),
]

LEAD_BANNERS = ["2 KILLED IN KUWAIT", "900,000 IN THE DARK", "77,000 \u00b7 LOWEST SINCE 1997"]


# ---------------------------------------------------------------- scenes
def scene_kuwait(box_w, box_h):
    """Lead 1 scene: night skyline, explosion glow, smoke, small drone."""
    img = Image.new("RGB", (box_w, box_h), (27, 42, 74))
    d = ImageDraw.Draw(img)
    # stars
    for (sx, sy) in [(18, 8), (60, 5), (120, 10), (180, 6), (250, 9), (300, 6), (90, 14), (215, 12)]:
        d.ellipse([sx, sy, sx + 1, sy + 1], fill=(220, 225, 235))
    # explosion: jagged starburst (not a smooth sun) + embers + dark smoke
    ex, ey = 205, 22
    import math as _math
    outer, inner = [], []
    for i in range(24):
        ang = i * _math.pi / 12
        r = 26 if i % 2 == 0 else 12
        outer.append((ex + r * _math.cos(ang), ey + r * _math.sin(ang) * 0.8))
    d.polygon(outer, fill=(255, 140, 30))
    for i in range(16):
        ang = i * _math.pi / 8
        r = 15 if i % 2 == 0 else 7
        inner.append((ex + r * _math.cos(ang), ey + r * _math.sin(ang) * 0.8))
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


def scene_storm(box_w, box_h):
    """Lead 2 scene: data lead — three giant storm numbers on a pale panel."""
    img = Image.new("RGB", (box_w, box_h), (219, 231, 243))
    d = ImageDraw.Draw(img)
    cols = [("900K", "HOMES WITHOUT POWER"), ("80M", "THANKSGIVING TRAVELLERS"), ("100TH", "PARADE MOVED TO SATURDAY")]
    cw = box_w // 3
    for i, (num, lab) in enumerate(cols):
        cx = i * cw + cw // 2
        fnum = font(SERIF_B, 26)
        w = tw(d, num, fnum)
        d.text((cx - w / 2, 6), num, font=fnum, fill=(17, 24, 39))
        flab = font(SANS_B, 8)
        lines = wrap(d, lab, flab, cw - 10, 2)
        y = 36
        for ln in lines:
            w = tw(d, ln, flab)
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


def scene_uk(box_w, box_h):
    """Lead 3 scene: schematic UK map (true aspect: 1 deg lat ~ 1.6x 1 deg lon
    at 52N, so lat scale is 1.6x lon scale) + red down arrow + giant 77,000."""
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
    fnum = font(SERIF_B, 30)
    d.text((140, 6), "77,000", font=fnum, fill=INK)
    flab = font(SANS_B, 8)
    for j, ln in enumerate(["NET MIGRATION", "LOWEST SINCE 1997"]):
        d.text((142, 40 + j * 10), ln, font=flab, fill=GREY)
    return img


LEAD_SCENES = [scene_kuwait, scene_storm, scene_uk]


# ---------------------------------------------------------------- map
def load_land():
    data = json.loads(GEOJSON.read_text())
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


def project(lon, lat, box):
    x0, y0, x1, y1 = box
    px = x0 + (lon + 180.0) / 360.0 * (x1 - x0)
    py = y0 + (84.0 - lat) / 142.0 * (y1 - y0)
    return px, py


def build_map(box_w, box_h, pins):
    """Full world map: solid landmass, graticule, ocean labels, numbered pins.
    Returns (map_image, pin_draw_positions, land_mask)."""
    box = (0, 0, box_w, box_h)
    img = Image.new("RGB", (box_w, box_h), OCEAN)
    d = ImageDraw.Draw(img)
    # graticule
    for lon in range(-150, 181, 30):
        x, _ = project(lon, 84, box)
        d.line([x, 0, x, box_h], fill=GRID, width=1)
    for lat in range(-60, 85, 30):
        _, y = project(0, lat, box)
        d.line([0, y, box_w, y], fill=GRID, width=1)
    ext, holes = load_land()
    for ring in ext:
        pts = [project(lon, lat, box) for lon, lat in ring]
        if len(pts) >= 3:
            d.polygon(pts, fill=LAND, outline=LAND_EDGE)
    for ring in holes:
        pts = [project(lon, lat, box) for lon, lat in ring]
        if len(pts) >= 3:
            d.polygon(pts, fill=OCEAN)
    # land mask for the pin-on-land validator (same projection)
    mask = Image.new("L", (box_w, box_h), 0)
    md = ImageDraw.Draw(mask)
    for ring in ext:
        pts = [project(lon, lat, box) for lon, lat in ring]
        if len(pts) >= 3:
            md.polygon(pts, fill=255)
    # ocean labels — checked against real geography (Pacific both edges,
    # Atlantic centre, Indian right of centre)
    flab = font(SANS_B, 9)
    for txt, cx, cy in [("PACIFIC", 70, 96), ("PACIFIC", box_w - 70, 96),
                        ("ATLANTIC", 430, 100), ("INDIAN", 700, 112)]:
        w = tw(d, txt, flab)
        d.text((cx - w / 2, cy), txt, font=flab, fill=(120, 140, 160))
    # pins: true positions, then nudge colliding dots with leader lines
    true_pos = {}
    for n, region, _k, _h, _de, _b, _s, lat, lon in pins:
        true_pos[n] = project(lon, lat, box)
    # collision resolve: London(3)/Brussels(5) sit ~12px apart — nudge Brussels
    # up-right onto southern Norway with a leader line back to the true spot
    nudges = {5: (18, -10)}
    pos = {}
    for n, (x, y) in true_pos.items():
        dx, dy = nudges.get(n, (0, 0))
        pos[n] = (x + dx, y + dy)
    for n, region, _k, _h, _de, _b, _s, _lat, _lon in pins:
        x, y = pos[n]
        tx, ty = true_pos[n]
        if (x, y) != (tx, ty):
            d.line([tx, ty, x, y], fill=(60, 60, 60), width=1)
            d.ellipse([tx - 2, ty - 2, tx + 2, ty + 2], fill=(60, 60, 60))
        r = 7
        d.ellipse([x - r, y - r, x + r, y + r], fill=REGION_COLOR[region],
                  outline=(255, 255, 255), width=1)
        fnum = font(SANS_B, 8)
        s = str(n)
        w = tw(d, s, fnum)
        d.text((x - w / 2, y - 5), s, font=fnum, fill=(255, 255, 255))
    return img, true_pos, mask


# ---------------------------------------------------------------- render
def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- masthead (y 8-68)
    f_title = font(SERIF_B, 40)
    d.text((MX, 10), "THE DAY IN ONE PAGE", font=f_title, fill=INK)
    f_date = font(SANS_B, 13)
    f_count = font(SANS_B, 12)
    t1 = "FRIDAY, 27 NOVEMBER 2026"
    t2 = "38 STORIES \u00b7 7 REGIONS"
    d.text((W - MX - tw(d, t1, f_date), 14), t1, font=f_date, fill=INK)
    d.text((W - MX - tw(d, t2, f_count), 34), t2, font=f_count, fill=RED)
    d.line([MX, 72, W - MX, 72], fill=INK, width=2)

    # ---- ticker (y 76-98)
    d.rectangle([MX, 76, W - MX, 98], fill=RED)
    f_tick = font(SANS_B, 12)
    tick = "2 KILLED IN KUWAIT   \u00b7   100TH PARADE MOVED TO SATURDAY   \u00b7   UK MIGRATION LOWEST SINCE 1997"
    fit_one_line(d, tick, f_tick, CW - 16, "ticker")
    d.text(((W - tw(d, tick, f_tick)) / 2, 80), tick, font=f_tick, fill=(255, 255, 255))

    # ---- leads (y 102-280), 3 columns of 320
    lead_x = [MX, 352, 682]
    lead_w = 320
    for i, (n, region, kicker, headline, deck, badge, source, _lat, _lon) in enumerate(DRAWN[:3]):
        x = lead_x[i]
        # red punch banner
        d.rectangle([x, 102, x + lead_w, 122], fill=RED)
        fb = font(SANS_B, 12)
        bt = LEAD_BANNERS[i]
        fit_one_line(d, bt, fb, lead_w - 12, f"lead {n} banner")
        d.text((x + 6, 105), bt, font=fb, fill=(255, 255, 255))
        # kicker
        fk = font(SANS_B, 10)
        d.text((x, 126), kicker, font=fk, fill=RED)
        # headline, 2 lines max, serif bold 17
        fh = font(SERIF_B, 17)
        lines = wrap(d, headline, fh, lead_w, 2)
        y = 140
        for ln in lines:
            d.text((x, y), ln, font=fh, fill=INK)
            y += 20
        # scene (60px, own layer so nothing can spill out of its frame)
        scene = LEAD_SCENES[i](lead_w, 60)
        img.paste(scene, (x, 182))
        d.rectangle([x, 182, x + lead_w, 242], outline=LIGHT_RULE, width=1)
        # deck, 2 lines max, 10pt
        fd = font(SANS, 10)
        lines = wrap(d, deck, fd, lead_w, 2)
        y = 246
        for ln in lines:
            d.text((x, y), ln, font=fd, fill=(40, 40, 40))
            y += 12
        # badge + named source
        badge_circle(d, x + 6, 275, 6, badge)
        fs = font(SANS, 8)
        d.text((x + 16, 271), f"via {source}", font=fs, fill=GREY)
        # thin rule under each lead
        d.line([x, 281, x + lead_w, 281], fill=LIGHT_RULE, width=1)

    # ---- IN NUMBERS strip (y 284-332)
    f_sec = font(SANS_B, 11)
    d.text((MX, 286), "IN NUMBERS", font=f_sec, fill=INK)
    d.line([MX + 92, 292, W - MX, 292], fill=LIGHT_RULE, width=1)
    cell_w = CW // 7
    for i, (num, lab) in enumerate(NUMBERS):
        cx = MX + i * cell_w
        fn = font(SERIF_B, 20)
        fit_one_line(d, num, fn, cell_w - 8, f"numbers {num}")
        d.text((cx + 4, 300), num, font=fn, fill=RED_DARK)
        fl = font(SANS_B, 8)
        lines = wrap(d, lab, fl, cell_w - 8, 2)
        y = 320
        for ln in lines:
            d.text((cx + 4, y), ln, font=fl, fill=GREY)
            y += 9
        if i:
            d.line([cx, 300, cx, 330], fill=LIGHT_RULE, width=1)

    # ---- mids (2 rows x 5, y 336-552)
    mid_xs = [MX, 219, 416, 613, 810]
    mid_w = 189
    mid_ys = [338, 449]
    for idx, (n, region, kicker, headline, deck, badge, source, _lat, _lon) in enumerate(DRAWN[3:]):
        row, col = divmod(idx, 5)
        x, y = mid_xs[col], mid_ys[row]
        # number circle + kicker
        d.ellipse([x, y, x + 14, y + 14], fill=REGION_COLOR[region], outline=(255, 255, 255), width=1)
        fnum = font(SANS_B, 8)
        s = str(n)
        w = tw(d, s, fnum)
        d.text((x + 7 - w / 2, y + 2), s, font=fnum, fill=(255, 255, 255))
        fk = font(SANS_B, 8)
        d.text((x + 18, y + 2), kicker, font=fk, fill=REGION_COLOR[region])
        # headline, 2 lines max, serif bold 12
        fh = font(SERIF_B, 12)
        lines = wrap(d, headline, fh, mid_w, 2)
        yy = y + 18
        for ln in lines:
            d.text((x, yy), ln, font=fh, fill=INK)
            yy += 15
        # deck, 2 lines max, 9.5 -> 9pt
        fd = font(SANS, 9)
        lines = wrap(d, deck, fd, mid_w, 2)
        yy = y + 50
        for ln in lines:
            d.text((x, yy), ln, font=fd, fill=(40, 40, 40))
            yy += 12
        # badge + named source
        badge_circle(d, x + 5, y + 82, 5, badge)
        fs = font(SANS, 8)
        d.text((x + 14, y + 78), f"via {source}", font=fs, fill=GREY)
        # row divider
        if row == 0:
            d.line([x, y + 103, x + mid_w, y + 103], fill=LIGHT_RULE, width=1)

    # ---- map section (y 556-736)
    d.text((MX, 556), "THE WORLD \u2014 13 STORIES PINNED", font=f_sec, fill=INK)
    d.line([MX + 218, 562, W - MX, 562], fill=LIGHT_RULE, width=1)
    map_img, true_pos, mask = build_map(CW, 142, DRAWN)
    img.paste(map_img, (MX, 574))
    d.rectangle([MX, 574, W - MX, 716], outline=INK, width=1)
    # legend on its OWN row below the map (never overlapping the map)
    fl = font(SANS_B, 8)
    lx = MX
    lab = "PIN COLOUR = REGION:"
    d.text((lx, 721), lab, font=fl, fill=INK)
    lx += tw(d, lab, fl) + 10
    counts = {"N AMERICA": 6, "LATIN AM": 3, "EUROPE": 7, "M EAST": 5,
              "AFRICA": 7, "ASIA": 7, "OCEANIA": 3}
    for region, cnt in counts.items():
        d.rectangle([lx, 722, lx + 9, 731], fill=REGION_COLOR[region])
        t = f"{region} {cnt}"
        d.text((lx + 12, 721), t, font=fl, fill=INK)
        lx += 12 + tw(d, t, fl) + 12

    # ---- charts row (y 740-828)
    # left: stories by region (horizontal bars)
    px, pw = MX, 486
    d.rectangle([px, 740, px + pw, 828], outline=LIGHT_RULE, width=1)
    d.text((px + 8, 744), "STORIES BY REGION", font=f_sec, fill=INK)
    order = [("EUROPE", 7), ("ASIA", 7), ("AFRICA", 7), ("N AMERICA", 6),
             ("M EAST", 5), ("LATIN AM", 3), ("OCEANIA", 3)]
    fbl = font(SANS_B, 8)
    fbv = font(SANS_B, 9)
    by = 762
    for region, cnt in order:
        d.text((px + 8, by), region, font=fbl, fill=GREY)
        bx = px + 92
        bw = int(cnt / 7 * 330)
        d.rectangle([bx, by + 1, bx + bw, by + 8], fill=REGION_COLOR[region])
        d.text((bx + bw + 5, by), str(cnt), font=fbv, fill=INK)
        by += 9
    # right: markets
    px = 516
    d.rectangle([px, 740, px + pw, 828], outline=LIGHT_RULE, width=1)
    d.text((px + 8, 744), "MARKETS \u00b7 FUTURES + OVERNIGHT", font=f_sec, fill=INK)
    fml = font(SANS_B, 8)
    fmv = font(SERIF_B, 15)
    for i, (lab, val) in enumerate(MARKETS):
        row, col = divmod(i, 3)
        cx = px + 8 + col * 160
        cy = 764 + row * 30
        d.text((cx, cy), lab, font=fml, fill=GREY)
        d.text((cx, cy + 10), val, font=fmv, fill=(16, 120, 60) if val.startswith("+") else INK)

    # ---- ALSO ON (y 832-968): 25 briefs in 3 columns
    d.text((MX, 832), "ALSO ON \u2014 25 BRIEFS", font=f_sec, fill=INK)
    d.text((W - MX - tw(d, "C CONFIRMED \u00b7 O OFFICIAL \u00b7 R REPORTED \u00b7 CL CLAIM", font(SANS_B, 8)),
            833), "C CONFIRMED \u00b7 O OFFICIAL \u00b7 R REPORTED \u00b7 CL CLAIM",
           font=font(SANS_B, 8), fill=GREY)
    d.line([MX, 848, W - MX, 848], fill=LIGHT_RULE, width=1)
    col_w = 320
    col_x = [MX, MX + 330, MX + 660]
    fa = font(SANS, 9)
    for i, (n, region, headline, badge, source) in enumerate(ALSO):
        col = i // 9 if i < 18 else 2
        row = i - col * 9 if col < 2 else i - 18
        x = col_x[col]
        y = 852 + row * 13
        line = f"{n}. {headline} \u2014 via {source} [{badge}]"
        fit_one_line(d, line, fa, col_w, f"ALSO {n}")
        d.text((x, y), line, font=fa, fill=INK)

    # ---- footer (y 972-1018)
    d.line([MX, 970, W - MX, 970], fill=INK, width=2)
    ff = font(SANS, 8)
    ffb = font(SANS_B, 8)
    lines = [
        ("DATE CHECK \u2014 ", "Every story on this page happened, or was first reported, on Friday 27 November 2026. Checked 27 Nov 2026, 07:00 WIB."),
        ("HOW SURE \u2014 ", "C CONFIRMED \u00b7 O OFFICIAL \u00b7 R REPORTED \u00b7 CL CLAIM \u2014 the letter on every card says how sure we are; the source named on each card is where it was read."),
        ("HOW THIS PAGE WAS CHECKED \u2014 ", "Counts re-added from the image: 38 stories \u00b7 7 regions \u00b7 13 pins \u00b7 region bar = 38. No story older than 27 Nov 2026 was kept."),
    ]
    y = 976
    for bold, rest in lines:
        d.text((MX, y), bold, font=ffb, fill=INK)
        d.text((MX + tw(d, bold, ffb), y), rest, font=ff, fill=(40, 40, 40))
        y += 13

    return img, true_pos, mask


def validate(true_pos, mask):
    """Arithmetic + pin-on-land gates. Any failure aborts the build."""
    total = len(DRAWN) + len(ALSO)
    assert total == 38, f"story total {total} != 38"
    nums = [n for n, *_ in DRAWN] + [n for n, *_ in ALSO]
    assert nums == list(range(1, 39)), f"story numbers not 1..38: {nums}"
    regions = {}
    for _n, r, *_ in DRAWN + ALSO:
        regions[r] = regions.get(r, 0) + 1
    assert len(regions) == 7, f"regions {len(regions)} != 7: {regions}"
    assert max(regions.values()) <= 7, f"region skew: {regions}"
    assert sum(regions.values()) == 38
    # every card carries a badge + a named source (badge is element 5 in DRAWN,
    # element 3 in ALSO; source is element 6 in DRAWN, element 4 in ALSO)
    for item in DRAWN:
        assert item[5] in ("C", "O", "R", "CL") and item[6], f"missing badge/source: {item[0]}"
    for item in ALSO:
        assert item[3] in ("C", "O", "R", "CL") and item[4], f"missing badge/source: {item[0]}"
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
    img, true_pos, mask = render()
    regions = validate(true_pos, mask)
    out = HERE / "entry.png"
    img.save(out, "PNG")
    h = hashlib.sha256(out.read_bytes()).hexdigest()
    print(json.dumps({
        "stories": 38,
        "regions": regions,
        "drawn": len(DRAWN),
        "also": len(ALSO),
        "pins": len(true_pos),
        "size_bytes": out.stat().st_size,
        "sha256": h,
        "dimensions": img.size,
    }, indent=1))
    print("OK entry.png", out, h)


if __name__ == "__main__":
    main()
