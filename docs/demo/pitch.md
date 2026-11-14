# The 3-minute pitch: script, word by word

Structure suggested by the organisers: problem (20 s), live demo (90 s), numbers (40 s),
lessons (30 s). Catalan first (the jury is local), English below. Every number in the
"numbers" block comes from `docs/results-A.md` or `docs/error-analysis.md` with its n; the
rehearsal timings are in `docs/demo/demo-problems.md`. Time stamps are cumulative inside each
block; a sentence of about 12 words takes 5 s spoken calmly.

Four voices. The team decides who is who (see the report); the roles are:

| voice | block | also |
| --- | --- | --- |
| **V1** | problem (20 s) | holds the board up during the demo |
| **V2** | narrates the demo (90 s) | |
| **V3** | numbers (40 s) | drives the laptop during the demo (the clicks, no talking) |
| **V4** | lessons (30 s) | timekeeper: shows V2 a hand signal at 60 s and 80 s of the demo |

The click script that V3 follows is in `docs/demo/demo-problems.md` (chain "Mariona1 / 6è de
primària"). The pseudonym and course are typed before the pitch starts, with the start screen
on the projector; the first click of the demo is "Comença".

---

## Català

### 1. El problema (20 s), V1

| s | text |
| --- | --- |
| 0 | Un problema del Cangur, una placa de quatre gigues de memòria i cap connexió a internet. |
| 6 | El nostre copilot no resol els problemes per l'alumne: l'ensenya a raonar amb pistes, i tot passa dins la placa. |
| 13 | Primer vam mesurar si el model podia raonar. No pot. Així que el fem servir per ensenyar, i el dataset M3Kang fa de professor. |
| 20 | *(V1 aixeca la placa; V2 comença)* |

### 2. La demo (90 s), V2 parla, V3 clica, V1 sosté la placa

| s | V2 diu | V3 fa |
| --- | --- | --- |
| 0 | Això és la placa, un Arduino UNO Q. Sense Wi-Fi. El portàtil només mostra la pàgina que la placa serveix pel cable USB. | res; la pantalla d'inici és al projector amb "Mariona1" i "6è de primària" ja escrits |
| 9 | L'alumna es diu Mariona i fa sisè de primària. Comencem. | clic **Comença** |
| 14 | Primer problema: una graella de quaranta caselles. Tema: taulers i patrons. La Mariona no ho veu clar i, en lloc d'arriscar, demana una pista. | clic **Pista** |
| 24 | Pista u: el copilot busca dins la placa, amb embeddings, un problema semblant del mateix tema i un nivell més fàcil, i l'ensenya amb la seva figura: la mateixa idea amb vint-i-vuit caselles. Cap resposta, cap model que raoni. | assenyala la targeta "Pista 1" |
| 38 | Pista dos: una fitxa d'estratègia del tema. Ara sí: files més columnes menys la intersecció. Quinze, la C. | clic **Pista**; després clic **C** |
| 48 | Tick a la matriu LED. I el domini de taulers puja: encerta amb pistes. | V1 gira la placa cap al jurat |
| 55 | Següent problema. El diagnòstic puja dos cursos: un full plegat dues vegades i tallat. Pista u: el problema germà, un nivell per sota, amb la seva imatge. Pista dos: l'estratègia "gira i volteja". | clic **Següent problema**; clic **Pista**; clic **Pista** |
| 70 | Avui la Mariona s'equivoca: diu A. Creu a la LED, i la pàgina li diu quina era. El domini d'espacial queda a u, i el proper problema d'aquest tema li arribarà un nivell més fàcil. | clic **A**; V1 mostra la creu |
| 81 | I el professor ho veu tot: domini per tema i alumne, i encerts per nivell. Cada pas ha trigat menys d'un segon dins la placa. | clic **Vista del professor** (pestanya 2) |
| 90 | *(V3 torna a la pestanya 1; V2 calla; V3 parla)* | |

### 3. Els números (40 s), V3

| s | text | font |
| --- | --- | --- |
| 0 | Abans de construir res, vam mesurar. El model de zero coma vuit mil milions va encertar seixanta-un de dos-cents vuitanta-un problemes de validació en anglès: vint-i-un coma set per cent. Respondre sempre D en dóna vint-i-tres coma u. | results-A §1, error-analysis (n = 281) |
| 12 | I com més segur estava el model, menys encertava: setze coma nou per cent al quart més confiat. | results-A §2 (quartils de 281) |
| 18 | La cursa oficial a la placa, els cinc-cents seixanta-dos problemes en català i anglès: cent trenta encerts, vint-i-tres coma u per cent, exactament sempre D. Zero coma trenta-vuit segons de mitjana, el pitjor quaranta, cap per sobre de seixanta. | results-A §10 (n = 562) |
| 30 | Les pistes que heu vist no gasten model: un embedding a la placa triga zero coma dotze segons. Amb els dos servidors, el relay i l'app en marxa queden dos coma sis gigues lliures, i la placa arrenca en fred en dos minuts. | results-A §10 |
| 40 | *(V4 parla)* | |

> **Pendent, a decidir:** la mesura "abans i després" amb persones no està feta. El protocol
> (`docs/teach-measurement.md`: 3 persones, 5 problemes sense pistes i 5 amb l'escala, n = 15
> respostes per condició) triga 30 minuts a la placa. Si es fa, substituïu la frase dels 30 s
> per: «Amb tres persones i quinze respostes per condició, l'encert va passar de X a Y amb
> l'escala de pistes: n petit, i som els autors.» Si no es fa, no digueu cap xifra d'aprenentatge.

### 4. Les lliçons (30 s), V4

| s | text |
| --- | --- |
| 0 | La lliçó principal és un resultat negatiu, i el publiquem. La lletra d'un model de zero coma vuit mil milions no porta informació: tria la D un trenta-vuit per cent de les vegades i la C un tres. |
| 10 | Els solucionadors per plantilla tampoc serveixen: quatre famílies sobre nou-cents onze problemes d'entrenament en disparen quatre. El Cangur no és un dataset de plantilles. |
| 18 | Per això el nostre model mai raona: corregeix amb les etiquetes de M3Kang, tria el problema següent al nivell de l'alumne i guia sense donar la resposta. |
| 25 | Després: mesurar amb alumnes reals abans i després, i obrir la pista del model només quan la seva qualitat jutjada passi del setanta per cent. Gràcies. |

---

## English

### 1. The problem (20 s), V1

| s | text |
| --- | --- |
| 0 | A Kangaroo problem, a board with four gigabytes of memory and no internet connection. |
| 6 | Our copilot does not solve problems for the student: it teaches them to reason with hints, and everything happens on the board. |
| 13 | First we measured whether the model could reason. It cannot. So we use it to teach, and the M3Kang dataset is the teacher. |
| 20 | *(V1 lifts the board; V2 starts)* |

### 2. The demo (90 s), V2 speaks, V3 clicks, V1 holds the board

| s | V2 says | V3 does |
| --- | --- | --- |
| 0 | This is the board, an Arduino UNO Q. No Wi-Fi. The laptop only shows the page the board serves over the USB cable. | nothing; the start screen is on the projector with "Mariona1" and "6è de primària" already typed |
| 9 | The student is Mariona, sixth grade. Let's begin. | click **Comença** |
| 14 | First problem: a grid of forty cells. Topic: boards and patterns. Mariona is not sure and, instead of guessing, asks for a hint. | click **Pista** |
| 24 | Hint one: the copilot searches on the board, with embeddings, for a similar problem of the same topic one level easier, and shows it with its figure: the same idea with twenty-eight cells. No answer, no model reasoning. | point at the "Pista 1" card |
| 38 | Hint two: a strategy card for the topic. Now she has it: rows plus columns minus the overlap. Fifteen, option C. | click **Pista**; then click **C** |
| 48 | A tick on the LED matrix. And the mastery of boards goes up: correct with hints. | V1 turns the board to the jury |
| 55 | Next problem. The diagnostic climbs two grades: a sheet folded twice and cut. Hint one: the sister problem, one level below, with its picture. Hint two: the strategy "rotate and flip". | click **Següent problema**; click **Pista**; click **Pista** |
| 70 | Today Mariona gets it wrong: she says A. A cross on the LED, and the page tells her which one it was. Spatial mastery stays at one, and her next problem on this topic will come one level easier. | click **A**; V1 shows the cross |
| 81 | And the teacher sees everything: mastery by topic and student, and hits by level. Every step took under a second on the board. | click **Vista del professor** (tab 2) |
| 90 | *(V3 returns to tab 1; V3 speaks)* | |

### 3. The numbers (40 s), V3

| s | text | source |
| --- | --- | --- |
| 0 | Before building anything, we measured. The zero point eight billion model got sixty-one of two hundred and eighty-one English validation problems right: twenty-one point seven percent. Always answering D gives twenty-three point one. | results-A §1, error-analysis (n = 281) |
| 12 | And the more confident the model was, the less it got right: sixteen point nine percent in its most confident quarter. | results-A §2 (quartiles of 281) |
| 18 | The official run on the board, all five hundred and sixty-two problems in Catalan and English: one hundred and thirty right, twenty-three point one percent, exactly always D. Zero point three eight seconds on average, the worst forty, none over sixty. | results-A §10 (n = 562) |
| 30 | The hints you saw spend no model time: one embedding on the board takes zero point one two seconds. With both servers, the relay and the app running, two point six gigabytes stay free, and the board cold-starts in two minutes. | results-A §10 |
| 40 | *(V4 speaks)* | |

> **Pending, to decide:** the "before and after" measurement with people is not done. The
> protocol (`docs/teach-measurement.md`: 3 people, 5 problems without hints and 5 with the
> ladder, n = 15 answers per condition) takes 30 minutes on the board. If it is done, replace
> the sentence at 30 s with: "With three people and fifteen answers per condition, accuracy
> went from X to Y with the hint ladder: a small n, and we are the authors." If not, say no
> learning figure at all.

### 4. The lessons (30 s), V4

| s | text |
| --- | --- |
| 0 | The main lesson is a negative result, and we publish it. The letter of a zero point eight billion model carries no information: it picks D thirty-eight percent of the time and C three percent. |
| 10 | Template solvers do not help either: four families over nine hundred and eleven training problems fire on four. Kangaroo is not a dataset of templates. |
| 18 | That is why our model never reasons: it corrects with the M3Kang labels, picks the next problem at the student's level and guides without giving the answer. |
| 25 | Next: measure with real students before and after, and open the model's hint only when its judged quality passes seventy percent. Thank you. |

---

## Rehearsal notes

- Speak the demo slower than it feels: the clicks are instant (under 0.2 s measured in sim,
  0.0 s of model time on the board), so the narration sets the pace, not the machine.
- The tick or cross stays 3 s on the LED, then the mastery map returns. V1 turns the board
  towards the jury the moment V3 clicks the letter.
- If a hint has not appeared after 10 s, V2 keeps talking and V3 follows `contingency.md`.
- Jury criteria covered, in order: original use of M3Kang (labels as teacher, neighbours as
  hints: demo 24 s), guiding without the answer (demo 24-48 s), board offline (demo 0 s, V1),
  measured before and after (numbers block, pending with people), under 60 s per step and 4 GB
  (numbers 18-30 s), demonstrable in 3 minutes (the whole thing).
