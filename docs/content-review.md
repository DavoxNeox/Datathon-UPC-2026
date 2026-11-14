# Content review: strategies, demo set, student-facing Catalan

Status: **draft by the content curator, nothing here is validated by a person yet.** Everything
the student reads must be natural school Catalan (no Spanish calques) with an English version.
Problems are always referred to by M3Kang id; statements and images are never copied.

Branch `team/content-curation-a0bddb`. Files touched: `data_curated/demo_set.json` (new),
`data_curated/strategies.json`, `tests/test_content.py` (new), this document. No code in
`copilot/` or `assets/` was edited: sections 3 and 4 are proposals for the controller or D.

## 1. `data_curated/demo_set.json` (18 problems, all `status: draft`)

Two groups. The **script problems** are the six ids of `docs/demo/demo-problems.md` (the two
chains played on stage and the reserve chain), listed in `demo_core` and `demo_reserve`; D's
rung 3 will read their steps one at a time (never the last one), so every step is written to
stand alone as a hint. The **alternates** (`alternates`) were chosen before the script was
published, with demo criteria (levels 0 to 3, every topic, readable options, half with a
figure); they stay as spare material for rung 3 and for a plan B.

Licence rule applied to every text: problems by id, figures in our words, and **no value of a
distractor option anywhere**; the correct value appears only in the last step (which is never
shown as a hint). `tests/test_content.py` enforces it (`test_option_values_stay_out_of_the_texts`)
together with the leak filter on every text before the last step.

| id | level | topic | figure | answer (checked) | role |
| --- | --- | --- | --- | --- | --- |
| lvl-1_2024_2 | 1 | boards | yes | C | script, chain B 1st: rows + columns − crossings on an 8×5 grid. |
| lvl-3_2019_18 | 3 | spatial | yes | E | script, chain B 2nd: two folds, two cuts, a 3×3 of pieces. |
| lvl-2_2020_4 | 2 | arithmetic | no | A | script, chain A 1st: batches, eggs, boxes; round up. |
| lvl-4_2010_12 | 4 | digits | no | E | script, chain A 2nd: undo divide/add/multiply backwards. |
| lvl-3_2021_20 | 3 | areas | yes | E | script, reserve 1st: eight grey triangles of half a cm². |
| lvl-5_2022_30 | 5 | counting | yes | B | script, reserve 2nd: three stacked rings have a forced order. |
| lvl-0_2016_8 | 0 | counting | no | C | alternate: worst case ("to be sure"). |
| lvl-0_2019_22 | 0 | arithmetic | no | D | alternate: two sentences, bar drawing. |
| lvl-0_2016_16 | 0 | areas | yes | A | alternate: cutting corners keeps the perimeter. |
| lvl-2_2016_2 | 2 | spatial | yes | D | alternate: two dice, hidden faces; `dice` manipulative. |
| lvl-0_2015_17 | 0 | digits | yes | D | alternate: cross of five squares, parity. |
| lvl-2_2023_12 | 2 | logic | no | B | alternate: two errors, one distance. |
| lvl-0_2016_6 | 0 | boards | no | D | alternate: fence-post pattern. |
| lvl-1_2016_8 | 1 | counting | yes | E | alternate: rectangles in four strips. |
| lvl-2_2017_21 | 2 | angles | no | D | alternate: clock hands at right angles. |
| lvl-0_2015_14 | 0 | spatial | yes | C | alternate: 27-cube chessboard. |
| lvl-3_2016_5 | 3 | arithmetic | no | B | alternate: doubling lilies. |
| lvl-1_2024_8 | 1 | areas | yes | D | alternate: two rectangles, three squares. |
| lvl-1_2022_13 | 1 | logic | no | D | alternate: impossible total of points. |

Every image was opened and every answer re-derived and compared with the label. Checks:
`python3 laptop/validate_demo_set.py data_curated/demo_set.json` (0 problems) and
`python3 -m unittest tests.test_content` (green).

Second checks asked by the reviewer (both entries stay `draft`, with a `review_note` field):

- lvl-2_2016_2: on the enlarged picture the right die shows **4 on top, 6 in front, 2 on the
  right** (a standard die after all; the first description said 3/6/3 and was wrong). Visible
  dots 1 + 2 + 4 + 6 + 2 = 15, hidden 42 − 15 = 27 = label D. Description and last step corrected.
- lvl-2_2017_21: the angle between the hands t minutes after 8:00 is |240 − 5.5·t| degrees; it
  is 90° or 270° at t = 27.3, 60, 92.7, 125.5, 158.2, 190.9 and 223.6, and the next (256.4) is
  after noon: seven times, label D. The last step no longer lists rounded clock times.

What the team must review: the Catalan of every step read aloud (the script problems first),
and whether a step shown alone as a rung-3 hint reads well without the previous ones.

## 2. `data_curated/strategies.json`: before / after

Method: every card was read against at least three real problems of its topic (ids below) and
had to be one actionable sentence of at most 15 Catalan words that gives no answer. Catalan
fixes: `tatxa` (accepted but a calque in school use) → `ratlla`; `al cap` → `mentalment`;
`la seva àrea` → `no en canvia l'àrea` (weak pronoun); `línia de nombres` → `recta numèrica` (the
school term); `no oblidis` → `sense oblidar`; number words removed where a strategy does not
need them (the leak filter reads `una`, `dues`, `set` as numbers).

Problems used per topic: arithmetic lvl-0_2019_22, lvl-2_2019_10, lvl-3_2016_5; logic
lvl-1_2022_13, lvl-2_2018_28, lvl-2_2023_12; digits lvl-0_2015_17, lvl-0_2023_1, lvl-2_2020_23;
counting lvl-0_2016_8, lvl-0_2016_19, lvl-1_2016_8, lvl-1_2017_11; areas lvl-0_2016_16,
lvl-1_2024_8, lvl-2_2018_6; angles lvl-2_2017_21, lvl-3_2018_24, lvl-3_2023_23; spatial
lvl-0_2015_14, lvl-1_2016_19, lvl-2_2016_2; boards lvl-0_2016_6, lvl-0_2020_9, lvl-1_2017_6.

| topic # | before (ca) | after (ca) | reason |
| --- | --- | --- | --- |
| arithmetic 2 | Fes el problema pas a pas: primer el total, després el que es treu o s'afegeix. | Ves pas a pas: primer el total, després el que es treu o s'afegeix. | 16 words → 14. |
| arithmetic 4 | Prova amb nombres petits per veure el patró i després aplica'l als nombres del problema. | Prova-ho amb nombres petits, troba el patró i aplica'l al problema. | 16 → 11; `prova-ho` with the pronoun. |
| arithmetic 5 | Dibuixa un esquema o una línia de nombres amb les quantitats. | Dibuixa un esquema o una recta numèrica amb les quantitats. | `recta numèrica` is the school term. |
| logic 1 | … i tatxa les que contradiuen alguna pista. | … i ratlla les que contradiuen alguna pista. | `ratllar` is the natural verb. |
| logic 2 | Comença per la pista que més limita: la que només permet una o dues opcions. | Comença per la pista que més limita: la que deixa menys opcions. | 15 → 12 and no number words (`una`, `dues` trip the leak filter). |
| digits 3 | Mira la darrera xifra: sovint decideix si un nombre és parell o múltiple de 5 o de 10. | Fixa't en la darrera xifra: diu si el nombre és parell o acaba en zero. | 18 → 15. Applies to lvl-2_2020_23 and the divisibility problems. |
| digits 4 | Per saber si un nombre és divisible per 3 o per 9, suma les seves xifres. | Per saber si un nombre és divisible per tres o per nou, suma'n les xifres. | `suma'n` (weak pronoun) instead of `les seves`. |
| digits 5 | Per trobar el nombre més gran o més petit possible, omple les xifres d'esquerra a dreta. | Per al nombre més gran o més petit possible, omple les xifres d'esquerra a dreta. | 16 → 15. |
| counting 1 | Organitza els casos per no repetir-ne cap ni oblidar-ne cap: per exemple, per la primera lletra o la primera xifra. | Ordena els casos per la primera lletra o xifra: no en repetiràs ni n'oblidaràs cap. | 22 → 15; same idea (lvl-0_2016_19, lvl-1_2017_11). |
| counting 2 (paths) | En una quadrícula, cada casella rep la suma dels camins que arriben de dalt i de l'esquerra. | Cada casella val la suma de la casella de dalt i la de l'esquerra. | 19 → 13; `manipulative: paths` kept. |
| counting 5 | Fes un arbre amb les possibilitats i compta les fulles. | Si demana "estar-ne segurs", pensa en el pitjor cas: la sort va en contra. | **substitute.** The tree card duplicated card 1; a third of the low-level counting problems are worst-case questions (lvl-0_2016_8, lvl-0_2022_20, lvl-1_2016_7, lvl-2_2019_17) and no card covered them. |
| areas 2 | Compara peces iguals: si dues peces són congruents, tenen la mateixa àrea. | Marca cada tros del contorn: el perímetre és la suma de tots els trossos. | **substitute.** `congruent` is not level-0 vocabulary and card 5 already says it; perimeter questions are frequent in this topic (lvl-0_2016_16, lvl-2_2018_6, lvl-1_2023_16) and had no card. |
| areas 3 | Per saber quina fracció del total és la part ombrejada, compta quadradets iguals. | Per saber quina fracció és la part ombrejada, compta quadradets iguals. | shorter, same meaning. |
| areas 5 | Moure una peça sense estirar-la no canvia la seva àrea. | Moure una peça sense estirar-la no en canvia l'àrea. | weak pronoun `en`. |
| angles 4 | Marca a la figura tots els angles que coneixes abans de buscar el que et demanen. | Marca a la figura tots els angles que saps abans de buscar el que demanen. | 16 → 15. |
| angles 5 | En un polígon regular tots els angles són iguals: divideix el total. | Al rellotge, l'agulla gran gira 6° per minut i la petita, mig grau. | **substitute.** Regular polygons do not appear in levels 0–3 of this topic; clock-hand questions do (lvl-2_2017_21, and the level 4–5 clock problems). Keep the old card if the team prefers it for levels 6–7. |
| spatial 1 | Gira la figura al cap o sobre el paper… | Gira la figura mentalment o sobre el paper… | `al cap` is a calque of "en la cabeza". |
| spatial 3 | En un dau, les cares oposades sumen 7 i no es poden veure alhora. | En un dau, les cares oposades sumen 7 i mai no es veuen alhora. | more natural; `dice` manipulative kept. |
| spatial 4 | Compta els cubs per capes o per files, i no oblidis els amagats. | Compta els cubs per capes o per files, sense oblidar els amagats. | one clause instead of two. |

Unchanged and confirmed useful: arithmetic 1 and 3, logic 3 to 5, digits 1 and 2, counting 3
and 4, areas 1 and 4, angles 1 to 3, spatial 2 and 5, boards 1 to 5. The English of the changed
cards was aligned; the `_comment` now states the 15-word rule.

## 3. Student-facing strings: proposals (not applied)

Priority **demo** marks what the jury sees in the first three minutes.

| file:line | current | proposed | reason | priority |
| --- | --- | --- | --- | --- |
| assets/index.html:13, assets/app.js:16 | Reinicia l'alumne | Canvia d'alumne | "Reinicia" reads as resetting the person; the action is to start over with another student. | demo |
| assets/index.html:23, app.js:8 | Àlies | Nom o àlies | Younger students do not know "àlies"; they will type their name anyway. | demo |
| assets/index.html:27, app.js:15 | Si no tries curs, el copilot el descobreix amb tres o quatre problemes. | Si no tries cap curs, el copilot l'endevina amb tres o quatre problemes. | `cap curs`, and `endevinar` is the natural verb here. | demo |
| assets/app.js:16 | Deixa que el copilot ho descobreixi | Que ho endevini el copilot | shorter in the dropdown, same verb as above. | demo |
| assets/app.js:13 | placa (est.) | placa (estimat) | abbreviations in a table header read as English "est." | low |
| assets/app.js:13 | càrrega de la pàgina | temps de càrrega | it is a time, not a load. | low |
| assets/app.js:14 | Ja has respost. Pots veure la solució. | Ja has respost. Si vols, mira la solució. | friendlier, invites rather than permits. | demo |
| assets/app.js:10 | Pensant… | Un moment… | "Pensant" implies the model reasons; the design says it does not. | demo |
| assets/app.js:10–11 | Pista 1 · problema semblant / Estratègia / Pas de la solució / Pista del model | Pista 1 · un problema semblant / Pista 2 · una estratègia / Pista 3 · un pas de la solució / Pista 3 · del model | the ladder shows which rung the student is on; the label already prints `esglaó N`, so alternatively drop "Pista 1" from the first and keep the rest. | demo |
| assets/app.js:116 | esglaó | graó | both are correct; `graó` is the everyday word and shorter next to the number. | low |
| assets/app.js:17 | Vols esborrar l'historial d'aquest alumne i tornar a l'inici? | Vols esborrar el progrés d'aquest alumne i tornar a l'inici? | "historial" sounds medical or browser-like; "progrés" is what is erased. | low |
| assets/app.js:18 | mostra'l sencer / mostra'n menys | mostra-ho tot / mostra'n menys | the object is the text, neuter `ho`. | low |
| assets/app.js:19 | 5è de primària … 2n de batxillerat | unchanged | correct forms (5è, 6è, 1r, 2n, 3r, 4t). Check the mapping level 0 = 5è with B: Cangur in Catalonia starts at 5è, consistent. | – |
| assets/app.js:127–129 | Xifres / Comptatge / Espacial / Taulers | Nombres / Comptar / Espai / Taulers | one-word labels under the mastery bars; "Xifres" alone is odd and "Espacial" is an adjective. Optional. | low |
| copilot/webapp.py:78 | Tria una resposta, o demana una pista. | Tria una resposta o demana una pista. | no comma before `o`. | demo |
| copilot/webapp.py:173 | Correcte! | Molt bé, correcte! | warmer on the big moment of the demo. | demo |
| copilot/webapp.py:175 | No és això. La resposta era {label}. | No és aquesta. La resposta correcta era la {label}. | `això` points at a thing; the student picked an option (feminine). With the error signatures (section 4) this line is followed by the diagnosis. | demo |
| copilot/webapp.py:175 (en) | Not this time. The answer was {label}. | Not quite. The correct answer was {label}. | aligned with the Catalan. | low |
| copilot/webapp.py:198 | Pensant una pista… | Preparant una pista… | one does not "think a hint"; also avoids claiming reasoning. | demo |
| copilot/webapp.py:218 | No he pogut preparar la pista. | Ara no puc preparar cap pista. Torna-ho a provar. | tells the student what to do. | low |
| copilot/hints.py:184 | No tinc cap problema semblant més fàcil. Prova una estratègia. | No tinc cap problema semblant més fàcil. Prova-ho amb una estratègia. | `provar` wants an object here. | low |
| copilot/hints.py:191,194 | Un problema semblant, més fàcil (nivell N). Com el resoldries? | Un problema semblant i més fàcil (nivell N). Com el resoldries? | comma splice; the same-level variant is fine. | demo |
| copilot/hints.py:203, 277 | Escriu les dades del problema i què et demanen. | Escriu les dades del problema i encercla què et demanen. | same wording as strategy card arithmetic 1. | low |
| copilot/hints.py:260 | Solució: opció D (27). | Solució: opció D (27). | fine; the full stop after the parenthesis is correct. | – |
| copilot/solvers/average.py:76 | Resolent, k = … | Si ho resols, k = … | `Resolent` as an absolute gerund is a calque. | low |
| copilot/solvers/ages.py:55 | Comprova que tothom ja havia nascut! | unchanged | good, keep the humour. | – |
| assets/manip/dice.html:42 | Gira'l amb les fletxes i mira quines cares es veuen alhora. | unchanged | correct. | – |
| assets/manip/rotate.html:62 | No: aquesta és un mirall o una altra rotació. | No: aquesta és una reflexió (un mirall) o una altra rotació. | `mirall` alone is informal; name the concept once. | low |
| assets/teacher.html:42 | 2 encerta amb pistes / 3 de vegades sense pistes / 4 sempre sense pistes | 2 encerta amb pistes / 3 a vegades sense pistes / 4 sempre sense pistes | `a vegades` is the usual form in schools; both accepted. | low |

## 4. Error signatures (`copilot/signatures.py`, branch `team/innov-error-signatures`)

The Catalan is good: direct, school register, no calques, and the texts dodge `un`/`una`/`dues`
for the leak filter. Proposals:

| line | current (ca) | proposed | reason |
| --- | --- | --- | --- |
| 61 | El teu resultat no s'assembla al correcte per cap relliscada típica: torna a llegir l'enunciat i planteja el problema des del principi. | No és cap de les relliscades habituals: torna a llegir l'enunciat i planteja el problema des del principi. | shorter; "no s'assembla al correcte" tells the student there is a correct value nearby, which is noise. |
| 127 | La teva resposta surt escrita a l'enunciat, no és el resultat: encara falta fer-hi alguna operació. | Aquest nombre ja surt a l'enunciat: és una dada, no el resultat. Encara hi falta alguna operació. | two sentences; `dada` names the trap (Kangaroo plants a datum). |
| 136 | Has intercanviat les xifres: tens les xifres bones però desordenades. Torna a escriure el nombre amb calma. | Has intercanviat les xifres: són les bones, però desordenades. Torna a escriure el nombre amb calma. | avoids repeating `xifres`. |
| 161 | …o t'has menjat xifres… | …o t'has deixat xifres… | `menjar-se xifres` is colloquial; `deixar-se` is the classroom phrase. |
| 170 | Has comptat cada cas per duplicat: el teu resultat és el doble del que toca. Pensa quins casos són en realitat el mateix. | Has comptat cada cas dues vegades: et surt el doble. Pensa quins casos són en realitat el mateix. | **careful:** `dues` is read as 2 by the leak filter, so only if the answer is not 2 (the code already drops a leaking text and falls through). Otherwise keep `per duplicat`. |
| 177 | T'has deixat la meitat: el teu resultat és la meitat del que toca. Hi ha casos que no has comptat. | T'has deixat la meitat: hi ha casos que no has comptat. | the middle clause repeats the first. |
| 186, 191 | Et sobra el primer o el darrer / Et falta el primer o el darrer: revisa els extrems del recompte. | Has comptat un de més / un de menys: revisa el primer i el darrer. | — but `un` is read as 1 by the filter; keep the current wording when the answer may be 1 (the author's note on line 38 explains this). Current is acceptable. |
| 200, 207 | …torna a mirar què fas amb el {x} de l'enunciat, potser l'havies de sumar / restar. | …torna a mirar què fas amb el {x} de l'enunciat: potser calia sumar-lo / restar-lo. | colon instead of the comma splice; `calia` instead of the conditional past. |

English texts: fine; "You counted one too many: check the end points, one of them does not
belong." (line 187) could be "You counted one too many: check the first and the last." to
match the Catalan.

## 5. Follow-ups for the owners (not done here)

- `copilot/leak_filter.py` reads the OCR value `27cm2` as the numbers 27 **and 2**, so any
  Catalan text with `dos`/`dues` is rejected for lvl-1_2024_8 and every option written
  `Ncm2`/`Nm2`. The unit regex should strip `cm2`, `m2`, `cm3` before extracting numbers
  (`tests/test_content.py` strips them itself before calling the filter).
- `laptop/validate_demo_set.py` only checks digits; `tests/test_content.py` runs the leak
  filter (number words included) on every text before the last step and is the stricter gate.
- `data_curated/demo_set.json` has no reader in `copilot/` yet: the ladder could use its steps
  as rung 3 for these ids (text, never the last step) and its `figure_ca` as the description the
  model lacks.
