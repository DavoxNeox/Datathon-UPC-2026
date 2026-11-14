# Review of `team/content-curation-a0bddb` (merged into main at 8501c23)

Scope: `data_curated/demo_set.json` (13 problems), `data_curated/strategies.json` (19 cards edited, 3
replaced), `tests/test_content.py`, `docs/content-review.md`. Nothing changed by me.

**Executed**: the suite on `origin/main` (181 tests OK, `test_content` included, with the data
linked); every demo_set answer compared with the real label and the option value; every demo_set
field scanned for 6-word windows copied from the Catalan or English statement; the option values
quoted inside each entry listed; the 40 strategy cards read in both languages. **Only read**:
the proposed interface strings (not applied), the signature text proposals.

## Executive summary

1. The brief promised a demo set with checked solutions, corrected strategy cards, content tests and
   a Catalan review of the interface. Delivered, and the checks hold: **13/13 solutions name the
   right option and value** against `val.jsonl`/`train.jsonl` (the doc says 12; the file has 13);
   no field copies a statement at the test's 12-word window, and at a stricter 6-word window only one
   generic phrase matches ("quants punts hi ha en total"); the leak filter accepts every text before
   the last step.
2. The strategy cards are better than before: the Catalan fixes are right (`ratlla`, `mentalment`,
   `recta numèrica`, weak pronouns), the 15-word rule is enforced by a test, and the three
   substitutions are justified against real problems of the topic. None of the 40 gives an answer.
3. The set is not the demo. The pitch (merged minutes earlier) runs `Mariona1`'s and `Guillem`'s
   chains (`lvl-1_2024_2`, `lvl-3_2019_18`, `lvl-2_2020_4`, `lvl-4_2010_12`); `demo_core` names four
   other problems, and no code in `copilot/` reads `demo_set.json`. The 13 hand-written solutions
   will not appear on stage or on the page.
4. Every entry quotes the option values of its problem (12 of 13), and the `figure_*` fields describe
   the statements. Our own words, but with the options and the label they let a reader rebuild the
   problem; the repository rule is ids only.

## Findings

**C1 (IMPORTANT). The demo set is disconnected from the demo and from the code.** `demo_core` in
`data_curated/demo_set.json` vs the chains in `docs/demo/demo-problems.md`; `grep demo_set copilot/`
finds nothing on main. `docs/content-review.md` §5 says so ("no reader in copilot/ yet"). *Fix:*
either (a) write entries for the four pitch problems and make `hints._rung3` read `demo_set.json`
steps (never the last one) before the solver trace, so rung 3 on stage is a real step and not a
second card (review-main I13), or (b) keep the file as a reserve and say in the doc that it is not
used. (a) is a few lines and turns the best content of this branch into the demo's rung 3.

**C2 (IMPORTANT). Dataset content inside the committed file.** Option values appear in 12 of 13
entries (for instance `lvl-0_2015_17`: 3, 5, 7, 8, 9 are all five options; `lvl-0_2016_16`: 48, 40,
32, 16 cm), labels are stated in the last step by design, and `figure_ca/en` describe the statement
("una bossa amb boles de tres colors…"). `tests/test_content.py` only forbids 12 consecutive words
equal to the statement. *Fix:* decide the rule once with the controller: if "ids and our own words"
allows descriptions and the answer, write that in `data_curated/README.md`; in any case drop the
distractor values from the text (a step can say "el doble" without quoting the option) and add a test
that no entry contains more than two of its five option values.

**C3 (MINOR). Two solutions need a human check before `reviewed`.** `lvl-2_2016_2`: the doc notes a
non-standard die (a 3 on two faces); the step adds visible dots to 15 and hidden to 27, which matches
the label, but a jury member who knows dice will object to "cares oposades sumen 7" if that card is
shown with this problem. `lvl-2_2017_21`: the seven clock times are approximations; the last step
lists them, fine, but "9:00" and "9:33" are not both right angles at those minutes without rounding.
Both are flagged `draft` by the author; keep them out of the core until a second person signs.

**C4 (MINOR). Strategy cards: three remarks on the 40.**
- `angles/5` "Al rellotge, l'agulla gran gira 6° per minut i la petita, mig grau" is a fact for one
  problem type, not a strategy; the replaced "polígon regular" card served levels 6-7. Keep both if
  the 15-word rule allows six cards.
- `counting/5` "Si demana «estar-ne segurs», pensa en el pitjor cas: la sort va en contra" is the
  strongest card in the set: for `lvl-0_2016_8` it is the whole method (the author knows; it is the
  demo_core problem). Acceptable at rung 2, but it is close to a solution for that family.
- `digits/3` "diu si el nombre és parell o acaba en zero" lost the multiple-of-5 case the old card
  had; "parell, o múltiple de cinc o de deu" is 15 words.
  English versions align with the Catalan; the `_comment` states the rule. No card announces an
  option or a value that equals an answer except by coincidence of general facts (7, 180°, 360°).

**C5 (MINOR). Interface strings (§3 of the review, not applied).** The proposals are sound Catalan;
the ones worth applying before the demo are the ones marked "demo": "No és aquesta. La resposta
correcta era la X", "Preparant una pista…" (the app must not claim it thinks), "Tria una resposta o
demana una pista" (no comma), "Canvia d'alumne". Two I would not apply: "Nom o àlies" invites real
names on a public teacher page (the pseudonym rule is a privacy feature; say "Àlies (no el nom)"),
and "Molt bé, correcte!" is fine but changes a tested string in `webapp.py`.

**C6 (MINOR). `tests/test_content.py` strips `cm2`/`m2` itself before calling the leak filter**
because the filter reads `27cm2` as 27 and 2. The right fix is in `copilot/leak_filter.py:_numbers_in`
(review-main I2 lists the filter's gaps); until then the test is more lenient than the ladder.

**C7 (MINOR). Counts.** The doc says 12 problems; the file has 13 (`lvl-1_2022_13` is in the table
but not in the "12"). `status` is `draft` everywhere and the file's own `_about` says a person must
check each against the image: the author did (every image opened, per §1), so the entries the
author checked can be marked `reviewed` with the initials.

## Figures checked

| Claim | Recomputed | Status |
| --- | --- | --- |
| every answer re-derived and compared with the label | 13/13 letters and values match `val`/`train` | ✓ |
| no field shares 12 consecutive words with a statement | true; at 6 words one generic phrase | ✓ |
| leak filter accepts every pre-final text | `test_content` passes with data linked | ✓ |
| 19 cards edited, 3 replaced, ≤ 15 Catalan words | diff and test agree | ✓ |
| images opened for each problem | not checkable here | read only |

## Verdict

Good content, correct answers, the best Catalan in the repository; wire it to rung 3 for the pitch
problems or say it is unused, and take the option values out of the file.
