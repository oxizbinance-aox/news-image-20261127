# NI27 v1 fix session — Self-judge vs NI20 #1 superskie (27 Nov 2026)

Fix session (authorship): `makefun check` on the rebuild failed only
`thinking_reproduces` — 171 of 782 counted lines (21.8%, bar 30%).
`thinking_in_window` and `thinking_fresh` both passed, so this session
re-ran `init` in the repo first (anchor
`makefun anchor c0df8fb1a97ce424cb22cc92fcc96508723a4dc3 round 34311422`
in a tool result, before any write), then rewrote `draw_ni27.py`,
`main.ts` and `README.md` from scratch with a different structure —
new helper decomposition, new data shapes, new names, new prose — while
keeping every drawn pixel identical. The rebuilt `entry.png` is
byte-identical to the verified v1 (sha256 below), so every reading below
was re-verified on the fix-session output itself.

Reference (same bar as the rebuild session):
- #1 superskie 872350, 33 stories, 7 regions —
  `~/workspace/makefun/ni27-zoom/ni20_1.webp`
  (submission 01a1fbe6-f105-7190-bded-2ac1c6e5d2ab)

## Trio rubric (0–2 each, illustration / hierarchy / craft)

| Dimension | Ours | #1 | Notes |
|-----------|------|----|-------|
| Illustration | 1 | 2 | The device mix is right — a rich Kuwait night-strike scene with a jagged burst and smoke, an informative UK map at true aspect, a data lead with three giant numbers, two chart panels, a full world map — but the scale trails #1: our lead scenes are 60px tall against #1's ~150px, and the ten mid cards carry no pictograms at all. |
| Hierarchy | 2 | 2 | The same winning skeleton: masthead → red ticker → three leads with red punch banners → IN NUMBERS → ten mids → full-width world map with legend → two charts → ALSO → DATE CHECK / HOW SURE / HOW CHECKED footer. Every zone reads clearly at 300px. |
| Craft | 2 | 2 | Zero defects found: the layout validator reports 0 problems, all five 2x crops are clean, OCR reads 183 boxes with 35/38 story numbers (the 3 misses are tiny-glyph OCR limits — pin-circle "4", ALSO "18." and "30." — all three visually confirmed present at 2x), pins 13/13 on land, and the arithmetic is exact (region bar = 38 = header = last ALSO number). |
| **Total** | **5/6** | **6/6** | **Meets the trio ≥5 bar. The one-point gap is illustration scale and detail, the same wall NI26 hit.** |

## Pairwise vs #1 (4 heuristics)

- Density: WIN — 38 stories vs 33 (#1).
- Legibility: TIE — both legible at 300px, zero garble.
- Design: LOSE — #1's bigger lead scenes and a pictogram on every mid card; our map is bigger (full-width 980px vs #1's ~300px quadrant) but illustration is the swing dimension.
- Breadth: TIE — 7 regions vs 7 (#1).

Pairwise verdict: mixed — density won, legibility and breadth tied,
design lost. **Not a clear win over #1.** Per Metode Bertingkat T5
(proxies must AGREE on a clear win), this v1 is a clean, dense,
submittable entry — not a proven #1-beater. The residual gap is the
known PIL-vector ceiling: layout rebuilds don't close the illustration
gap, only richer illustration does.

## What this fix session caught and fixed

1. A real bug the rewrite introduced: in the mid-card painter the text
   loops reused the name `row`, shadowing the grid row — the row-0
   divider lines never drew. Found by a pixel diff (950 pixels, all on
   y=441), fixed by renaming the loop variable, re-rendered to
   byte-identical output.
2. The land data file `/tmp/ne110m_land.geojson` had been wiped with
   /tmp since the rebuild. Re-downloaded from the same upstream URL —
   138,160 bytes, 127 features, same as the v1 record — and a durable
   copy saved at `~/workspace/makefun/land-ne110m.geojson`; the new
   script falls back to it when /tmp is gone.
3. The OCR venv (`/tmp/ocr-venv`) was wiped too. Recreated durably at
   `~/workspace/makefun/ocr-venv` with RapidOCR; the gate below ran from it.

## Defects checked in this fix session (all verified gone at 2x)

1. Lead 1 explosion read as a sun — jagged starburst with embers and
   dark smoke, confirmed at 2x.
2. Lead 3 UK map read as a teal blob — corrected polygon at true aspect
   (1 deg lat = 1.6x 1 deg lon at 52N), confirmed at 2x.
3. Lead 2 label "PARADE MOVED TO SAT" — now "PARADE MOVED TO SATURDAY",
   wrapping to two lines, confirmed at 2x.
4. IN NUMBERS labels sat 5px above the mid kickers — labels moved up,
   mid rows moved down 2px.
5. Two candidate stories dropped for wrong dates: Sinaloa kingpin arrest
   (20 Nov, not 27 Nov) and Machado's exile return (22 Nov, not 27 Nov).
6. ALSO #23/#33 headlines repeated their source — headlines trimmed.

## Tier status (Metode Bertingkat)

- T1 LAYAK: fee $0, round open; cap check belongs to the parent at submit.
- T2 LENGKAP: 38 stories, 7 regions max 7/38, 13 drawn + 25 ALSO, badges +
  named sources everywhere, kickers, arithmetic exact — PASS.
- T3 RAPI: zero truncation/overlap/garble, no geometry outside any frame,
  pins from lat/lon 13/13 on land — PASS.
- T4 KORAN: full solid world map + numbered coloured pins + count legend,
  red banner per lead, serif headlines, 1px rules, no dark panels,
  3-device lead mix — PASS (map proportion flatter than #1's is the noted
  residual).
- T5 MENANG: trio 5/6 (bar met) BUT pairwise vs #1 mixed, and the
  second-family blind A/B was NOT run in this session — NOT a clear win.
  Decision on submit belongs to the parent, not this fix agent.

## Density-gate (OCR) log

- Engine: RapidOCR (onnxruntime), whole page 1024x1024, venv
  `~/workspace/makefun/ocr-venv`.
- Text boxes detected: 183.
- Story numbers 1–38 found by OCR: 35/38. Missing: 4, 18, 30 — all three
  visually verified present in the image (pin-circle "4", ALSO "18." and
  "30." — small glyphs the OCR misses, not missing content).
- Section headers found: IN NUMBERS, ALSO ON, DATE CHECK, HOW SURE,
  PIN COLOUR, STORIES BY REGION, MARKETS. "38 STORIES · 7 REGIONS" found
  as "38STORIES·7REGIONS" (OCR spacing artefact).
- Determinism: two renders in this fix session, sha256 identical
  `8fe50fa1b7896c6e77eba3e1687818294659ddda6e2b74446528edd3854f2408`,
  and identical to the v1 sha256.
