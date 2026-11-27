# The Day in One Page — 27 November 2026

[![make.fun](https://make.fun/badge/news-image-20261127.svg)](https://make.fun/bounty/news-image-20261127) [![make.fun rank](https://make.fun/badge/news-image-20261127/oxizbinance-aox/news-image-20261127/rank.svg)](https://make.fun/bounty/news-image-20261127) [![make.fun reward](https://make.fun/badge/news-image-20261127/oxizbinance-aox/news-image-20261127/reward.svg)](https://make.fun/bounty/news-image-20261127)

**38 stories · 7 regions · one broadsheet front page for Friday 27 November 2026.**

This entry squeezes a full day of world news onto a single 1024×1024 page. The top of the page carries three lead stories — a night strike over Kuwait drawn as a scene, a storm data lead built around three giant numbers, and a UK map lead — then a strip of seven big figures, ten mid-size cards, a full world map with thirteen numbered pins, two chart panels, twenty-five one-line briefs, and a footer that explains how each item was checked.

- The bounty: https://make.fun/bounty/news-image-20261127
- The pot: $100 — $20 for 1st, $12 for 2nd, $6 for 3rd, $2 for 4th–10th, $1.20 for 11th–50th
- Entries close: 2026-11-29T00:00:00Z · entry fee: $0
- The image: `entry.png`, 1024×1024, 187,287 bytes
- Reproducibility: `draw_ni27.py` renders the same PNG every time — sha256 `8fe50fa1b7896c6e77eba3e1687818294659ddda6e2b74446528edd3854f2408`, confirmed identical across two renders in this session (see `build-log.json`)
- The program: `main.ts` (Node 22) copies `entry.png` into the output directory and logs the byte count

## How the page is put together

The build follows Metode Bertingkat, the five-level method the team has refined since 26 Nov 2026. Thirty-eight stories is the target band the winners sit in (36–40; a 48-story page turned out to be a liability, not a flex). The seven regions are balanced — no region holds more than 7 of the 38 stories. Thirteen cards are drawn in full and twenty-five more run as one-line briefs; the region bar, the header count, and the last brief number all read 38.

Every single item carries two trust marks: a claim letter (C CONFIRMED · O OFFICIAL · R REPORTED · CL CLAIM) and the outlet it was read in, named on the card itself. Each of the three leads wears a red punch banner, headlines are set in serif, and the world map is a solid landmass with pins projected from real latitude/longitude — 13 out of 13 on land, with the London/Brussels pair separated by a leader line. A layout validator inside the renderer kills the build on any clipped deck, and the page was re-read at 2x zoom before this version shipped. Self-judge trio: 5/6 — see `self-judge.md` for the full read, including the honest gap (our lead scenes are smaller than the NI20 winner's).

## The 38 stories

Every story below happened, or was first reported, on Friday 27 November 2026. Two candidates were thrown out while checking dates: a cartel arrest from 20 Nov and an exile return from 22 Nov.

### Drawn cards — leads 1–3, mids 4–13

| # | Headline | Region | How sure | Read at |
|---|----------|--------|----------|---------|
| 1 | Iranian drone strike kills two Italians in Kuwait | M East | R | BBC · NYT |
| 2 | Storm grounds Thanksgiving; 100th parade moves | N America | O | Reuters · NPR |
| 3 | UK net migration falls to lowest this century | Europe | O | NYT · ONS |
| 4 | Hamas weighs reply as Israel kills 10 in Gaza | M East | R | Reuters |
| 5 | EU leaders deadlocked over $49bn Ukraine loan | Europe | R | Al Jazeera |
| 6 | Zelenskyy warns of major Russian grid attack | Europe | CL | BBC |
| 7 | 300+ Russians killed backing Mali's junta | Africa | R | The Guardian |
| 8 | Ebola passes 12,000 cases in DR Congo | Africa | O | PANA · WHO |
| 9 | India top court tightens PMLA attachment rule | Asia | O | Times of India |
| 10 | Blast and fire rock Bangkok oil depot | Asia | R | Times of India |
| 11 | China's drones reshape Asia's militaries | Asia | R | Mint |
| 12 | NZ final count leaves coalition on a knife-edge | Oceania | O | Newstalk ZB |
| 13 | Mexico charges ex-prosecutor over US drug raid | Latin Am | R | BBC |

### ALSO briefs 14–38

| # | Headline | Region | How sure | Read at |
|---|----------|--------|----------|---------|
| 14 | Depardieu to stand trial for alleged rape | Europe | O | BBC |
| 15 | UK calls up reservists, first since Cold War | Europe | O | TOI |
| 16 | France's mainstream faces election debacle | Europe | R | BBC |
| 17 | Poundland collapses; 11,000 jobs in doubt | Europe | C | BBC |
| 18 | Houthis target Saudi Red Sea ports | M East | R | Al Jazeera |
| 19 | Italy angry as Ukraine hits ships off Libya | Africa | R | Al Jazeera |
| 20 | Eisenkot seals deal with left-wing parties | M East | R | The Hindu |
| 21 | 16 Gaza schoolchildren killed in November | M East | R | The Guardian |
| 22 | RSF drones kill 19 in Sudan's Damazin | Africa | R | Rights groups |
| 23 | Sudan drones killed 1,600+ in 2026 | Africa | O | UN |
| 24 | MSF halts work in South Sudan after abduction | Africa | R | PANA |
| 25 | Ethiopia's Abiy offers Sudan dialogue | Africa | O | Sudan Tribune |
| 26 | India approves Rs 11,000 cr equipment scheme | Asia | O | News On AIR |
| 27 | Dhaka: India ‘weakened Pak in 1971’ | Asia | CL | India Today |
| 28 | Myanmar defies parts of ICJ genocide ruling | Asia | R | BBC |
| 29 | Musk: two SpaceX shares for every US child | N America | CL | The Hindu |
| 30 | FCC clears SpaceX for 1m satellites | N America | O | BBC |
| 31 | Trump demands probe of ‘fake’ GDP figures | N America | CL | Mint |
| 32 | Claude turns artifacts into apps | N America | O | Mashable |
| 33 | CIA waterboarded more than it admitted | N America | R | NYT |
| 34 | Venezuela reveals $237bn public debt | Latin Am | O | Breitbart |
| 35 | Venezuela signs $400m Shell service deal | Latin Am | O | Breitbart |
| 36 | Australia braces for severe bushfire season | Oceania | O | AFAC |
| 37 | Barrett to captain All Blacks for first time | Oceania | O | Newstalk ZB |
| 38 | Gukesh, Sindarov draw marathon Game 3 | Asia | C | India Today |

## Where the news was read

BBC · NYT · Reuters · NPR · Al Jazeera · The Guardian · PANA · WHO · Times of India · Mint · Newstalk ZB · The Hindu · India Today · News On AIR · UN · Sudan Tribune · Mashable · Breitbart · AFAC · ONS · TOI · Rights groups. Each story was checked against its named outlet on 27 Nov 2026, and the claim letter on every card says how sure we are about it — confirmed, official, reported, or claim.
