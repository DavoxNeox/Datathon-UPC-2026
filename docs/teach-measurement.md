# Measuring the Teach track with people (protocol, 30 minutes, 3 people)

The jury asks for a number measured before and after. The simulators (`copilot/simulate.py`)
give convergence figures; this protocol gives a figure with people, on the board.

1. Three team members, one pseudonym each (`p1`, `p2`, `p3`), start at the same level (the
   level selector on the start screen, for example 2).
2. **Without hints:** 5 problems each, answered without pressing "Pista". Note right/wrong.
3. **With the ladder:** 5 more problems each. On a wrong first thought, climb the ladder rung
   by rung before answering; note the rung used and right/wrong. `record_answer` stores the rung.
4. Export from the board:

```bash
python3 -c "from copilot import trainer; import json; print(json.dumps(trainer.teacher_report(), ensure_ascii=False, indent=1))" > results/teach-people.json
```

Report, with n = 15 answers per condition: accuracy without hints, accuracy after rung 1 or 2
(counts as "with hints"), how many times rung 3 or 4 was needed, and seconds per problem
(`timeline` in `/api/state`). Say plainly that n is small and the people are the authors.

## Rung 0 (reading in the other language): does it cut reading failures? (10 minutes, 4 people)

Rung 0 shows the same problem in the other language and is not counted as a hint. The question is
whether a wrong answer came from the statement or from the maths. A 10-minute protocol with the
team, on the board or in sim mode, that keeps the two conditions apart:

1. **Material**: 8 validation problems of level 2 whose Catalan and English versions exist
   (all 281 do) and whose options were read in both languages (158 do), 4 of them `text_only`.
   Fix the list of ids beforehand (`results/bilingual-protocol-ids.txt`, ids only) and use the
   same 8 for everyone, in the same order. Start screen: level 2, one pseudonym per person and
   condition (`r0-on-1`, `r0-off-1`, ...).
2. **Two conditions, crossed**: persons 1 and 2 do problems 1 to 4 with rung 0 **allowed** (press
   "Llegeix-lo en anglès" whenever a sentence is unclear, before anything else) and 5 to 8 with
   rung 0 **forbidden**; persons 3 and 4 the other way round. Nobody uses rungs 1 to 4; "Solució"
   is forbidden too. Reading language: the Catalan page for everyone.
3. **One minute per problem**, timed by the page's `timeline`; after 60 s answer anyway.
4. **After each wrong answer**, the person says in one word why: `reading` (did not understand a
   sentence or a word), `maths` (understood, could not solve), `time`. Write it next to the id.
5. **Export** from the board, ids only:

```bash
python3 -c "from copilot import webapp; import json; print(json.dumps(webapp.SESSION.teacher()['rung0'], ensure_ascii=False, indent=1))" > results/rung0-people.json
```

Report, with n = 16 answers per condition: accuracy with rung 0 allowed against forbidden, how
many times rung 0 was opened (`uses`) and on how many problems, the share of wrong answers tagged
`reading` in each condition, and seconds per problem. The number that answers the question is the
difference in `reading` failures between the two conditions; a difference in accuracy alone can
come from the maths. Say plainly that n is small, that the people are the authors (fluent in both
languages, so the effect is a floor for real students) and that the 60 s cap is ours.
