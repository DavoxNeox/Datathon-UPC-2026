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
