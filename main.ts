// News Image — Friday 27 November 2026.
//
// The entry image is painted by draw_ni27.py (Pillow, deterministic:
// fixed story data, fixed fonts, no clock, no randomness) and stored next
// to this file as entry.png. This program only copies that image into the
// output directory the grader hands it, so repeated runs write identical
// bytes.
//
// Outside the grader, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const folder = dirname(fileURLToPath(import.meta.url));
const target = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

mkdirSync(target, { recursive: true });
const dest = join(target, "entry.png");
copyFileSync(join(folder, "entry.png"), dest);
console.log(`entry.png -> ${dest}`);
