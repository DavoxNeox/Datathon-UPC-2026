# The 3-minute pitch: script, word by word

Structure suggested by the organisers: problem (20 s), live demo (90 s), numbers (40 s),
lessons (30 s). Catalan first (the jury is local), English below. Every number in the
"numbers" block comes from `docs/results-A.md` or `docs/error-analysis.md` with its n. Time
stamps are cumulative inside each block and assume **2.4 words per second** (12 words every
5 s, a calm pace); the word counts below are of the spoken text only.

| block | Catalan words | at 2.4 w/s | budget |
| --- | ---: | ---: | ---: |
| problem | 47 | 20 s | 20 s |
| demo (narration; the clicks and the LED fill the rest) | 182 | 76 s | 90 s |
| numbers | 96 | 40 s | 40 s |
| lessons | 72 | 30 s | 30 s |
| **total** | **397** | **165 s** | **180 s** |

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
| 13 | Vam mesurar si el model podia raonar. No pot. L'usem per ensenyar, i M3Kang fa de professor. |
| 20 | *(V1 aixeca la placa; V2 comença)* |

### 2. La demo (90 s), V2 parla, V3 clica, V1 sosté la placa

| s | V2 diu | V3 fa |
| --- | --- | --- |
| 0 | Això és la placa, un Arduino UNO Q, sense Wi-Fi. El portàtil només mostra la pàgina que serveix pel cable USB. | res; la pantalla d'inici és al projector amb "Mariona1" i "6è de primària" ja escrits |
| 9 | L'alumna es diu Mariona i fa sisè. Comencem. | clic **Comença** |
| 13 | Primer problema, de taulers i patrons. La Mariona no ho veu clar i, en lloc d'arriscar, demana una pista. | clic **Pista** |
| 21 | Pista u: el copilot busca dins la placa, amb embeddings, un problema semblant del mateix tema, un nivell més fàcil, amb la seva figura. Cap resposta, cap model que raoni. | assenyala la targeta "Un problema semblant" |
| 34 | Pista dos: una estratègia del tema. Ara sí: respon. | clic **Pista**; després clic **C** |
| 40 | Tick a la matriu LED, la fulla d'accions es tenyeix de verd, i el progrés de taulers puja: encerta amb pistes. | V1 gira la placa cap al jurat; V3 assenyala l'indicador de progrés del tema (si la pàgina el té sota les lletres; si no, obre **Més** i el tanca) |
| 47 | Continuem: el diagnòstic puja dos cursos. Raonament espacial. Pista u, el problema germà amb la seva imatge; pista dos, l'estratègia "gira i volteja". | clic **Continua** (o Enter); clic **Pista** a la fulla d'accions de baix; clic **Pista** |
| 60 | Avui la Mariona s'equivoca. Les pistes no li han dit la resposta; la correcció arriba només ara. Creu a la LED. Quan acabi el diagnòstic, aquest tema li arribarà un nivell més fàcil. | clic **A**; V1 mostra la creu; la fulla es tenyeix de vermell; V3 assenyala el progrés d'espacial a 1 (o obre **Més** i el tanca) |
| 75 | I el professor ho veu tot: progrés per tema i alumne, encerts per nivell. Cada pas ha trigat menys d'un segon dins la placa. | clic **Vista del professor** (pestanya 2) |
| 84 | *(V3 torna a la pestanya 1 i parla)* | |

### 3. Els números (40 s), V3

| s | text | font |
| --- | --- | --- |
| 0 | Vam mesurar abans de construir. El model va encertar seixanta-un de dos-cents vuitanta-un problemes: vint-i-un coma set per cent; sempre D, vint-i-tres coma u. | results-A §1, error-analysis (n = 281) |
| 10 | Com més segur, menys encertava: setze coma nou per cent al quart més confiat. | results-A §2 |
| 16 | La cursa oficial a la placa, cinc-cents seixanta-dos problemes: vint-i-sis coma set per cent; sempre D en dóna vint-i-tres coma u. La diferència és una regla sobre com es construeixen els distractors, no raonament, i mai entra a les pistes. | results-A §10, middle-value run (n = 562; bootstrap of the gain on val: -2 to +26 problems) |
| 33 | Les pistes no gasten model: un embedding triga zero coma dotze segons; la placa arrenca en dos minuts. | results-A §10 |
| 41 | *(V4 parla)* | |

> **Pendent, a decidir:** la mesura "abans i després" amb persones no està feta. El protocol
> (`docs/teach-measurement.md`: 3 persones, 5 problemes sense pistes i 5 amb l'escala, n = 15
> respostes per condició) triga 30 minuts a la placa. Si es fa, afegiu al final del bloc: «Amb tres
> persones i quinze respostes per condició, l'encert va passar de X a Y: n petit, i som els
> autors.» (12 words, 5 s.) Si no es fa, no digueu cap xifra d'aprenentatge.

### 4. Les lliçons (30 s), V4

| s | text |
| --- | --- |
| 0 | La lliçó principal és un resultat negatiu, i el publiquem: la lletra del model no porta informació. Tria la D un trenta-vuit per cent de les vegades. |
| 12 | Els solucionadors per plantilla tampoc: quatre famílies sobre nou-cents onze problemes en disparen quatre. El Cangur no és un dataset de plantilles. |
| 21 | Per això el model mai raona: M3Kang corregeix, tria el següent problema i guia sense donar la resposta. Després, mesurar amb alumnes. Gràcies. |

---

## English

| block | English words | at 2.4 w/s | budget |
| --- | ---: | ---: | ---: |
| problem | 48 | 20 s | 20 s |
| demo (narration; the clicks and the LED fill the rest) | 179 | 75 s | 90 s |
| numbers | 98 | 41 s | 40 s |
| lessons | 74 | 31 s | 30 s |
| **total** | **399** | **166 s** | **180 s** |

### 1. The problem (20 s), V1

| s | text |
| --- | --- |
| 0 | A Kangaroo problem, a four-gigabyte board and no internet connection. |
| 5 | The copilot does not solve problems for the student: it teaches them to reason with hints, on the board. |
| 13 | We measured whether the model could reason. It cannot. We use it to teach, and M3Kang is the teacher. |
| 20 | *(V1 lifts the board; V2 starts)* |

### 2. The demo (90 s), V2 speaks, V3 clicks, V1 holds the board

| s | V2 says | V3 does |
| --- | --- | --- |
| 0 | This is the board, an Arduino UNO Q, no Wi-Fi. The laptop only shows the page it serves over USB. | nothing; the start screen is on the projector with "Mariona1" and "6è de primària" already typed |
| 9 | The student is Mariona, sixth grade. Let's begin. | click **Comença** |
| 13 | First problem, boards and patterns. Mariona is not sure and, instead of guessing, asks for a hint. | click **Pista** |
| 21 | Hint one: the copilot searches on the board, with embeddings, for a similar problem of the same topic, one level easier, with its figure. No answer, no model reasoning. | point at the "Un problema semblant" card |
| 34 | Hint two: a strategy for the topic. Now she answers. | click **Pista**; then click **C** |
| 40 | A tick on the LED matrix, the action sheet turns green, and the progress of boards goes up: correct with hints. | V1 turns the board to the jury; V3 points at the topic progress indicator (under the letters if the page has it; otherwise opens **Més** and closes it) |
| 47 | We continue: the diagnostic climbs two grades. Spatial reasoning. Hint one, the sister problem with its picture; hint two, the strategy "rotate and flip". | click **Continua** (or Enter); click **Pista** on the bottom action sheet; click **Pista** |
| 60 | Today Mariona gets it wrong. The hints never told her the answer; the correction comes only now. A cross on the LED. Once the diagnostic ends, this topic will come one level easier. | click **A**; V1 shows the cross; the sheet turns red; V3 points at spatial progress at 1 (or opens **Més** and closes it) |
| 75 | And the teacher sees everything: progress by topic and student, hits by level. Every step took under a second on the board. | click **Vista del professor** (tab 2) |
| 84 | *(V3 returns to tab 1 and speaks)* | |

### 3. The numbers (40 s), V3

| s | text | source |
| --- | --- | --- |
| 0 | We measured before building. The model got sixty-one of two hundred and eighty-one problems right: twenty-one point seven percent; always D, twenty-three point one. | results-A §1, error-analysis (n = 281) |
| 10 | The more confident, the less right: sixteen point nine percent in its most confident quarter. | results-A §2 |
| 16 | The official run on the board, five hundred and sixty-two problems: twenty-six point seven percent; always D gives twenty-three point one. The difference is a rule about how distractors are built, not reasoning, and it never enters the hints. | results-A §10, middle-value run (n = 562; bootstrap of the gain on val: -2 to +26 problems) |
| 32 | The hints spend no model time: one embedding takes zero point one two seconds; the board boots in two minutes. | results-A §10 |
| 40 | *(V4 speaks)* | |

> **Pending, to decide:** the "before and after" measurement with people is not done (protocol
> in `docs/teach-measurement.md`, n = 15 answers per condition, 30 minutes on the board). If it
> is done, add at 35 s: "With three people and fifteen answers per condition, accuracy went
> from X to Y: a small n, and we are the authors." If not, say no learning figure at all.

### 4. The lessons (30 s), V4

| s | text |
| --- | --- |
| 0 | The main lesson is a negative result, and we publish it: the model's letter carries no information. It picks D thirty-eight percent of the time. |
| 12 | Template solvers do not help either: four families over nine hundred and eleven problems fire on four. Kangaroo is not a dataset of templates. |
| 21 | That is why the model never reasons: M3Kang corrects, picks the next problem and guides without giving the answer. Next: measure with students. Thank you. |

---

## Rehearsal notes

- The page (Duolingo-style redesign, no modal windows): **Pista** and **Solució** sit in a fixed
  action sheet at the bottom that turns green or red with the verdict; the next problem is
  **Continua** (Enter works too); the manipulative opens under the hints, the picture enlarges in
  place, and `Canvia d'alumne` confirms in line with a second press. Check on the integrated page
  whether the topic progress is visible under the letters or behind **Més**, and rehearse the
  40 s and 60 s gestures accordingly.
- The hint button shows one dot per use left. The script never says how many there are: if a
  sentence needs the number, say "tres pistes i una lliçó" / "three hints and a lesson" and check
  `HINT_MAX_USES` in `config.env` that morning (the fourth use is a lesson).

- The clicks are instant (under 0.5 s measured on the board, no model time), so the
  narration sets the pace. The demo block has about 14 s of slack for the clicks and the LED; the whole script is about 166 s spoken.
- The tick or cross stays 3 s on the LED, then the progress map returns. V1 turns the board
  towards the jury the moment V3 clicks the letter.
- After two answers the diagnostic is still running (it needs three): Mariona1's third problem
  is level 5, areas. Do not promise what the page does not show; the script says "once the
  diagnostic ends".
- If a hint has not appeared after 10 s, V2 keeps talking and V3 follows `contingency.md`.
- Jury criteria covered, in order: original use of M3Kang (labels as teacher, neighbours as
  hints: demo 21 s), guiding without the answer (demo 21-60 s), board offline (demo 0 s),
  measured before and after (numbers block, pending with people), under 60 s per step and 4 GB
  (numbers 18-28 s), demonstrable in 3 minutes.
