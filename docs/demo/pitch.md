# The 3-minute pitch: script, word by word

Structure suggested by the organisers: problem (20 s), live demo (90 s), numbers (40 s),
lessons (30 s). Catalan first (the jury is local), English below. Every number in the
"numbers" block comes from `docs/results-A.md`, `docs/reason-experiments.md` or `docs/error-analysis.md` with its n. Time
stamps are cumulative inside each block and assume **2.4 words per second** (12 words every
5 s, a calm pace); the word counts below are of the spoken text only.

| block | Catalan words | at 2.4 w/s | budget |
| --- | ---: | ---: | ---: |
| problem | 49 | 20 s | 20 s |
| demo (narration; the clicks and the LED fill the rest) | 196 | 82 s | 90 s |
| numbers | 96 | 40 s | 40 s |
| lessons | 72 | 30 s | 30 s |
| **total** | **413** | **172 s** | **180 s** |

**Grading (rules changed on 14 Nov 2026):** 50% Reasoning, an objective test exam corrected
from `predict.py`'s CSV (`runbook.md` §11), and 50% Teaching, judged by the jury in these
three minutes. The script presents both halves as what they are.

## What the jury must notice (five lines)

1. **The small model does not reason in text, and that is a virtue on stage:** measured at chance
   level (21.7% on M3Kang), so nothing on stage waits for it, nothing it says can be wrong; what
   works is making it write a short program that the board runs, exact when it is right.
2. **The student reasons:** three hints and a lesson, climbed on demand; the answer never
   appears before the student commits.
3. **M3Kang is the teacher:** the neighbour hint, the correction and the level come from the
   dataset's own labels and structure, not from generated text.
4. **Everything runs offline on the board:** one USB cable, and the page's own timing table
   shows real seconds per step (under a second).
5. **The Reasoning half is measured and honest:** the exam policy is a program the model writes
   and the board runs (38/100 on the practice set on the laptop; 8 of 20 on the board against 5
   for brief reasoning, a small sample), numbers and limits included.

Four voices. The team decides who is who (see the report); the roles are:

| voice | block | also |
| --- | --- | --- |
| **V1** | problem (20 s) | holds the board up during the demo |
| **V2** | narrates the demo (90 s) | |
| **V3** | numbers (40 s) | drives the laptop during the demo (the clicks, no talking) |
| **V4** | lessons (30 s) | timekeeper: shows V2 a hand signal at 60 s and 80 s of the demo |

The click script that V3 follows is in `docs/demo/demo-problems.md` (chain "Mariona1 / 6è de
primària"). The pseudonym and course are typed before the pitch starts, with the start screen
on the projector; the first click of the demo is "Comença". What V2 says about each problem is
only what the page shows at that moment; the speaker's own notes (answers, what the figures
look like) are in `docs/demo/local/demo-notes.md`, never in git.

---

## Català

### 1. El problema (20 s), V1

| s | text |
| --- | --- |
| 0 | Un problema del Cangur, una placa de quatre gigues i cap connexió a internet. |
| 5 | El copilot no resol els problemes per l'alumne: l'ensenya a raonar amb pistes, dins la placa. |
| 13 | Vam mesurar si el model podia raonar. No pot. A l'examen, el model escriu un programa; a l'aula, M3Kang fa de professor. |
| 20 | *(V1 aixeca la placa; V2 comença)* |

### 2. La demo (90 s), V2 parla, V3 clica, V1 sosté la placa

| s | V2 diu | V3 fa |
| --- | --- | --- |
| 0 | La placa: un Arduino UNO Q, sense Wi-Fi. El portàtil només mostra la seva pàgina pel cable USB. | res; la pantalla d'inici és al projector amb "Mariona1" i "6è de primària" ja escrits |
| 9 | L'alumna es diu Mariona i fa sisè. Mireu la placa: respira, perquè és nova. Comencem. | clic **Comença**; V1 ensenya el rombe que puja i baixa de brillantor |
| 13 | Primer problema, de taulers i patrons. La Mariona dubta i demana una pista: els quatre blocs de la placa són tres pistes i una lliçó. | clic **Pista**; V1 ensenya els quatre blocs de les dues files de baix; en arribar la pista, un s'apaga |
| 21 | Pista u: la placa busca, amb embeddings, un problema semblant del mateix tema, un nivell més fàcil, amb figura. Cap resposta, cap model que raoni. | assenyala la targeta "Un problema semblant" |
| 34 | Pista dos: una estratègia del tema. Ara sí: respon. | clic **Pista**; després clic al valor correcte (notes locals; els botons mostren el valor, no la lletra; la tecla de la lletra també val) |
| 40 | La placa mostra la lletra i el tick; la fulla es torna verda, i la barra de taulers s'omple dos segments de cinc: encerta amb pistes. | V1 gira la placa cap al jurat: lletra gran 0,8 s, tick, i al cap de 3 s el mapa de domini amb la fila de taulers creixent; V3 assenyala la barra de progrés de dalt |
| 47 | Continuem: el diagnòstic puja dos cursos, a raonament espacial. Pista u, el problema germà amb la seva imatge; pista dos, l'estratègia "gira i volteja". | clic **Continua** (o Enter); clic **Pista** a la fulla d'accions de baix; clic **Pista** |
| 60 | Avui s'equivoca. Les pistes no li han dit la resposta; la correcció arriba ara. Creu a la placa, un segment a espacial. Després del diagnòstic, aquest tema li arribarà més fàcil. | clic a un valor equivocat (notes locals); V1 mostra la creu; la fulla es tenyeix de vermell; V3 assenyala la barra de dalt |
| 75 | I el professor ho veu tot: progrés per tema i alumne, i els segons reals de cada pas a la placa. | clic **Vista del professor** (pestanya 2); abans, assenyala la taula "Temps (per al professor)" |
| 84 | *(V3 torna a la pestanya 1 i parla)* | |

### 3. Els números (40 s), V3

| s | text | font |
| --- | --- | --- |
| 0 | Dues meitats. Raonament: el model petit no raona en text; sol, a M3Kang, encerta vint-i-un coma set per cent, l'atzar. La regla del valor central arribava a vint-i-quatre coma nou. | results-A §1 (n = 281); history only: M3Kang middle value, v2 options, val 70/281 = 24.9%, board 140/562 |
| 13 | Per a l'examen li fem escriure un programa Python curt, que la placa executa en un intèrpret restringit: exacte quan encerta. A la placa, vuit de vint, contra cinc del raonament breu; vint-i-nou segons de mitjana, mai més de seixanta. | reason-experiments "The exam setting on the board": 8/20 vs 5/20 on the same 20 rows (small sample), mean 29.1 s, worst 49.4 s, 9.7 min; laptop 38/100 on the 100 practice rows, any fixed letter 20/100, M3Kang policy 16/100, brief reasoning alone 27/100 on the board (33 s) |
| 30 | Ensenyament: les pistes no gasten model, un embedding triga zero coma dotze segons, i cada temps que heu vist és real, de la placa. | results-A §10; the page's "Temps (per al professor)" table |
| 40 | *(V4 parla)* | |

> **Pendent, a decidir:** la mesura "abans i després" amb persones no està feta. El protocol
> (`docs/teach-measurement.md`: 3 persones, 5 problemes sense pistes i 5 amb l'escala, n = 15
> respostes per condició) triga 30 minuts a la placa. Si es fa, afegiu al final del bloc: «Amb tres
> persones i quinze respostes per condició, l'encert va passar de X a Y: n petit, i som els
> autors.» (12 words, 5 s.) Si no es fa, no digueu cap xifra d'aprenentatge.

### 4. Les lliçons (30 s), V4

| s | text |
| --- | --- |
| 0 | La lliçó és un resultat negatiu, i el publiquem: la lletra del model no porta informació. Que un model de zero coma vuit no raoni és, a la placa, una virtut: respon en mil·lisegons i no s'inventa cap pista. |
| 16 | Els solucionadors per plantilla disparen quatre cops en nou-cents onze problemes: el Cangur no és de plantilles. Qui raona és l'alumne, amb l'escala i la lliçó; M3Kang corregeix. Després: mesurar amb alumnes. Gràcies. |

---

## English

| block | English words | at 2.4 w/s | budget |
| --- | ---: | ---: | ---: |
| problem | 49 | 20 s | 20 s |
| demo (narration; the clicks and the LED fill the rest) | 195 | 81 s | 90 s |
| numbers (the placeholder counted as 12 words) | 99 | 41 s | 40 s |
| lessons | 75 | 31 s | 30 s |
| **total** | **418** | **174 s** | **180 s** |

### 1. The problem (20 s), V1

| s | text |
| --- | --- |
| 0 | A Kangaroo problem, a four-gigabyte board and no internet connection. |
| 5 | The copilot does not solve problems for the student: it teaches them to reason with hints, on the board. |
| 13 | We measured whether the model could reason. It cannot. In the exam, it writes a program; in class, M3Kang is the teacher. |
| 20 | *(V1 lifts the board; V2 starts)* |

### 2. The demo (90 s), V2 speaks, V3 clicks, V1 holds the board

| s | V2 says | V3 does |
| --- | --- | --- |
| 0 | The board: an Arduino UNO Q, no Wi-Fi. The laptop only shows its page over USB. | nothing; the start screen is on the projector with "Mariona1" and "6è de primària" already typed |
| 9 | The student is Mariona, sixth grade. Look at the board: it breathes, because she is new. Let's begin. | click **Comença**; V1 shows the diamond fading in and out |
| 13 | First problem, boards and patterns. Mariona hesitates and asks for a hint: the four blocks on the board are three hints and a lesson. | click **Pista**; V1 shows the four blocks on the two bottom rows; when the hint arrives, one goes dim |
| 21 | Hint one: the board searches, with embeddings, a similar problem of the same topic, one level easier, with its figure. No answer, no model reasoning. | point at the "Un problema semblant" card |
| 34 | Hint two: a strategy for the topic. Now she answers. | click **Pista**; then click the correct value (local notes; the buttons show the value, not the letter; the letter key also works) |
| 40 | The board shows the letter and the tick; the sheet turns green, and the boards bar fills two segments of five: correct with hints. | V1 turns the board to the jury: big letter 0.8 s, tick, and 3 s later the mastery map with the boards row growing; V3 points at the progress bar at the top |
| 47 | We continue: the diagnostic climbs two grades, to spatial reasoning. Hint one, the sister problem with its picture; hint two, the strategy "rotate and flip". | click **Continua** (or Enter); click **Pista** on the bottom action sheet; click **Pista** |
| 60 | Today she gets it wrong. The hints never told her the answer; the correction comes now. A cross on the board, one segment on spatial. After the diagnostic, this topic will come easier. | click a wrong value (local notes); V1 shows the cross; the sheet turns red; V3 points at the bar at the top |
| 75 | And the teacher sees everything: progress by topic and student, and the real seconds of every step on the board. | click **Vista del professor** (tab 2); before that, point at the "Temps (per al professor)" table |
| 84 | *(V3 returns to tab 1 and speaks)* | |

### 3. The numbers (40 s), V3

| s | text | source |
| --- | --- | --- |
| 0 | Two halves. Reasoning: the small model does not reason in text; alone, on M3Kang, it gets twenty-one point seven percent, chance. The middle-value rule reached twenty-four point nine. | results-A §1 (n = 281); history only: M3Kang middle value, v2 options, val 70/281 = 24.9%, board 140/562 |
| 13 | For the exam we make it write a short Python program, and the board runs it in a restricted interpreter: exact when it is right. On the board, eight of twenty, against five for brief reasoning; twenty-nine seconds on average, never over sixty. | reason-experiments "The exam setting on the board": 8/20 vs 5/20 on the same 20 rows (small sample), mean 29.1 s, worst 49.4 s, 9.7 min; laptop 38/100 on the 100 practice rows, any fixed letter 20/100, M3Kang policy 16/100, brief reasoning alone 27/100 on the board (33 s) |
| 30 | Teaching: the hints spend no model time, one embedding takes zero point one two seconds, and every time you saw is real, from the board. | results-A §10; the page's "Temps (per al professor)" table |
| 40 | *(V4 speaks)* | |

> **Pending, to decide:** the "before and after" measurement with people is not done (protocol
> in `docs/teach-measurement.md`, n = 15 answers per condition, 30 minutes on the board). If it
> is done, add at 35 s: "With three people and fifteen answers per condition, accuracy went
> from X to Y: a small n, and we are the authors." If not, say no learning figure at all.

### 4. The lessons (30 s), V4

| s | text |
| --- | --- |
| 0 | The lesson is a negative result, and we publish it: the model's letter carries no information. That a zero point eight model does not reason is, on the board, a virtue: it answers in milliseconds and invents no hint. |
| 16 | Template solvers fire four times in nine hundred and eleven problems: Kangaroo is not templates. The one who reasons is the student, with the ladder and the lesson; M3Kang corrects. Next: measure with students. Thank you. |

---

## Rehearsal notes

- **What the LED matrix shows** (main c40257f, measured on the board), so V1 knows when to turn
  it to the jury: start screen with a new student, a central diamond breathing every 2.4 s;
  problem loaded, four blocks on the two bottom rows (the four hint uses) and the mastery bars
  dimmed above; a hint arrives, one block goes dim (3, 2, 1, 0 left); while the model writes a
  hint, a dot runs along the bottom row (never in the Catalan demo: no model hint); an answer,
  the chosen letter large for 0.8 s, then the tick or the cross; 3 s later the mastery map, one
  row per topic, 0 to 13 LEDs, the current topic's row growing. V1 holds the board still during
  the letter and the tick, and tilts it to the jury for the map.

- The page (Duolingo-style redesign, no modal windows): **Pista** and **Solució** sit in a fixed
  action sheet at the bottom that turns green or red with the verdict; the next problem is
  **Continua** (Enter works too); the manipulative opens under the hints, the picture enlarges in
  place, and `Canvia d'alumne` (in the side menu: the three-bar icon fixed at the top left opens a
  floating sidebar that hides when the cursor leaves it, or with Escape) confirms in line with a
  second press. The answer buttons show only the option's value, centred, no letter: the click
  script says the value (in `docs/demo/local/demo-notes.md`), and the keys A to E still answer.
  `Solució` scrolls to its card and leaves only `Continua`; a small underlined footer under the
  options opens the original scan. The progress bar of the
  current topic (its name and five segments, one per mastery point) is always at the top of the
  page: at 40 s it shows two segments (mastery 2, correct with hints), at 60 s one segment
  (mastery 1). No click is needed to show it.
- The hint button shows one dot per use left. The script never says how many there are: if a
  sentence needs the number, say "tres pistes i una lliçó" / "three hints and a lesson" and check
  `HINT_MAX_USES` in `config.env` that morning (the fourth use is a lesson).

- The clicks are instant (under 0.5 s measured on the board, no model time), so the
  narration sets the pace. The demo block has about 9 s of slack for the clicks and the LED; the whole script is about 174 s spoken.
- The tick or cross stays 3 s on the LED, then the progress map returns. V1 turns the board
  towards the jury the moment V3 clicks an answer.
- After two answers the diagnostic is still running (it needs three): Mariona1's third problem
  is level 5, areas. Do not promise what the page does not show; the script says "once the
  diagnostic ends".
- If a hint has not appeared after 10 s, V2 keeps talking and V3 follows `contingency.md`.
- Jury criteria covered, in order: original use of M3Kang (labels as teacher, neighbours as
  hints: demo 21 s), guiding without the answer (demo 21-60 s), board offline (demo 0 s),
  measured before and after (numbers block, pending with people), under 60 s per step and 4 GB
  (numbers 18-28 s), demonstrable in 3 minutes.
