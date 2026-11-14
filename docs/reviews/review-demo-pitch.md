# Review of `team/demo-pitch-8e0e9b` (merged into main at 7baefaf; rehearsal commit e5de2ff)

Scope: `docs/demo/pitch.md`, `demo-problems.md`, `runbook.md`, `contingency.md`, `one-pager.md`,
`dev/demo_pick.py`, `dev/demo_rehearse.py`. Nothing changed by me.

**Executed**: the suite on `origin/main` (181 tests OK); the four pitch problems and the two reserve
problems looked up in the data (id, language, level, label, topic, options, image) and run through
`hints.get_hint` rungs 1 and 2 on main; `dev/demo_pick.py --chain` for the three pseudonyms;
`dev/demo_rehearse.py` for both chains against a sim server on main; every figure of the numbers
and lessons blocks checked against `docs/results-A.md` and `docs/error-analysis.md`; the spoken
words of each block counted. **Only read**: the runbook and contingency steps that need the board.

## Executive summary

1. The brief promised a timed 3-minute script in Catalan and English, four demo problems by id with a
   click script, a runbook, contingencies with a video storyboard and a sim rehearsal. All delivered,
   and the parts I can check are right: the four problems exist in Catalan with the stated level,
   label, topic and options; the neighbours are the ones named (`lvl-0_2024_3` 0.935 with picture,
   `lvl-2_2019_9` 0.914 with picture, `lvl-1_2021_21` 0.827, `lvl-3_2016_29` 0.810), all easier and
   of the same topic; the sim rehearsal reproduces both chains step by step with 0.0 s of model time;
   the controller then verified the same on the board (e5de2ff).
2. Every number spoken in the numbers and lessons blocks traces to `results-A.md` or
   `error-analysis.md` with its n (61/281, 23.1%, 16.9% on the top quartile, 130/562, 0.38 s, 40 s,
   0.12 s, 2.6 GB, 2 minutes, D 38% / C 3%, 4 of 911). The script says plainly that no learning
   figure exists and tells the speaker not to invent one.
3. **The script does not fit in 180 s.** At the pace the document itself sets (12 words in 5 s, 2.4
   words/s) the Catalan text takes 222 s: the numbers block has 138 words for 40 s (3.5 w/s) and the
   lessons block 115 words for 30 s (3.8 w/s). Numbers read aloud in Catalan ("seixanta-un de
   dos-cents vuitanta-un") are slower still.
4. **One sentence of the script is false for what the app would do next**: "el proper problema
   d'aquest tema li arribarà un nivell més fàcil" (demo, 70 s). After two answers the diagnostic is
   still running (minimum three), so Mariona1's third problem is `lvl-5_2011_18`, level 5 `areas`
   (`demo_pick.py --chain Mariona1 1`), four levels up, whatever she answered. If the jury says "show
   us", the page contradicts the speaker.
5. The script also says out loud what the main review flagged: "la pàgina li diu quina era" right
   after "guia sense donar la resposta". The jury will hear both.
6. License: `demo-problems.md` prints the five option values and the label of six problems and
   paraphrases their statements; the repository rule is ids only.

## Findings

**P1 (IMPORTANT). Timing.** Word counts (stage directions excluded): problem 60 words / 20 s,
demo 221 / 90, numbers 138 / 40, lessons 115 / 30; total 534 Catalan words, 527 English. At 2.4
w/s that is 222 s and 220 s. *Fix:* cut the numbers block to three figures (61/281 vs always D;
130/562 on the board, worst 40 s; 0.12 s per embedding and 2.6 GB free) and the lessons block to
two sentences, or move the "model confidence" sentence to the one-pager. Rehearse with a stopwatch
and write the measured time in `pitch.md`.

**P2 (IMPORTANT). The "next problem one level easier" promise is not what the trainer does.**
`pitch.md` demo row 70 (CA and EN). Reproduced: `python3 dev/demo_pick.py --chain Mariona1 1` gives
problem 3 = `lvl-5_2011_18` (level 5, areas, `ok: False`); `trainer._diagnostic_finished` needs three
answers. *Fix:* say "quan acabi el diagnòstic, els problemes d'aquest tema li arribaran més fàcils",
or have the trainer start the chain from the target level after the diagnostic (review-main I6).

**P3 (IMPORTANT). The pitch narrates the answer reveal as a feature.** Demo row 70: "la pàgina li
diu quina era". With `copilot/webapp.py` as it is (review-main C3) this is accurate, and it undercuts
the 13 s sentence "guia sense donar la resposta". *Fix:* either change the app (one more attempt
before the letter is shown) or drop the clause and let the cross and the mastery bar speak.

**P4 (IMPORTANT). M3Kang content in a committed document.** `docs/demo/demo-problems.md` lists the
option values and labels of `lvl-1_2024_2`, `lvl-3_2019_18`, `lvl-2_2020_4`, `lvl-4_2010_12`,
`lvl-3_2021_20`, `lvl-5_2022_30` and describes their statements ("the result is 777", "a grid of
forty cells", "buying boxes of eggs"). Options and labels are dataset content; the paraphrases are
the team's words but let a reader reconstruct the problem. `pitch.md` repeats "quaranta caselles"
and "vint-i-vuit caselles". *Fix:* keep ids, levels, topics and neighbour ids in the docs; move the
options, labels and descriptions to a file outside the repository (the runbook already has
`demo_pick.py --show` for the team's eyes).

**P5 (MINOR). Rung 2 is narrated as something it does not say.** Demo row 38: "files més columnes
menys la intersecció. Quinze, la C." The card shown is "Busca el patró que es repeteix i mira cada
quantes caselles torna a començar"; the reasoning comes from the speaker. Fine as theatre; say "la
Mariona pensa" rather than implying the card said it.

**P6 (MINOR). The teacher view will list every rehearsal pseudonym.** In my sim run
`/api/teacher` showed `Mar, Mariona1, Pau, student-test, test-webapp`. The runbook resets the demo
pseudonyms but not `prova`, `Guillem` or anything typed on other days. *Fix:* add to runbook step 5
a one-line clean of `data/students.db` (or `reset_student` for every row) the morning of the pitch.

**P7 (MINOR). First `Pista` after an app restart loads the index.** 0.21 s in sim (measured twice,
the first call of each run); the runbook's rehearsal warms it, but if the app is restarted
afterwards (contingency rows 3 and 4) the first hint on stage pays it on the board's CPU. Tell V2 it
may take a second or two.

**P8 (MINOR). `demo_pick.py` and the demo set disagree.** The content-curation branch chose four
other core problems (`lvl-0_2016_8`, `lvl-0_2019_22`, `lvl-0_2016_16`, `lvl-2_2016_2`) with
hand-written steps; the pitch uses `Mariona1`'s chain, for which no steps exist, and nothing in
`copilot/` reads `demo_set.json` anyway. See review-content-curation C1. One list must win.

**Runbook and contingency**: they cover what actually failed on the board on 14 Nov per
`docs/deploy-board.md` (`TMPDIR` over `adb shell`, `app start` refusing when running, the forward
dying when `adb` reconnects, the relay service, the 20 s page start, port 7000 vs AirPlay). Row 4
("hint over 10 s") correctly says the page stays `busy` and a reload does not help. Good.

## Figures checked (numbers and lessons blocks)

| Spoken | Source | Status |
| --- | --- | --- |
| 61 of 281 = 21.7%, always D 23.1% | results-A §Phase 1, error-analysis | ✓ |
| 16.9% in the most confident quartile | results-A §Phase 2 | ✓ (n = 70 of 281, as the one-pager says) |
| 130/562 = 23.1%, mean 0.38 s, worst 40 s, none over 60 | results-A §official run | ✓ |
| embedding 0.12 s, 2.6 GB free, cold start 2 min | results-A §Phase 10, deploy-board §5 | ✓ (2609 MB) |
| model picks D 38%, C 3% | results-A §Phase 2 prior | ✓ |
| 4 families, 911 problems, fire on 4 | results-A §Phase 5 (3 consecutive + 1 digit_count) | ✓ |
| quality gate 70% | config.env | ✓ |
| "every step under a second on the board" | e5de2ff: under 0.5 s | ✓ |
| four problems, labels C / E / A / E; reserve E / B | data | ✓ |

## Verdict

The problems, clicks and numbers are right and verified on the board; the script needs 40 s cut,
one false promise reworded, and the option values taken out of git.
