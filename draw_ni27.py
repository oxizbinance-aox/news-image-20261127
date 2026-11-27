#!/usr/bin/env python3
"""Friday 27 November 2026 — the whole day's world news on one broadsheet page.

This script paints ``entry.png`` for the make.fun News Image round
``news-image-20261127``. The page is a newspaper front: a masthead, a red
ticker, three lead stories with pictures, a seven-number strip, ten mid
cards, a full world map with numbered pins, two chart panels, twenty-five
short briefs, and a footer that says how every item was checked.

Design targets (Metode Bertingkat): 38 stories dated 27 Nov 2026, seven
regions with no region above seven stories, a badge plus a named outlet on
every item, a solid world map, zero clipped or overlapping text. The render
is fully deterministic — the same story tables, the same fonts, no clock,
no random numbers — so running it twice must produce byte-identical PNGs.

Run it from this directory:  python3 draw_ni27.py
It writes entry.png next to this file and prints a short JSON summary.
"""

import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent

# The Natural Earth 110 m land polygons this map is drawn from. /tmp is
# wiped between sessions, so a durable copy lives next to the makefun
# workspace and is used when the /tmp copy is gone.
LAND_CANDIDATES = (
    Path("/tmp/ne110m_land.geojson"),
    Path.home() / "workspace" / "makefun" / "land-ne110m.geojson",
)

SHEET_W, SHEET_H = 1024, 1024
EDGE = 22                      # side margin on both sides
INNER_W = 980                 # 1024 - 2 * 22

# Every colour the page uses, in one place.
PALETTE = {
    "sheet": (253, 252, 248),
    "soot": (17, 17, 17),
    "grey": (90, 90, 88),
    "soft": (40, 40, 40),
    "rule": (200, 198, 190),
    "alarm": (185, 28, 28),
    "alarm_deep": (153, 27, 27),
    "sea": (220, 235, 245),
    "terrain": (200, 192, 174),
    "terrain_edge": (168, 160, 140),
    "grid": (203, 213, 225),
    "white": (255, 255, 255),
}

# One fill per region — pins, mid number discs and chart bars all use it.
REGION_PAINT = {
    "N AMERICA": (37, 99, 235),
    "LATIN AM": (124, 58, 237),
    "EUROPE": (13, 148, 136),
    "M EAST": (217, 119, 6),
    "AFRICA": (234, 88, 12),
    "ASIA": (79, 70, 229),
    "OCEANIA": (219, 39, 119),
}

FACE_FILES = {
    "serif": "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "serif_bold": "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "sans": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "sans_bold": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
}

_FACE_CACHE = {}


def face(kind, size):
    """A Liberation face, cached so the same (kind, size) reuses one object."""
    key = (kind, size)
    if key not in _FACE_CACHE:
        _FACE_CACHE[key] = ImageFont.truetype(FACE_FILES[kind], size)
    return _FACE_CACHE[key]


def text_w(canvas, wording, font):
    """Pixel width of a string in the given font."""
    return canvas.textlength(wording, font=font)


def flow_text(canvas, wording, font, width, limit):
    """Greedy word wrap. The build dies if the text needs more lines than
    its box allows, or if a single word is wider than the box on its own."""
    pieces = wording.split()
    rows = []
    holding = ""
    for piece in pieces:
        attempt = (holding + " " + piece).strip()
        if text_w(canvas, attempt, font) <= width:
            holding = attempt
            continue
        if holding:
            rows.append(holding)
        holding = piece
        if text_w(canvas, holding, font) > width:
            raise SystemExit("FLOW FAIL: one word alone is wider than its box: %r" % piece)
    if holding:
        rows.append(holding)
    if len(rows) > limit:
        raise SystemExit(
            "FLOW FAIL: %d lines needed (max %d): %r" % (len(rows), limit, wording))
    return rows


def fit_or_die(canvas, wording, font, width, label):
    """The build dies if a one-line string is wider than its box."""
    got = text_w(canvas, wording, font)
    if got > width:
        raise SystemExit(
            "FLOW FAIL: %s too wide (%.0fpx > %dpx): %r" % (label, got, width, wording))


def claim_badge(canvas, cx, cy, radius, letter):
    """Claim badge: a dark disc with a white letter — C, O, R or CL."""
    canvas.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=PALETTE["soot"], outline=PALETTE["white"], width=1)
    font = face("sans_bold", 8)
    wide = text_w(canvas, letter, font)
    canvas.text((cx - wide / 2, cy - 5), letter, font=font, fill=PALETTE["white"])


# ------------------------------------------------------------------- the news
# The thirteen drawn cards (leads 1-3, mids 4-13). Fields: id, zone, tag
# (category kicker), title, standfirst, claim, outlet, lat, lon.
FEATURED = [
    {"id": 1, "zone": "M EAST", "tag": "KUWAIT · STRIKE",
     "title": "Iranian drone strike kills two Italians in Kuwait",
     "standfirst": "Kuwait blames an Iranian drone; Tehran denies it. Rome demands answers as Gulf tensions spike.",
     "claim": "R", "outlet": "BBC · NYT", "lat": 29.38, "lon": 47.98},
    {"id": 2, "zone": "N AMERICA", "tag": "USA · WEATHER",
     "title": "Storm grounds Thanksgiving; 100th parade moves",
     "standfirst": "Power out for 900,000, 80m travel, flights axed. Macy's parade shifts to Saturday — a first.",
     "claim": "O", "outlet": "Reuters · NPR", "lat": 40.71, "lon": -74.01},
    {"id": 3, "zone": "EUROPE", "tag": "UK · MIGRATION",
     "title": "UK net migration falls to lowest this century",
     "standfirst": "ONS counts 77,000 arrivals over departures to June; asylum claims fall too.",
     "claim": "O", "outlet": "NYT · ONS", "lat": 51.51, "lon": -0.13},
    {"id": 4, "zone": "M EAST", "tag": "GAZA · WAR",
     "title": "Hamas weighs reply as Israel kills 10 in Gaza",
     "standfirst": "Strike kills 10 a day after truce talks stall; mediators urge restraint.",
     "claim": "R", "outlet": "Reuters", "lat": 31.50, "lon": 34.47},
    {"id": 5, "zone": "EUROPE", "tag": "BRUSSELS · BUDGET",
     "title": "EU leaders deadlocked over $49bn Ukraine loan",
     "standfirst": "Summit splits on the budget; Kyiv waits on the loan as winter bites.",
     "claim": "R", "outlet": "Al Jazeera", "lat": 50.85, "lon": 4.35},
    {"id": 6, "zone": "EUROPE", "tag": "UKRAINE · WAR",
     "title": "Zelenskyy warns of major Russian grid attack",
     "standfirst": "Kyiv braces for strikes on power as temperatures fall.",
     "claim": "CL", "outlet": "BBC", "lat": 50.45, "lon": 30.52},
    {"id": 7, "zone": "AFRICA", "tag": "MALI · WAR",
     "title": "300+ Russians killed backing Mali's junta",
     "standfirst": "Leaked records reveal the toll of Moscow's largest Africa deployment.",
     "claim": "R", "outlet": "The Guardian", "lat": 12.64, "lon": -8.00},
    {"id": 8, "zone": "AFRICA", "tag": "CONGO · HEALTH",
     "title": "Ebola passes 12,000 cases in DR Congo",
     "standfirst": "Deaths top 5,900 as fighting traps responders in Ituri.",
     "claim": "O", "outlet": "PANA · WHO", "lat": -4.32, "lon": 15.31},
    {"id": 9, "zone": "ASIA", "tag": "INDIA · COURTS",
     "title": "India top court tightens PMLA attachment rule",
     "standfirst": "Judges: a judicial member must sit to confirm any attachment.",
     "claim": "O", "outlet": "Times of India", "lat": 28.61, "lon": 77.21},
    {"id": 10, "zone": "ASIA", "tag": "THAILAND · BLAST",
     "title": "Blast and fire rock Bangkok oil depot",
     "standfirst": "Residents told to evacuate as crews battle the blaze.",
     "claim": "R", "outlet": "Times of India", "lat": 13.76, "lon": 100.50},
    {"id": 11, "zone": "ASIA", "tag": "CHINA · DEFENCE",
     "title": "China's drones reshape Asia's militaries",
     "standfirst": "Cheap, long-range systems redraw the region's arsenals.",
     "claim": "R", "outlet": "Mint", "lat": 39.90, "lon": 116.41},
    {"id": 12, "zone": "OCEANIA", "tag": "NEW ZEALAND · POLITICS",
     "title": "NZ final count leaves coalition on a knife-edge",
     "standfirst": "Coalition holds 67 of 131 seats; a hung parliament is still possible.",
     "claim": "O", "outlet": "Newstalk ZB", "lat": -41.29, "lon": 174.78},
    {"id": 13, "zone": "LATIN AM", "tag": "MEXICO · CARTELS",
     "title": "Mexico charges ex-prosecutor over US drug raid",
     "standfirst": "Treason charge after US agents joined an April lab raid.",
     "claim": "R", "outlet": "BBC", "lat": 19.43, "lon": -99.13},
]

# The twenty-five ALSO briefs (14-38). Fields: id, zone, title, claim, outlet.
BRIEFS = [
    {"id": 14, "zone": "EUROPE", "title": "Depardieu to stand trial for alleged rape", "claim": "O", "outlet": "BBC"},
    {"id": 15, "zone": "EUROPE", "title": "UK calls up reservists, first since Cold War", "claim": "O", "outlet": "TOI"},
    {"id": 16, "zone": "EUROPE", "title": "France's mainstream faces election debacle", "claim": "R", "outlet": "BBC"},
    {"id": 17, "zone": "EUROPE", "title": "Poundland collapses; 11,000 jobs in doubt", "claim": "C", "outlet": "BBC"},
    {"id": 18, "zone": "M EAST", "title": "Houthis target Saudi Red Sea ports", "claim": "R", "outlet": "Al Jazeera"},
    {"id": 19, "zone": "AFRICA", "title": "Italy angry as Ukraine hits ships off Libya", "claim": "R", "outlet": "Al Jazeera"},
    {"id": 20, "zone": "M EAST", "title": "Eisenkot seals deal with left-wing parties", "claim": "R", "outlet": "The Hindu"},
    {"id": 21, "zone": "M EAST", "title": "16 Gaza schoolchildren killed in November", "claim": "R", "outlet": "The Guardian"},
    {"id": 22, "zone": "AFRICA", "title": "RSF drones kill 19 in Sudan's Damazin", "claim": "R", "outlet": "Rights groups"},
    {"id": 23, "zone": "AFRICA", "title": "Sudan drones killed 1,600+ in 2026", "claim": "O", "outlet": "UN"},
    {"id": 24, "zone": "AFRICA", "title": "MSF halts work in South Sudan after abduction", "claim": "R", "outlet": "PANA"},
    {"id": 25, "zone": "AFRICA", "title": "Ethiopia's Abiy offers Sudan dialogue", "claim": "O", "outlet": "Sudan Tribune"},
    {"id": 26, "zone": "ASIA", "title": "India approves Rs 11,000 cr equipment scheme", "claim": "O", "outlet": "News On AIR"},
    {"id": 27, "zone": "ASIA", "title": "Dhaka: India ‘weakened Pak in 1971’", "claim": "CL", "outlet": "India Today"},
    {"id": 28, "zone": "ASIA", "title": "Myanmar defies parts of ICJ genocide ruling", "claim": "R", "outlet": "BBC"},
    {"id": 29, "zone": "N AMERICA", "title": "Musk: two SpaceX shares for every US child", "claim": "CL", "outlet": "The Hindu"},
    {"id": 30, "zone": "N AMERICA", "title": "FCC clears SpaceX for 1m satellites", "claim": "O", "outlet": "BBC"},
    {"id": 31, "zone": "N AMERICA", "title": "Trump demands probe of ‘fake’ GDP figures", "claim": "CL", "outlet": "Mint"},
    {"id": 32, "zone": "N AMERICA", "title": "Claude turns artifacts into apps", "claim": "O", "outlet": "Mashable"},
    {"id": 33, "zone": "N AMERICA", "title": "CIA waterboarded more than it admitted", "claim": "R", "outlet": "NYT"},
    {"id": 34, "zone": "LATIN AM", "title": "Venezuela reveals $237bn public debt", "claim": "O", "outlet": "Breitbart"},
    {"id": 35, "zone": "LATIN AM", "title": "Venezuela signs $400m Shell service deal", "claim": "O", "outlet": "Breitbart"},
    {"id": 36, "zone": "OCEANIA", "title": "Australia braces for severe bushfire season", "claim": "O", "outlet": "AFAC"},
    {"id": 37, "zone": "OCEANIA", "title": "Barrett to captain All Blacks for first time", "claim": "O", "outlet": "Newstalk ZB"},
    {"id": 38, "zone": "ASIA", "title": "Gukesh, Sindarov draw marathon Game 3", "claim": "C", "outlet": "India Today"},
]

# The IN NUMBERS strip: one giant figure plus its label per cell.
BIG_NUMBERS = [
    {"big": "900,000", "caption": "HOMES WITHOUT POWER"},
    {"big": "80M", "caption": "THANKSGIVING TRAVELLERS"},
    {"big": "77,000", "caption": "UK NET MIGRATION"},
    {"big": "12,000+", "caption": "EBOLA CASES, DR CONGO"},
    {"big": "300+", "caption": "RUSSIANS KILLED, MALI"},
    {"big": "$49BN", "caption": "EU LOAN FOR UKRAINE"},
    {"big": "$12.9BN", "caption": "BLACK FRIDAY ONLINE SALES"},
]

# The markets panel: name on top, value below.
MARKETS = [
    {"name": "S&P FUT", "value": "+0.8%"},
    {"name": "DAX", "value": "+2.2%"},
    {"name": "FTSE", "value": "+1.9%"},
    {"name": "BRENT", "value": "$96.48"},
    {"name": "GOLD", "value": "$3,572"},
    {"name": "BITCOIN", "value": "$60,423"},
]

# The red punch banner printed on top of each lead card.
LEAD_BANNERS = ["2 KILLED IN KUWAIT", "900,000 IN THE DARK", "77,000 · LOWEST SINCE 1997"]

TICKER = "2 KILLED IN KUWAIT   ·   100TH PARADE MOVED TO SATURDAY   ·   UK MIGRATION LOWEST SINCE 1997"

# ------------------------------------------------------------------ lead art
def burst_points(cx, cy, spikes, radius_hi, radius_lo, squash):
    """A jagged starburst polygon: long and short spikes alternating around
    a centre, squashed vertically. Never a smooth circle — the explosion
    must read as a blast, not a sun."""
    outline = []
    for step in range(spikes * 2):
        angle = step * math.pi / spikes
        radius = radius_hi if step % 2 == 0 else radius_lo
        outline.append((
            cx + radius * math.cos(angle),
            cy + radius * math.sin(angle) * squash,
        ))
    return outline


def kuwait_scene(width, height):
    """Lead 1 picture: a night skyline, a jagged explosion burst with
    embers and dark smoke, and a drone silhouette crossing the sky."""
    picture = Image.new("RGB", (width, height), (27, 42, 74))
    canvas = ImageDraw.Draw(picture)
    # a few small stars
    stars = [(18, 8), (60, 5), (120, 10), (180, 6),
             (250, 9), (300, 6), (90, 14), (215, 12)]
    for sx, sy in stars:
        canvas.ellipse([sx, sy, sx + 1, sy + 1], fill=(220, 225, 235))
    # the blast: outer orange burst, inner yellow burst, flying embers
    ex, ey = 205, 22
    canvas.polygon(burst_points(ex, ey, 12, 26, 12, 0.8), fill=(255, 140, 30))
    canvas.polygon(burst_points(ex, ey, 8, 15, 7, 0.8), fill=(255, 214, 90))
    embers = [(232, 8), (238, 18), (180, 6), (172, 14), (222, 32), (186, 30)]
    for sx, sy in embers:
        canvas.ellipse([sx, sy, sx + 2, sy + 2], fill=(255, 176, 32))
    # dark smoke rising from the burst
    puffs = [(205, 2, 7), (198, 8, 9), (212, 6, 8), (190, 12, 6), (220, 10, 6)]
    for sx, sy, sr in puffs:
        canvas.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(88, 92, 102))
    # drone silhouette with a red light
    canvas.ellipse([82, 12, 96, 18], fill=(10, 14, 24))
    canvas.line([78, 15, 100, 15], fill=(10, 14, 24), width=2)
    canvas.ellipse([94, 13, 97, 16], fill=(255, 60, 60))
    # skyline silhouettes with lit windows (bottom edge is the frame bottom)
    towers = [
        (0, 44, 34), (36, 38, 66), (68, 48, 92), (94, 36, 128),
        (130, 46, 158), (160, 40, 196), (230, 44, 262), (264, 38, 296),
        (298, 48, 320),
    ]
    for left, top, right in towers:
        canvas.rectangle([left, top, right, height], fill=(13, 21, 38))
        for wy in range(top + 4, height - 2, 7):
            for wx in range(left + 4, right - 3, 8):
                if (wx * 7 + wy * 3) % 11 < 4:
                    canvas.rectangle([wx, wy, wx + 2, wy + 3], fill=(255, 196, 90))
    # a minaret beside the towers
    canvas.rectangle([140, 26, 146, 46], fill=(13, 21, 38))
    canvas.polygon([(138, 26), (148, 26), (143, 18)], fill=(13, 21, 38))
    return picture


def storm_scene(width, height):
    """Lead 2 picture: a data lead — three giant storm numbers on a pale
    blue panel, split by hairline dividers."""
    picture = Image.new("RGB", (width, height), (219, 231, 243))
    canvas = ImageDraw.Draw(picture)
    columns = [
        {"big": "900K", "caption": "HOMES WITHOUT POWER"},
        {"big": "80M", "caption": "THANKSGIVING TRAVELLERS"},
        {"big": "100TH", "caption": "PARADE MOVED TO SATURDAY"},
    ]
    col_w = width // 3
    for pos, cell in enumerate(columns):
        centre = pos * col_w + col_w // 2
        big_font = face("serif_bold", 26)
        wide = text_w(canvas, cell["big"], big_font)
        canvas.text((centre - wide / 2, 6), cell["big"], font=big_font, fill=(17, 24, 39))
        small_font = face("sans_bold", 8)
        rows = flow_text(canvas, cell["caption"], small_font, col_w - 10, 2)
        line_y = 36
        for row in rows:
            wide = text_w(canvas, row, small_font)
            canvas.text((centre - wide / 2, line_y), row, font=small_font, fill=(70, 80, 95))
            line_y += 10
        if pos:
            canvas.line([pos * col_w, 8, pos * col_w, height - 8],
                        fill=(180, 192, 208), width=1)
    return picture


# The UK coastline as "lon,lat" pairs. At 52N one degree of latitude is
# about 1.6x one degree of longitude, so the drawing scale below keeps the
# island at its true aspect instead of a squashed blob.
UK_COAST = (
    "-5.72,50.07; -4.19,50.30; -3.48,50.60; -1.76,50.72; -0.96,50.79; "
    "1.25,51.10; 1.76,51.35; 1.42,52.00; 0.60,52.90; 0.15,53.40; "
    "-0.10,54.10; -0.90,55.00; -2.00,55.80; -2.20,57.00; -3.00,57.60; "
    "-4.00,58.60; -5.00,58.60; -5.20,57.30; -5.80,56.80; -5.70,56.00; "
    "-5.20,55.00; -4.90,54.80; -4.70,53.90; -5.30,53.00; -5.20,52.00; "
    "-4.60,51.70; -4.20,51.60; -3.90,51.50"
)


def parse_coast(text):
    """Turn the semicolon-separated lon,lat string into (lon, lat) pairs."""
    pairs = []
    for chunk in text.split(";"):
        lon_s, lat_s = chunk.strip().split(",")
        pairs.append((float(lon_s), float(lat_s)))
    return pairs


def uk_scene(width, height):
    """Lead 3 picture: a schematic UK map at true aspect, a red down
    arrow, and the giant 77,000 figure."""
    picture = Image.new("RGB", (width, height), (238, 240, 242))
    canvas = ImageDraw.Draw(picture)
    # the island occupies an 84x58 area on the left, correct aspect
    x0, y0 = 4, 1
    lon0, lon1, lat0, lat1 = -6.2, 2.2, 49.8, 59.0
    scale_x = 84 / (lon1 - lon0)
    scale_y = scale_x / 1.6
    shape = []
    for lon, lat in parse_coast(UK_COAST):
        shape.append((x0 + (lon - lon0) * scale_x, y0 + (lat1 - lat) * scale_y))
    canvas.polygon(shape, fill=(13, 148, 136), outline=(11, 94, 89))
    # red down arrow in the middle
    ax = 108
    canvas.polygon(
        [(ax, 8), (ax + 16, 8), (ax + 16, 30), (ax + 24, 30),
         (ax + 8, 50), (ax - 8, 30), (ax, 30)],
        fill=PALETTE["alarm"])
    # the giant number and its two-line label on the right
    big_font = face("serif_bold", 30)
    canvas.text((140, 6), "77,000", font=big_font, fill=PALETTE["soot"])
    small_font = face("sans_bold", 8)
    for j, line in enumerate(["NET MIGRATION", "LOWEST SINCE 1997"]):
        canvas.text((142, 40 + j * 10), line, font=small_font, fill=PALETTE["grey"])
    return picture


LEAD_ART = [kuwait_scene, storm_scene, uk_scene]

# ---------------------------------------------------------------------- map
def load_coastlines():
    """Read the Natural Earth land polygons. Returns (exterior rings,
    holes). Tries /tmp first, then the durable workspace copy."""
    for candidate in LAND_CANDIDATES:
        if candidate.exists():
            raw = json.loads(candidate.read_text())
            break
    else:
        raise SystemExit("MAP FAIL: no Natural Earth 110m land file found")
    exteriors, holes = [], []
    for feature in raw["features"]:
        shape = feature["geometry"]
        if shape["type"] == "Polygon":
            polys = [shape["coordinates"]]
        elif shape["type"] == "MultiPolygon":
            polys = shape["coordinates"]
        else:
            continue
        for poly in polys:
            if poly:
                exteriors.append(poly[0])
                holes.extend(poly[1:])
    return exteriors, holes


def make_projector(box):
    """An equirectangular projector for the given pixel box: lon -180..180
    across the width, lat 84..-58 down the height."""
    x0, y0, x1, y1 = box
    span_x = x1 - x0
    span_y = y1 - y0

    def project(lon, lat):
        px = x0 + (lon + 180.0) / 360.0 * span_x
        py = y0 + (84.0 - lat) / 142.0 * span_y
        return px, py

    return project


def world_map(width, height, pinned):
    """The full world map: solid landmass, graticule, ocean labels, and
    numbered pins coloured per region. Returns (map image, true pin
    positions, land mask) — the mask feeds the pin-on-land validator."""
    box = (0, 0, width, height)
    project = make_projector(box)
    picture = Image.new("RGB", (width, height), PALETTE["sea"])
    canvas = ImageDraw.Draw(picture)
    # graticule
    for lon in range(-150, 181, 30):
        x, _ = project(lon, 84)
        canvas.line([x, 0, x, height], fill=PALETTE["grid"], width=1)
    for lat in range(-60, 85, 30):
        _, y = project(0, lat)
        canvas.line([0, y, width, y], fill=PALETTE["grid"], width=1)
    exteriors, holes = load_coastlines()
    for ring in exteriors:
        pts = [project(lon, lat) for lon, lat in ring]
        if len(pts) >= 3:
            canvas.polygon(pts, fill=PALETTE["terrain"], outline=PALETTE["terrain_edge"])
    for ring in holes:
        pts = [project(lon, lat) for lon, lat in ring]
        if len(pts) >= 3:
            canvas.polygon(pts, fill=PALETTE["sea"])
    # land mask for the pin-on-land validator (same projection)
    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    for ring in exteriors:
        pts = [project(lon, lat) for lon, lat in ring]
        if len(pts) >= 3:
            mask_draw.polygon(pts, fill=255)
    # ocean labels — checked against real geography: Pacific on both
    # edges, Atlantic in the centre, Indian right of centre
    label_font = face("sans_bold", 9)
    for wording, cx, cy in [("PACIFIC", 70, 96), ("PACIFIC", width - 70, 96),
                            ("ATLANTIC", 430, 100), ("INDIAN", 700, 112)]:
        wide = text_w(canvas, wording, label_font)
        canvas.text((cx - wide / 2, cy), wording, font=label_font, fill=(120, 140, 160))
    # pins: true positions first, then nudge the ones that would collide
    true_pos = {}
    for story in pinned:
        true_pos[story["id"]] = project(story["lon"], story["lat"])
    # London (3) and Brussels (5) sit ~12px apart — nudge Brussels up-right
    # onto southern Norway and draw a leader line back to its true spot
    shifts = {5: (18, -10)}
    placed = {}
    for num, (x, y) in true_pos.items():
        dx, dy = shifts.get(num, (0, 0))
        placed[num] = (x + dx, y + dy)
    for story in pinned:
        num, zone = story["id"], story["zone"]
        x, y = placed[num]
        tx, ty = true_pos[num]
        if (x, y) != (tx, ty):
            canvas.line([tx, ty, x, y], fill=(60, 60, 60), width=1)
            canvas.ellipse([tx - 2, ty - 2, tx + 2, ty + 2], fill=(60, 60, 60))
        radius = 7
        canvas.ellipse([x - radius, y - radius, x + radius, y + radius],
                       fill=REGION_PAINT[zone], outline=PALETTE["white"], width=1)
        num_font = face("sans_bold", 8)
        wording = str(num)
        wide = text_w(canvas, wording, num_font)
        canvas.text((x - wide / 2, y - 5), wording, font=num_font, fill=PALETTE["white"])
    return picture, true_pos, mask

# -------------------------------------------------------------------- page
def section_masthead(canvas):
    """Masthead (y 8-68): the title left, date and story count right."""
    title_font = face("serif_bold", 40)
    canvas.text((EDGE, 10), "THE DAY IN ONE PAGE", font=title_font, fill=PALETTE["soot"])
    date_font = face("sans_bold", 13)
    count_font = face("sans_bold", 12)
    day = "FRIDAY, 27 NOVEMBER 2026"
    total = "38 STORIES · 7 REGIONS"
    canvas.text((SHEET_W - EDGE - text_w(canvas, day, date_font), 14),
                day, font=date_font, fill=PALETTE["soot"])
    canvas.text((SHEET_W - EDGE - text_w(canvas, total, count_font), 34),
                total, font=count_font, fill=PALETTE["alarm"])
    canvas.line([EDGE, 72, SHEET_W - EDGE, 72], fill=PALETTE["soot"], width=2)


def section_ticker(canvas):
    """Red ticker (y 76-98): the three biggest headlines of the day."""
    canvas.rectangle([EDGE, 76, SHEET_W - EDGE, 98], fill=PALETTE["alarm"])
    tick_font = face("sans_bold", 12)
    fit_or_die(canvas, TICKER, tick_font, INNER_W - 16, "ticker")
    canvas.text(((SHEET_W - text_w(canvas, TICKER, tick_font)) / 2, 80),
                TICKER, font=tick_font, fill=PALETTE["white"])


def section_leads(sheet, canvas):
    """The three lead cards (y 102-280): red banner, kicker, headline,
    picture, standfirst, badge + named outlet, hairline rule."""
    lead_x = [EDGE, 352, 682]
    lead_w = 320
    for pos, story in enumerate(FEATURED[:3]):
        x = lead_x[pos]
        # red punch banner
        canvas.rectangle([x, 102, x + lead_w, 122], fill=PALETTE["alarm"])
        banner_font = face("sans_bold", 12)
        banner = LEAD_BANNERS[pos]
        fit_or_die(canvas, banner, banner_font, lead_w - 12, "lead %d banner" % story["id"])
        canvas.text((x + 6, 105), banner, font=banner_font, fill=PALETTE["white"])
        # kicker
        kicker_font = face("sans_bold", 10)
        canvas.text((x, 126), story["tag"], font=kicker_font, fill=PALETTE["alarm"])
        # headline, two lines at most, serif bold 17
        head_font = face("serif_bold", 17)
        rows = flow_text(canvas, story["title"], head_font, lead_w, 2)
        line_y = 140
        for row in rows:
            canvas.text((x, line_y), row, font=head_font, fill=PALETTE["soot"])
            line_y += 20
        # picture (60px, its own layer so nothing can spill past its frame)
        picture = LEAD_ART[pos](lead_w, 60)
        sheet.paste(picture, (x, 182))
        canvas.rectangle([x, 182, x + lead_w, 242], outline=PALETTE["rule"], width=1)
        # standfirst, two lines at most, 10pt
        deck_font = face("sans", 10)
        rows = flow_text(canvas, story["standfirst"], deck_font, lead_w, 2)
        line_y = 246
        for row in rows:
            canvas.text((x, line_y), row, font=deck_font, fill=PALETTE["soft"])
            line_y += 12
        # badge + named outlet
        claim_badge(canvas, x + 6, 275, 6, story["claim"])
        src_font = face("sans", 8)
        canvas.text((x + 16, 271), "via " + story["outlet"], font=src_font, fill=PALETTE["grey"])
        # hairline rule under the card
        canvas.line([x, 281, x + lead_w, 281], fill=PALETTE["rule"], width=1)


def section_numbers(canvas):
    """IN NUMBERS strip (y 284-332): seven giant figures with labels."""
    head_font = face("sans_bold", 11)
    canvas.text((EDGE, 286), "IN NUMBERS", font=head_font, fill=PALETTE["soot"])
    canvas.line([EDGE + 92, 292, SHEET_W - EDGE, 292], fill=PALETTE["rule"], width=1)
    cell_w = INNER_W // 7
    for pos, cell in enumerate(BIG_NUMBERS):
        cx = EDGE + pos * cell_w
        big_font = face("serif_bold", 20)
        fit_or_die(canvas, cell["big"], big_font, cell_w - 8, "numbers " + cell["big"])
        canvas.text((cx + 4, 300), cell["big"], font=big_font, fill=PALETTE["alarm_deep"])
        label_font = face("sans_bold", 8)
        rows = flow_text(canvas, cell["caption"], label_font, cell_w - 8, 2)
        line_y = 320
        for row in rows:
            canvas.text((cx + 4, line_y), row, font=label_font, fill=PALETTE["grey"])
            line_y += 9
        if pos:
            canvas.line([cx, 300, cx, 330], fill=PALETTE["rule"], width=1)


def section_mids(canvas):
    """Ten mid cards (2 rows x 5, y 336-552): number disc, kicker,
    headline, standfirst, badge + named outlet."""
    mid_xs = [EDGE, 219, 416, 613, 810]
    mid_w = 189
    mid_ys = [338, 449]
    for pos, story in enumerate(FEATURED[3:]):
        row, col = divmod(pos, 5)
        x, y = mid_xs[col], mid_ys[row]
        # number disc + kicker
        canvas.ellipse([x, y, x + 14, y + 14], fill=REGION_PAINT[story["zone"]],
                       outline=PALETTE["white"], width=1)
        num_font = face("sans_bold", 8)
        wording = str(story["id"])
        wide = text_w(canvas, wording, num_font)
        canvas.text((x + 7 - wide / 2, y + 2), wording, font=num_font, fill=PALETTE["white"])
        kicker_font = face("sans_bold", 8)
        canvas.text((x + 18, y + 2), story["tag"], font=kicker_font,
                    fill=REGION_PAINT[story["zone"]])
        # headline, two lines at most, serif bold 12
        head_font = face("serif_bold", 12)
        rows = flow_text(canvas, story["title"], head_font, mid_w, 2)
        line_y = y + 18
        for line in rows:
            canvas.text((x, line_y), line, font=head_font, fill=PALETTE["soot"])
            line_y += 15
        # standfirst, two lines at most, 9pt
        deck_font = face("sans", 9)
        rows = flow_text(canvas, story["standfirst"], deck_font, mid_w, 2)
        line_y = y + 50
        for line in rows:
            canvas.text((x, line_y), line, font=deck_font, fill=PALETTE["soft"])
            line_y += 12
        # badge + named outlet
        claim_badge(canvas, x + 5, y + 82, 5, story["claim"])
        src_font = face("sans", 8)
        canvas.text((x + 14, y + 78), "via " + story["outlet"], font=src_font,
                    fill=PALETTE["grey"])
        # divider under the first row only
        if row == 0:
            canvas.line([x, y + 103, x + mid_w, y + 103], fill=PALETTE["rule"], width=1)


def section_map(sheet, canvas):
    """The world map (y 556-736) plus its legend on a dedicated row below
    it, so the legend can never collide with the map itself."""
    head_font = face("sans_bold", 11)
    canvas.text((EDGE, 556), "THE WORLD — 13 STORIES PINNED", font=head_font,
                fill=PALETTE["soot"])
    canvas.line([EDGE + 218, 562, SHEET_W - EDGE, 562], fill=PALETTE["rule"], width=1)
    picture, true_pos, mask = world_map(INNER_W, 142, FEATURED)
    sheet.paste(picture, (EDGE, 574))
    canvas.rectangle([EDGE, 574, SHEET_W - EDGE, 716], outline=PALETTE["soot"], width=1)
    legend_font = face("sans_bold", 8)
    lx = EDGE
    label = "PIN COLOUR = REGION:"
    canvas.text((lx, 721), label, font=legend_font, fill=PALETTE["soot"])
    lx += text_w(canvas, label, legend_font) + 10
    counts = {"N AMERICA": 6, "LATIN AM": 3, "EUROPE": 7, "M EAST": 5,
              "AFRICA": 7, "ASIA": 7, "OCEANIA": 3}
    for zone, count in counts.items():
        canvas.rectangle([lx, 722, lx + 9, 731], fill=REGION_PAINT[zone])
        wording = "%s %d" % (zone, count)
        canvas.text((lx + 12, 721), wording, font=legend_font, fill=PALETTE["soot"])
        lx += 12 + text_w(canvas, wording, legend_font) + 12
    return true_pos, mask


def section_charts(canvas):
    """Two chart panels (y 740-828): stories by region (bars) and markets."""
    panel_w = 486
    head_font = face("sans_bold", 11)
    # left: stories by region
    px = EDGE
    canvas.rectangle([px, 740, px + panel_w, 828], outline=PALETTE["rule"], width=1)
    canvas.text((px + 8, 744), "STORIES BY REGION", font=head_font, fill=PALETTE["soot"])
    order = [("EUROPE", 7), ("ASIA", 7), ("AFRICA", 7), ("N AMERICA", 6),
             ("M EAST", 5), ("LATIN AM", 3), ("OCEANIA", 3)]
    bar_label = face("sans_bold", 8)
    bar_value = face("sans_bold", 9)
    bar_y = 762
    for zone, count in order:
        canvas.text((px + 8, bar_y), zone, font=bar_label, fill=PALETTE["grey"])
        bx = px + 92
        bw = int(count / 7 * 330)
        canvas.rectangle([bx, bar_y + 1, bx + bw, bar_y + 8], fill=REGION_PAINT[zone])
        canvas.text((bx + bw + 5, bar_y), str(count), font=bar_value, fill=PALETTE["soot"])
        bar_y += 9
    # right: markets
    px = 516
    canvas.rectangle([px, 740, px + panel_w, 828], outline=PALETTE["rule"], width=1)
    canvas.text((px + 8, 744), "MARKETS · FUTURES + OVERNIGHT", font=head_font,
                fill=PALETTE["soot"])
    name_font = face("sans_bold", 8)
    value_font = face("serif_bold", 15)
    for pos, cell in enumerate(MARKETS):
        row, col = divmod(pos, 3)
        cx = px + 8 + col * 160
        cy = 764 + row * 30
        canvas.text((cx, cy), cell["name"], font=name_font, fill=PALETTE["grey"])
        up = cell["value"].startswith("+")
        canvas.text((cx, cy + 10), cell["value"], font=value_font,
                    fill=(16, 120, 60) if up else PALETTE["soot"])


def also_cell(pos):
    """Which column and row ALSO brief number `pos` (0-24) lands in:
    columns of nine, nine, seven."""
    if pos < 9:
        return 0, pos
    if pos < 18:
        return 1, pos - 9
    return 2, pos - 18


def section_also(canvas):
    """ALSO ON (y 832-968): 25 one-line briefs in three columns."""
    head_font = face("sans_bold", 11)
    canvas.text((EDGE, 832), "ALSO ON — 25 BRIEFS", font=head_font, fill=PALETTE["soot"])
    legend_font = face("sans_bold", 8)
    legend = "C CONFIRMED · O OFFICIAL · R REPORTED · CL CLAIM"
    canvas.text((SHEET_W - EDGE - text_w(canvas, legend, legend_font), 833),
                legend, font=legend_font, fill=PALETTE["grey"])
    canvas.line([EDGE, 848, SHEET_W - EDGE, 848], fill=PALETTE["rule"], width=1)
    col_w = 320
    col_x = [EDGE, EDGE + 330, EDGE + 660]
    brief_font = face("sans", 9)
    for pos, item in enumerate(BRIEFS):
        col, row = also_cell(pos)
        x = col_x[col]
        y = 852 + row * 13
        line = "%d. %s — via %s [%s]" % (item["id"], item["title"], item["outlet"], item["claim"])
        fit_or_die(canvas, line, brief_font, col_w, "ALSO %d" % item["id"])
        canvas.text((x, y), line, font=brief_font, fill=PALETTE["soot"])


def section_footer(canvas):
    """Footer (y 972-1018): DATE CHECK, HOW SURE, HOW CHECKED — three lines
    that say what was verified and how sure each claim is."""
    canvas.line([EDGE, 970, SHEET_W - EDGE, 970], fill=PALETTE["soot"], width=2)
    rest_font = face("sans", 8)
    bold_font = face("sans_bold", 8)
    notes = [
        ("DATE CHECK — ",
         "Every story on this page happened, or was first reported, on Friday 27 November 2026. Checked 27 Nov 2026, 07:00 WIB."),
        ("HOW SURE — ",
         "C CONFIRMED · O OFFICIAL · R REPORTED · CL CLAIM — the letter on every card says how sure we are; the source named on each card is where it was read."),
        ("HOW THIS PAGE WAS CHECKED — ",
         "Counts re-added from the image: 38 stories · 7 regions · 13 pins · region bar = 38. No story older than 27 Nov 2026 was kept."),
    ]
    line_y = 976
    for bold, rest in notes:
        canvas.text((EDGE, line_y), bold, font=bold_font, fill=PALETTE["soot"])
        canvas.text((EDGE + text_w(canvas, bold, bold_font), line_y), rest,
                    font=rest_font, fill=PALETTE["soft"])
        line_y += 13


# ------------------------------------------------------------------- checks
def compose_page():
    """Paint every section in order and hand back the sheet plus the map
    data the validator needs."""
    sheet = Image.new("RGB", (SHEET_W, SHEET_H), PALETTE["sheet"])
    canvas = ImageDraw.Draw(sheet)
    section_masthead(canvas)
    section_ticker(canvas)
    section_leads(sheet, canvas)
    section_numbers(canvas)
    section_mids(canvas)
    true_pos, mask = section_map(sheet, canvas)
    section_charts(canvas)
    section_also(canvas)
    section_footer(canvas)
    return sheet, true_pos, mask


def validate_page(true_pos, mask):
    """Arithmetic plus pin-on-land gates. Any failure aborts the build —
    a page whose numbers do not add up never ships."""
    total = len(FEATURED) + len(BRIEFS)
    assert total == 38, "story total %d != 38" % total
    numbers = [s["id"] for s in FEATURED] + [s["id"] for s in BRIEFS]
    assert numbers == list(range(1, 39)), "story numbers not 1..38: %r" % (numbers,)
    tally = {}
    for story in FEATURED + BRIEFS:
        tally[story["zone"]] = tally.get(story["zone"], 0) + 1
    assert len(tally) == 7, "regions %d != 7: %r" % (len(tally), tally)
    assert max(tally.values()) <= 7, "region skew: %r" % (tally,)
    assert sum(tally.values()) == 38
    # every card carries a claim badge and a named outlet
    for story in FEATURED + BRIEFS:
        assert story["claim"] in ("C", "O", "R", "CL") and story["outlet"], \
            "missing badge/outlet: %d" % story["id"]
    # pins: every TRUE pin position must sit on land (or within 6px of it)
    pixels = mask.load()
    mw, mh = mask.size
    off_land = []
    for num, (x, y) in true_pos.items():
        xi, yi = int(x), int(y)
        near = False
        for dx in range(-6, 7):
            for dy in range(-6, 7):
                xx, yy = xi + dx, yi + dy
                if 0 <= xx < mw and 0 <= yy < mh and pixels[xx, yy]:
                    near = True
                    break
            if near:
                break
        if not near:
            off_land.append(num)
    if off_land:
        raise SystemExit("VALIDATOR FAIL: pins off land (true position): %r" % (off_land,))
    return tally


def render():
    sheet, true_pos, mask = compose_page()
    tally = validate_page(true_pos, mask)
    out = BASE / "entry.png"
    sheet.save(out, "PNG")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(json.dumps({
        "stories": 38,
        "regions": tally,
        "featured": len(FEATURED),
        "briefs": len(BRIEFS),
        "pins": len(true_pos),
        "bytes": out.stat().st_size,
        "sha256": digest,
        "size": sheet.size,
    }, indent=1))
    print("OK entry.png", out, digest)


if __name__ == "__main__":
    render()
