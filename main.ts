// News Image — Friday 27 November 2026.
//
// The entry image is rendered by draw_ni27.py (Pillow, deterministic: fixed
// data, fixed fonts, no timestamps, no randomness) and stored beside this
// file as entry.png. This program only copies that image to the output
// directory the grader provides, so both runs write the same bytes.
//
// Outside the grader, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

mkdirSync(outDir, { recursive: true });
copyFileSync(join(here, "entry.png"), join(outDir, "entry.png"));
