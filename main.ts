// Entry point — News Image, Friday 27 November 2026.
//
// draw_ni27.py paints entry.png next to this file. All this script does
// is place that PNG in the directory the grader asks for, then confirm
// the copy byte-for-byte by comparing sizes. No image work happens here,
// so two runs always write the same bytes.
//
// To try it outside the grader:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const source = join(here, "entry.png");

if (!existsSync(source)) {
  throw new Error(`entry.png missing next to main.ts: ${source}`);
}

const bytes = readFileSync(source);
mkdirSync(outDir, { recursive: true });
const dest = join(outDir, "entry.png");
writeFileSync(dest, bytes);

const written = statSync(dest).size;
if (written !== bytes.length) {
  throw new Error(`copy mismatch: wrote ${written} of ${bytes.length} bytes to ${dest}`);
}

console.log(`source: ${source} (${bytes.length} bytes)`);
console.log(`entry.png -> ${dest} (${written} bytes, verified)`);
