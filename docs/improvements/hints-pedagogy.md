# Hint ladder and pedagogy: what the rungs really show, and how to make them teach

Explorer D area, 14 Nov 2026, worktree `team/improvements-d18364` (= `origin/main` 5cc2ded). Read only,
ran things, changed no code. Builds on the reviewer's findings C2, C3, I1, I2, I3, I13, M3-M6, M8
(`origin/team/review-22fa88:docs/reviews/review-main-2026-11-14.md`); where I repeat one I say so and add the number.

**Summary (5 lines)**
1. On all 281 validation problems, in both languages, rung 3 is a second strategy card (281/281, verified), rung 4 has
   no explanation (trace 0/281) and no value for 109/281 Catalan problems: today the ladder is "a similar problem plus two
   topic cards", so it does not yet guide better than a plain neighbour (reviewer I13, now quantified).
2. The solver trace (rung 3a) cannot fire on the Catalan page at all: `hints._solved` gives `solvers.solve` the Catalan text
   and the four classifiers are English keywords (0/281 classified in Catalan, 7/281 in English, 0 fired).
3. The leak filter misses 75/110 adversarial hints (compound number words, dozen/half/pair, ordinals, option positions,
   expressions, Roman numerals, glued units) and wrongly rejects 12/40 harmless ones ("set", "nou", "deu", "un/una", "once").
4. The LLM gate is open for 63/281 English validation problems (all `areas`) on one judged sample; one live hint cost
   28.1 estimated board seconds, restated the question in English and was garbled in Catalan (reviewer I3 confirmed).
5. The pedagogy is sound in design (graduated, student-paced, no label before answering) but thin in content; the
   strongest no-LLM additions are hand-written steps for the demo set, the error-signature branch after a wrong attempt,
   option-derived sanity questions, and a rung 1 that becomes a self-checked worked example.

## What I ran

All from the worktree, `HINT_PREFETCH=off` where the ladder was called, data linked (`data/val.jsonl`, `data/index.db`).

| Command / action | Outcome | Status |
| --- | --- | --- |
| `python3 -m unittest discover tests` | 168 tests, OK, 1 skipped | ran |
| `HINT_PREFETCH=off python3 -m unittest discover tests` | **1 failure**: `test_prefetch_warms_in_a_thread_for_validated_topics` (the test reads `hints.PREFETCH` from the environment instead of patching it) | ran |
| `HINT_PREFETCH=off python3 -m unittest tests.test_hints tests.test_leak_filter` | 45 tests, the same single failure | ran |
| Scratch script `val_ladder.py`: `get_hint` rungs 1, 2, 3, 3, 4 on all 281 val ids x {cat, eng}, `hints.llm_hint` patched to a fake that returns `ok: False`, solvers real (7 English extraction calls to the shared server) | see table below | ran |
| Scratch script `leak_adv.py`: `leak_reason` on 110 adversarial and 40 harmless strings | 75/110 leaks missed, 12/40 harmless rejected (full list in "Leak filter" below) | ran |
| One live `hints.llm_hint` on `lvl-0_2017_7` (eng, `areas`, text-only, options read) | `ok`, `prompt_n` 221, `predicted_n` 49, 1 attempt, **28.1 estimated board seconds**, wall 1.1 s on the laptop; the English sentence (20 words) restates the question, the Catalan one (16 words) is not Catalan | ran |
| `solvers.classify` over val | eng: `average` 4, `ages` 3, none 274; **cat: none 281** | ran |
| Option statistics over the 281 English val rows | 167 with options; 137 with five parseable numeric options (127 all integers); 33 share a common factor >1; 33 are an arithmetic progression; 16 mix units; 18 span a factor >= 10; correct value is 7/9/10/1 in 12 | ran |
| `dev/start_servers.sh --status` | both servers up; total LLM calls I made: 9 (7 extractions + 2 hint calls); never stopped | ran |
| Read: `copilot/hints.py`, `copilot/leak_filter.py`, `data_curated/strategies.json` (all 40 cards), `data_curated/hint_quality.json`, `config.env`, tests, `INTERFACES.md` hint section, `docs/teach-measurement.md`, `docs/bilingual-rung.md`, `copilot/solvers/__init__.py`, `copilot/retrieval.py` 80-170, `assets/app.js` 118-140, `copilot/webapp.py` hint routes, `origin/team/innov-error-signatures-3b1c96:copilot/signatures.py`, its two docs and the 35-test file | | read only |

Ladder on the 281 validation ids (both languages give the same counts unless noted):

| measure | Catalan page | English page |
| --- | --- | --- |
| rung 1: easier neighbour / same level / none | 261 / 20 / 0 (the 20 are all the level-0 problems) | same |
| rung 1: neighbour has options / has image | 204 / 150 (150 = every visual-topic problem) | 211 / 150 |
| rung 1: cosine similarity mean / median / min | 0.759 / 0.761 / 0.526 | same |
| rung 1: label present in the payload | 0 | 0 |
| rung 2: strategy card | 281 | 281 |
| rung 3: trace / llm / strategy card | 0 / 0 / **281** | 0 / 0 (patched; gate open for 63) / **281** |
| rung 3 pressed twice: card, card | 281 | 281 |
| rung 3 card equal to the rung 2 card | 0 (the rotation works) | 0 |
| rung 4: has a trace / has a value | **0** / 172 | **0** / 167 |
| `estimated_board_seconds` other than 0.0 on rungs 1-4 | 0 | 0 |
| wall time rung 1 mean / max (laptop) | 0.010 / 0.037 s (one embedding per val id, cached after) | 0.001 / 0.003 s |

## Answers to the questions

- **Does the ladder guide better than a plain "here is a similar problem"?** Not yet on real data. Verified: rung 3 is a
  topic card on 281/281 and rung 4 is "Solució: opció X (value)." with no step on 281/281 (and no value on 109/281 in
  Catalan). The design (student-paced, graduated, label never before the answer, rung 0 separates reading from maths) is
  right and is what the jury should hear; the content behind rungs 3 and 4 is what is missing. P1-P5 fill it without
  the LLM.
- **Rung 1 as a worked example without leaking** (reviewer I1): the neighbour's label leaks nothing about the target
  problem (different id, different answer), so the honest version is a *faded* worked example: the student answers the
  neighbour first (one tap), then sees its letter, value and the topic card as the "why". P5.
- **Strategy cards**: 40 cards read; none gives an answer, the Catalan is good. Two are risky as facts (angles/4 does not
  say which total; spatial/2 assumes a standard die), one states the whole algorithm (counting/1), and the most useful
  Kangaroo strategy ("test each option in the statement") exists only in `logic`. Missing cards listed in P9.
- **Rung 3 without the LLM**: hand-written steps for the demo set (P2), the error-signature diagnosis after a wrong
  attempt (P3, 109/139 val problems with a numeric correct option have at least one signed distractor), and option-derived
  sanity questions (P4: units, magnitude, common factor, step, parity as a *question*).
- **Leak filter misses / over-blocks**: P6 and P7, with the lists.
- **Is the pedagogy sound for the jury?** The principles are; the evidence is not yet: no learning number (reviewer I10)
  and a rung 3 that equals rung 2. P11 gives the ladder its own measured table.

## Proposals

### P1. Rung 3a never fires on the Catalan page: solve on the English version
- **Where**: `copilot/hints.py:246-258` (`_solved` calls `solvers.solve(problem)` with the page-language problem),
  `copilot/solvers/__init__.py:30-37` (`classify` matches English keywords on `problem["text"]`).
- **Problem / opportunity**: `get_hint(id, 3, "cat")` looks up the Catalan row and passes it to the solvers, whose four
  `matches()` are English regexes (`consecutive (whole|...) numbers`, `average`, `years old`, `-digit`). Verified:
  `solvers.classify` over val gives 7 families in English and **0 in Catalan**; so on the Catalan page (the demo
  page) the solver trace is unreachable by construction, not only by data (reviewer I13 counted 0 fired on English).
- **Proposal**: in `_solved`, call `solvers.solve(problem_for(problem["id"], "eng") or problem)` and keep the result (the
  trace is bilingual, the options match by value). Add `test_rung3_trace_uses_the_english_text` with a Catalan fixture
  whose English twin is registered and a patched `solvers.solve` asserting the language of the text it receives.
- **Impact (student)**: medium: the trace still fires rarely (1 in 20 of its family), but today it is zero on the Catalan
  page and the docs promise it.
- **Effort**: S. **Risk**: none for INTERFACES; the English row exists for 281/281 val ids. Safe before the demo.
- **How to measure**: `solvers.classify(problem_for(id,"eng"))` count on val = 7 both pages; the existing trace test.
- **Verified**: ran (classify counts).

### P2. Hand-written steps for the demo problems, read by rung 3 and rung 4 (and fix the "Pas 2 de 3" count)
- **Where**: `copilot/hints.py:261-287` (`_rung3`), `:289-301` (`_rung4`), `data_curated/demo_set.template.json`
  (exists, never filled), `laptop/validate_demo_set.py` (exists), `INTERFACES.md` "Hint rungs" table.
- **Problem / opportunity**: rung 4 shows a trace for 0/281 val problems and no value for 109/281 Catalan problems
  (options not read by OCR): the "solution" is one line with a letter. Reviewer I13 proposes a demo set; this adds the
  concrete loader and uses it for rung 4 too, which the jury will see in the 3-minute demo.
- **Proposal**: (1) `hints._demo_steps(problem_id)` loads `data_curated/demo_set.json` once (ids, bilingual steps, a
  figure description); (2) in `_rung3`, source order becomes trace -> **demo steps** -> LLM -> card, the demo steps walked
  like the trace (never the last one), each step passed through `leak_reason` **before** counting, so `shown` is the
  number of steps that survive (closes reviewer M4: today `hints.py:266` counts, then `:273-275` skips); (3) `_rung4` uses
  the demo steps when the solver has none, and the figure description as the first line for visual problems;
  (4) fill the file with 12-16 ids: the 5 to 8 problems the trainer serves in the rehearsed demo plus one per topic at
  levels 0-2; `laptop/validate_demo_set.py` must assert every step passes the leak filter and the last step is the only
  one with the value; (5) INTERFACES: `kind` gains `"demo"` (or reuse `"trace"` with a `source` field). Tests: a fixture
  demo set in `tests/`, rung 3 walks it, rung 4 shows it, a leaking step is dropped and the count is right.
- **Impact (jury)**: high: the demo's rung 3 and rung 4 become a real worked solution, the jury's "guide without revealing"
  becomes visible.
- **Effort**: M (the code is 1 h; the 12-16 bilingual step sets are the team's hour). **Risk**: touches INTERFACES (one
  row); the trainer must actually serve those ids in the demo (reviewer I13, trainer owner). Safe before the demo if the
  ids are the rehearsed ones.
- **How to measure**: `val_ladder`-style count of rung-3 sources on the demo ids = demo 100%; rung 4 trace length > 0 on
  them; `validate_demo_set.py` green.
- **Verified**: ran (0/281 traces, 109/281 missing values).

### P3. The error signature as the rung-3 content after a wrong attempt
- **Where**: `origin/team/innov-error-signatures-3b1c96:copilot/signatures.py` (`diagnose(problem, letter)`, 35 tests,
  leak-filtered), `copilot/hints.py:261` (`_rung3`), `copilot/webapp.py:260-270` (`answer`), reviewer C3.
- **Problem / opportunity**: the branch shows the diagnosis under the cross, after the answer is already revealed (C3),
  so it teaches nothing the student can still use. Its coverage is the best no-LLM rung-3 content we have: 74% of the
  938 problems with a numeric correct option have at least one signed distractor (val: 109/139, from the branch's
  `docs/error-signatures-coverage.md`, read only), the texts never contain the value or the letter, and they are
  *specific to the student's slip* ("you counted one too many: check the end points"), which no card is.
- **Proposal**: once C3 gives a second attempt: `hints.note_attempt(problem_id, letter)` stores the wrong letter in
  `_state[pid]["attempt"]`; `_rung3` tries `signatures.diagnose(problem, letter)` first when an attempt exists and the
  signature is not `"none"`, returning `kind: "diagnosis"`; the webapp calls `note_attempt` on a wrong first answer and
  offers "Pista" again. `get_hint`'s signature is unchanged (state, like the card rotation). INTERFACES: add
  `"diagnosis"` to `kind` and one sentence under C3's new two-attempt rule. Tests: wrong letter + numeric options ->
  diagnosis at rung 3; `"none"` -> falls through to the next source.
- **Impact (student)**: high: a hint about *their* mistake is the single most effective tutoring move and costs 0 s.
- **Effort**: M (wiring; the module exists). **Risk**: depends on merging the branch and on C3 (webapp); touches
  INTERFACES. Do it before the demo only if C3 lands the same day; otherwise after.
- **How to measure**: on the 139 val problems with a numeric correct option, pick every distractor as the first attempt
  and count rung-3 kinds: diagnosis for 1381/3557 distractors (39%), per the branch's table.
- **Verified**: read only (branch); coverage numbers are the branch's, not recomputed.

### P4. Option-derived sanity questions as a rung-3 source (no LLM, no label)
- **Where**: new `copilot/option_checks.py` (stdlib), called from `hints._rung3` between the trace/demo steps and the LLM.
- **Problem / opportunity**: 137/281 English val problems (172/281 Catalan have options; 120 all-numeric) carry five
  numeric options that are themselves a teaching object, unused today. Measured on the 137: 16 mix units, 18 span a
  factor >= 10, 33 share a common factor > 1, 33 are an arithmetic progression (the classic off-by-one trap), 127 are
  integers (parity question possible). None of these texts needs the label, so they leak nothing.
- **Proposal**: deterministic, in this order, one per press: (a) mixed units -> "Les opcions no són totes en la mateixa
  unitat: passa-les a una abans de comparar"; (b) factor >= 10 -> "Estima primer l'ordre de magnitud del resultat: les
  opcions van de X a Y" (X, Y are the min and max option, allowed only when neither is the correct value; otherwise
  omit the numbers); (c) arithmetic progression -> "Les opcions van de d en d: un error d'un de més o de menys cau a
  l'opció del costat; revisa els extrems del recompte"; (d) common factor g -> "Totes les opcions són múltiples de g:
  pensa en grups de g"; (e) integers -> the parity *question*: "Quantes opcions són parelles? El resultat ha de ser
  parell o senar? Per què?" (never which). Every text goes through `leak_reason` with the real options; if it fails,
  skip. Add `kind: "check"` to INTERFACES. Tests: each rule on a synthetic option set; the leak filter drops a text that
  names the value.
- **Impact (student)**: medium: on about half of the problems rung 3 stops being a copy of rung 2, and the moves taught
  (units, estimate, parity, end points) are exactly Kangaroo's distractor design.
- **Effort**: M. **Risk**: low; INTERFACES one row; safe before the demo (deterministic, 0 s). The magnitude text must
  never print the correct value: rule (b) above.
- **How to measure**: rerun the ladder count on val: rung-3 `check` share (expected about 45-50% in English, higher in
  Catalan where 172 rows have options); 0 leaks when every produced text is passed to `leak_reason`.
- **Verified**: ran (the counts); the texts are a proposal.

### P5. Rung 1 as a faded worked example: the student answers the neighbour, then sees its answer and the "why"
- **Where**: `copilot/hints.py:208-234` (`_rung1` strips `label`, line 221), `copilot/webapp.py` (`hint`, `/api/state`),
  `assets/app.js:122-127`, `INTERFACES.md` rung table ("an easier solved neighbour problem"), `docs/README-final-draft.md`,
  `docs/project-hub-draft.md` (reviewer I1).
- **Problem / opportunity**: the neighbour is good (261/281 strictly easier, same topic by construction, similarity
  0.76, image on every visual-topic problem, options on 204/281) but *unsolved*: a stuck student now holds two problems.
  The neighbour's answer carries no information about the target's answer, so revealing it after an attempt is safe.
- **Proposal**: the rung-1 card gets a mini A-E row (when the neighbour has options) or a "Ja ho tinc" button; the page
  posts `/api/neighbour/{letter}`; the server, which keeps the neighbour's label in the session only (never in
  `/api/state`), replies right/wrong, then shows "Resposta del problema semblant: opció X (valor)" plus the first topic
  card as the explanation (or the demo steps of P2 when the neighbour is in the demo set: pick neighbours from the demo
  set first in `_rung1` when one is within one level). Timeline row `rung1:neighbour-answer`. Mastery untouched.
  Rename the rung in INTERFACES and the drafts: "an easier neighbour to solve first, then its answer"; replace
  "nivell N" with the school year in `_rung1`'s text (reviewer M8). Tests: webapp test that `/api/state` never carries the
  neighbour label before or after; the reveal text contains the neighbour's letter only after a post.
- **Impact (jury/student)**: high: it is the Bastani-style worked example the Project Hub draft promises, and it gives
  the student a success before the hard problem.
- **Effort**: L (server + page + docs). **Risk**: touches INTERFACES and the page; moderate. Not the day of the demo.
- **How to measure**: the people protocol (`docs/teach-measurement.md`): accuracy after rung 1 with vs without the reveal;
  automatic check: 0 occurrences of the neighbour label in `/api/state` across a scripted session.
- **Verified**: ran (rung-1 statistics); the design is read/reasoned.

### P6. Leak filter: the classes it misses (75/110 adversarial strings)
- **Where**: `copilot/leak_filter.py:21-37` (`_WORDS` 0-20, tens, 100, 1000), `:39-50` (`_PHRASES`), `:52` (`_UNITS`),
  `:78-96` (`_spellings`), `:98-111` (`_core`, `_contains_token`), `:113-151` (`leak_reason` letter patterns).
- **Problem / opportunity**: reviewer I2 found 24/34; my 110-string list missed 75. By class (all verified):
  compound number words in the three languages (`vint-i-quatre`, `twenty-four`, `twenty four`, `noranta-nou`,
  `vuitanta-un`, `cent vuitanta`, `one hundred and eighty`, `veinticuatro`, `trenta-sis`, `dos-cents`, `two hundred`);
  quantity words (`una dotzena`, `a dozen`, `mitja dotzena`, `la meitat`, `un parell`, `a pair`, `el doble de nou`,
  `twice nine`, `una vintena`, `a score`, `one and a half`, `un i mig`, `a third`); expressions whose value is the
  answer (`2x9`, `3*6`, `3·6`, `9+9`, `20-2`, `36/2`, `2^3`, `3 x 6`, `nou per dos`); Roman numerals (`XVIII`, `MMXXIV`);
  separators and spacing (`2.024`, `1.800`, `1 8`, `1,8` for 18, `18e`); glued or compound units (`18cm`, `18m²`,
  `18km/h`, `18years`; `18 cm` and `18 €` are caught); Arabic-Indic digits (`١٨`; fullwidth `１８` is caught by NFKC);
  ordinals of the value (`18th`, `18è`, `divuitè`, `the eighteenth`); the letter by position (`la tercera opció`,
  `the third option`, `the middle option`, `l'opció del mig`, `the last option`, `la primera opció`, `the smallest option`,
  `l'opció més gran`, `the letter after B`, `not A, B, D or E`); the lower-case letter in prose (`És la c.`, `It's c`,
  `Només queda la c.`, `C es la buena`); a multi-word text option written partly (`Anna i Berta` for "Anna and Berta").
  The LLM grammar (`hints.py:335`) forbids digits, so for the model path the live risk is the **word** classes; the digit
  classes matter for the solver traces, the demo steps (P2), the signature texts (P3) and the option checks (P4), which
  all rely on this filter.
- **Proposal**: (1) `_number_words(n)` generating Catalan (`vint-i-`, `-anta-`, `-cents`), English (`twenty-four` /
  `twenty four` / `one hundred and`), Spanish (`veinti-`, `y`) forms for 21-999 from the parts, used by `_spellings`;
  (2) a small `_QUANTITY` table: dozen/dotzena/docena -> 12, half-dozen -> 6, pair/parell -> 2, score/vintena -> 20,
  half/meitat/mitad -> 1/2, third/terç -> 1/3, double/doble/twice + number word -> 2n, "and a half"/"i mig" -> n+0.5;
  (3) evaluate `a (x|*|·|+|-|/|^|per|by|times) b` with small integers and compare with the value; (4) Roman numerals
  regex `^[IVXLCDM]+$` per token -> value; (5) normalise `\d{1,3}[.\s]\d{3}` -> digits, `\d[ ,.]\d` -> both readings,
  and `unicodedata.digit(ch, None)` for any script; (6) `_UNITS` without the trailing `\b` and with compound units
  (`km/h`, `m/s`, `cm3`, `years`, `anys`, `€` on either side); (7) ordinals: `18th|18è|18a|divuitè|eighteenth` from the
  parts; (8) letter by position: `(first|second|third|fourth|fifth|primera|segona|tercera|quarta|cinquena|middle|del mig|
  last|última|darrera|smallest|largest|més gran|més petita) (option|opció|one|answer)` -> the letter that position
  denotes (A-E or by option order/value) == label -> "letter"; `(la|the|és|es|it's) ([a-e])\b` with the lower-case
  label; `not` + the four other letters; (9) a text option of several words: match each word of length >= 4.
  Add all 110 strings to `tests/test_leak_filter.py` as data (no problem text in them).
- **Impact (jury)**: high: "never reveals" is the jury's criterion and the reviewer already wrote this gap down.
- **Effort**: M (the generators are 60 lines; the tests are the list). **Risk**: more false rejections (P7 must come with
  it); no INTERFACES change; safe before the demo because the LLM gate is closed on the Catalan page (P8).
- **How to measure**: `leak_adv.py`: 110/110 caught; `tests/test_leak_filter.py` SAFE list still passes; the signature
  branch's texts (`signatures.py`, 14 strings) still pass with the real options of val (its `dropped_by_leak_filter` count).
- **Verified**: ran.

### P7. Leak filter: what it over-blocks (12/40 harmless strings) and the language-aware fix
- **Where**: `copilot/leak_filter.py:21-37` (`_WORDS`: `set`=7, `nou`=9, `deu`=10, `once`=11, `un/una`=1, `cent`=100),
  `:132` (bare letter at the very end), `copilot/hints.py:459-466` (the retry costs a second pair of calls).
- **Problem / opportunity**: verified false rejections: "Set the pieces side by side." / "A set of cards." / "Set up the
  equation." (answer 7), "Un problema nou." (9), "Deu ser més gran." (10), "Once you count them, compare." (11), "Hi ha un
  dibuix." / "Una figura." / "Compta en una taula." (1), "Cent per cent dels casos." (100), "Vertex C." (letter C). The
  cost is real: a false rejection on the LLM path triggers the strict retry (another 2 calls, up to 28 s each on the
  board) or loses the hint; the signatures branch already contorts its Catalan to avoid `un/una` (its docstring says
  so); the correct value is 7, 9, 10 or 1 on 12/137 numeric val problems.
- **Proposal**: `leak_reason(hint, label, options, lang=None)`: when `lang` is given, use only that language's number
  words (English hints never match `set`, `nou`, `deu`, `cent`; Catalan hints never match `once`); `llm_hint` passes
  `call_lang`, the trace/demo/signature callers pass `"cat"` / `"eng"` per field. For the words that are also function
  words in their own language, require a quantity context: `un|una` count as 1 only in `un sol|una sola|només un|
  exactament un|un únic`; `deu` not when followed by `ser|haver|de`; `nou` not when it follows a noun (`problema nou`,
  `de nou`); `cent` not inside `per cent|percent`. Keep the bare-letter end rule but exclude the geometric nouns
  `vertex|vèrtex|punt|point|angle|costat|side` immediately before the letter. Add the 40 harmless strings as a SAFE
  list in the tests.
- **Impact (student)**: medium: fewer lost hints and fewer 28 s retries; frees the authors of P2/P3 texts from
  avoiding ordinary Catalan words.
- **Effort**: S-M. **Risk**: `lang=None` keeps today's behaviour, so callers can migrate one by one; INTERFACES does not
  list `leak_reason`. Safe before the demo.
- **How to measure**: `leak_adv.py` harmless list 40/40 pass while the adversarial list stays caught; the existing
  `SafeHintsTest` passes.
- **Verified**: ran.

### P8. Close the LLM gate on evidence, make it one call, and make the tests independent of config.env
- **Where**: `copilot/hints.py:174-191` (`quality()` accepts `n` >= 1, `:193` `llm_allowed`), `data_curated/hint_quality.json` (`areas: n=1,
  percent_en=100`; the `judge` string, reviewer C1), `config.env` `HINT_LLM_LANG=` (empty -> two calls), `hints.py:62-66`
  (`_llm_langs`), `tests/test_hints.py:134` (`test_prefetch_warms...` fails with `HINT_PREFETCH=off`).
- **Problem / opportunity**: verified: `llm_allowed("areas","eng")` is True, so the English page would call the LLM on
  63/281 val problems (22%, all `areas`); one live call cost 28.1 estimated board seconds (221 prompt + 49 generated
  tokens over two calls), the English sentence restated the question and the Catalan one was not Catalan (reviewer I3,
  reproduced on `lvl-0_2017_7`). The Catalan page makes an English call it never shows (`HINT_LLM_LANG` empty ->
  `("cat","eng")`). And `tests/test_hints.py` reads `hints.PREFETCH` from the environment: the suite is green only with
  the default `config.env`, which hides that the gate logic is untested under `off`.
- **Proposal**: `quality()` returns None unless `n >= HINT_QUALITY_MIN_N` (new key, default 10); `_llm_langs` makes
  one call in the shown language (`HINT_LLM_LANG=en` for the English page, Catalan never until judged >= 70 on 10);
  replace the `judge` string with initials; in the test, `mock.patch.object(hints, "PREFETCH", "warm")`. Keep the
  `warm` prefetch, drop `full` as default (reviewer M3: the join can wait 60 s and then call again).
- **Impact (jury)**: high: no 28 s wait in the demo, no restated question shown as a "model hint", and an honest story
  ("the model writes hints only for topics we judged, none yet").
- **Effort**: S. **Risk**: none; config and one function. Safe before the demo.
- **How to measure**: `llm_allowed(t, l)` False for all 8 topics x 2 languages on today's file; `HINT_PREFETCH=off
  python3 -m unittest discover tests` green.
- **Verified**: ran.

### P9. Strategy cards: fix two facts, soften one algorithm, add the eight missing Kangaroo moves, show the topic
- **Where**: `data_curated/strategies.json` (40 cards), `assets/app.js:133` (card header), reviewer M8 and I8.
- **Problem / opportunity**: read all 40. Wrong or risky: `angles/4` "divide the total" without saying the total of a
  regular n-gon ((n-2)·180°) invites 360°/n; `spatial/2` "opposite faces add up to 7" is false for the lettered and
  picture cubes Kangaroo likes. States the algorithm (reviewer M8): `counting/1`. Generic: `arithmetic/0` (fine as the
  universal first card) and `logic/4` "test each option against the clues", which is the **most useful Kangaroo
  strategy** and exists only in `logic`. Missing moves that recur in M3Kang: working backwards from the end state
  (arithmetic), testing the options in the statement (arithmetic, digits, areas), cube nets (spatial), paper folding
  and cutting (spatial), fixing the first digit and counting the rest (digits), a fraction of a quantity (areas), pairs
  among n (counting), an invariant that every move preserves (boards). With a 76% topic map (I8) the card's topic is
  invisible to the student.
- **Proposal**: edit the two facts (`angles/4`: "els angles exteriors de qualsevol polígon sumen 360°"; `spatial/2`:
  "en un dau normal..."), reword `counting/1` as a question ("quants camins arriben a cada casella des de dalt i des de
  l'esquerra?"), apply M8's wording (`ratlla`, `recta numèrica`, `operació inversa`), add one card per missing move
  above (8 cards, Catalan first, English twin), and add "Prova les opcions a l'enunciat" as card 1 of `arithmetic`,
  `digits` and `areas`. Page: header "Estratègia · Angles" from `topics.TOPICS` so a wrong topic is visible. Tests:
  `test_every_topic_has_strategies_in_both_languages` already enforces shape; add a leak check of every card against a
  value set {1..20, 7, 180, 360} to be sure no card names a common answer (today `angles/0,2` contain 180 and 360: fine
  as facts, but P6's filter would reject them if an answer were 180°, so keep the cards digit-free where possible).
- **Impact (student)**: medium; it is the rung most students will see twice.
- **Effort**: M (content). **Risk**: none; safe before the demo.
- **How to measure**: 48 cards, every card passes `leak_reason` for the 281 val label/option sets of its topic.
- **Verified**: read only.

### P10. Small truths: the rung-1 board clock and the level wording
- **Where**: `copilot/hints.py:213` (`retrieval.neighbors` call), `copilot/retrieval.py:111-125` (`query_vector` embeds
  an id that is not in `index.db` and returns `embeddings_used`), `hints.py:224` ("nivell N").
- **Problem / opportunity**: every val/test id is outside `index.db`, so the first rung 1 on a problem costs one
  embedding (0.12 s on the board, `BOARD_EMBED_SECONDS`), yet `estimated_board_seconds` is 0.0 for 281/281 (verified).
  Small, but the page prints "placa (est.) 0.0 s" next to it and the jury asks for honest clocks. And a child who chose
  "5è de primària" reads "nivell 1" (reviewer M8).
- **Proposal**: `retrieval.neighbors` already knows `_embeds`; expose it (`neighbors_with_cost` or a module-level
  `last_cost`) and let `_rung1` set `estimated_board_seconds = embeds * BOARD_EMBED_SECONDS`; show the school year via
  the same table the start screen uses.
- **Impact (jury)**: low. **Effort**: S. **Risk**: none; safe before the demo.
- **How to measure**: rung 1 on a fresh val id reports 0.12; a second call 0.0.
- **Verified**: ran.

### P11. Measure the ladder itself: `laptop/measure_ladder.py` and a coverage table in the docs
- **Where**: new `laptop/measure_ladder.py` (the scratch `val_ladder.py` above, cleaned), new section in
  `docs/teach-measurement.md` or `docs/results-A.md`, README limitations.
- **Problem / opportunity**: the jury asks for measurement; the ladder has none. The numbers exist in one run: rung 1
  easier 261/281 (level 0: same level, said so), similarity 0.76, image 150/150 visual, options 204/281; rung 3 sources
  0/0/281; rung 4 trace 0/281, value 172/281; 0.0 board seconds on rungs 1-4. After P1-P4 the same script shows the
  before/after the jury wants (rung-3 source shares, rung-4 explanation share).
- **Proposal**: the script takes `--input data/val.jsonl --lang cat|eng`, patches `llm_hint` to a counter (never calls
  the server), prints the table above as markdown, writes ids-only JSON to `results/ladder-val.json`; the docs quote
  the table with the date and the commit.
- **Impact (jury)**: medium: it turns "we have a ladder" into a measured claim and exposes regressions.
- **Effort**: S. **Risk**: none. Safe before the demo.
- **How to measure**: the table in the doc equals the script's output on the current commit.
- **Verified**: ran (the numbers).

## Discarded

- **LLM-written worked solutions for the neighbour or the target.** Breaks the design principle (the LLM never reasons);
  the 0.8B model answers at chance (23.1%) and one hint already costs 28 s of board time; a solution would exceed 60 s.
- **Elimination hints that state a property of the correct answer** ("the answer is even", "it is not A or E"). They
  leak one to two bits of the label before the student answers and contradict "never reveal the label or value" in
  spirit; the question form of P4 keeps the move and drops the leak.
- **Rung 3 from solver traces on neighbours in `train.jsonl`.** Only 4 family solutions fired on 1,466 train problems
  (`docs/results-A.md`), so a "solved neighbour" would almost never exist; the demo set (P2) is the honest source.
- **Translating the English LLM hint into Catalan with the model.** Its Catalan is the failure mode (verified live);
  showing the English sentence with the "in English" badge, as `HINT_LLM_LANG=en` already does, is the only option.

## Table

| n | title | impact | effort | safe before demo |
| --- | --- | --- | --- | --- |
| P1 | Rung 3a: solve on the English version (dead on the Catalan page) | medium | S | yes |
| P2 | Demo-set steps for rung 3 and rung 4, fix the step count | high | M | yes (demo ids) |
| P3 | Error signature as rung-3 content after a wrong attempt | high | M | only with C3 |
| P4 | Option-derived sanity questions as a rung-3 source | medium | M | yes |
| P5 | Rung 1 as a faded worked example (answer the neighbour, then see its answer) | high | L | no |
| P6 | Leak filter: compound words, quantities, expressions, ordinals, positions, units | high | M | yes |
| P7 | Leak filter: language-aware words, stop over-blocking set/nou/deu/un/once | medium | S-M | yes |
| P8 | LLM gate n >= 10, one call, judge string, test independent of config | high | S | yes |
| P9 | Strategy cards: two facts, eight missing moves, topic in the header | medium | M | yes |
| P10 | Honest rung-1 board clock and school-year wording | low | S | yes |
| P11 | `measure_ladder.py` and a measured ladder table in the docs | medium | S | yes |
