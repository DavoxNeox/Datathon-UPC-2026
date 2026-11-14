# The lineage of a problem

M3Kang spans 18 years (2007 to 2024) and 8 levels. The same mathematical idea comes back at
different levels in different years: the painted cube, the overlapping squares, the worst
case draw from a bag. `copilot/lineage.py` makes that visible: for a problem it returns its
chain by levels, the most similar training problem of the same topic at every other level,
ordered from the easiest to the hardest, with the similarity and the year. Nothing reasons:
the chain is a lookup in the embedding index, and the student is the one who compares the
rungs. It is an exploration ("look how this idea grows"), not a hint: the rungs are further
problems, shown unsolved and without their answers, and nothing in them helps to answer the
current one. `led_frame()` turns the chain into an 8x13 frame, one row per level, for the
matrix.

Measured with `python3 laptop/measure_lineage.py` on 14 Nov 2026 (laptop, shared servers,
index of 1466 English training vectors, 281 English validation problems). Problems are
referred to by id only.

## How it works

1. Query vector: the English vector of the problem. A training id reuses the vector stored
   in `data/index.db` (no model call); a validation id is embedded once through
   `retrieval.query_vector` and cached.
2. For every English row of the index with the same topic (`topics.get_topic`), excluding
   the problem itself, one dot product; the best score per level is kept.
3. Levels other than the problem's own whose best score reaches `min_similarity` form the
   chain; when more than `max_links` pass, the most similar stay; the result is sorted by
   level.

## Coverage on validation

Floor: a random same-topic training problem of another level scores 0.653 against a
validation problem (sd 0.074, n=281). The best per level scores 0.751 on average, so bge's
cosine scale is compressed: 0.6 is below the random floor and keeps almost everything.

| threshold | >= 3 links | mean links (of 7) | all 7 levels | mean similarity of kept links |
|---|---|---|---|---|
| 0.50 | 281/281 = 100.0% | 6.95 | 97.2% | 0.751 |
| 0.60 | 278/281 = 98.9% | 6.78 | 91.1% | 0.756 |
| 0.70 | 240/281 = 85.4% | 5.52 | 55.9% | 0.776 |
| 0.75 | 181/281 = 64.4% | 3.65 | 19.2% | 0.801 |
| 0.80 | 72/281 = 25.6% | 1.56 | 3.2% | 0.838 |
| 0.85 | 10/281 = 3.6% | 0.41 | 0.0% | 0.887 |

With `max_links=5`: mean 4.93 links at 0.60, 3.16 links at the default 0.75 (64.4% of the
problems keep at least 3 links).

Per topic (n = validation problems of the topic):

| topic | n | >= 3 links @0.60 | mean links @0.60 | >= 3 links @0.75 | mean links @0.75 | mean best similarity |
|---|---|---|---|---|---|---|
| arithmetic | 53 | 52/53 = 98.1% | 6.79 | 20/53 = 37.7% | 1.85 | 0.717 |
| logic | 13 | 11/13 = 84.6% | 4.92 | 3/13 = 23.1% | 1.00 | 0.661 |
| digits | 55 | 55/55 = 100.0% | 6.98 | 45/55 = 81.8% | 4.85 | 0.776 |
| counting | 10 | 10/10 = 100.0% | 6.40 | 3/10 = 30.0% | 1.80 | 0.704 |
| areas | 63 | 63/63 = 100.0% | 7.00 | 50/63 = 79.4% | 4.48 | 0.771 |
| angles | 6 | 6/6 = 100.0% | 5.00 | 4/6 = 66.7% | 3.00 | 0.765 |
| spatial | 61 | 61/61 = 100.0% | 7.00 | 45/61 = 73.8% | 4.25 | 0.767 |
| boards | 20 | 20/20 = 100.0% | 6.80 | 11/20 = 55.0% | 3.50 | 0.743 |

Per level of the query, the share with at least 3 links at 0.75 ranges from 53.8% (level 7,
n=39) to 75.0% (level 3, n=12); no level stands out. Chains are shorter for the two topics
with few index rows at the low levels (`angles` has none at levels 0 and 1, `logic` 2 and 1),
and for the word-problem topics whose texts share little vocabulary (arithmetic, logic).

A random sample of 100 training ids gives the same picture (72.0% with >= 3 links at 0.75,
mean 4.29 links), so validation problems are not penalised by being outside the index.

## Cost on the board

| query | embeddings | Python on the laptop (n) | board estimate |
|---|---|---|---|
| training id (stored vector) | 0 | 4.2 ms mean, 6.5 ms worst (100) | about 0.01 s |
| validation id | 1 x 0.12 s | 12.2 ms mean, 22.4 ms worst (281, the embedding request included) | 0.13 s |

`BOARD_EMBED_SECONDS=0.12` was measured on the board (config.env). The Python part is one dot
product per same-topic English row (33 to 398 rows), so it stays far below the embedding even
on the board's CPU. A chain never costs more than one embedding; a second call for the same
id costs none (`retrieval._QUERY_CACHE`).

## Hand judgement, round 1: 15 chains at 0.60 (calibration sample)

`measure_lineage.py --judge 15 --judge-threshold 0.6 --judge-seed 7` picks 15 validation
problems with at least 3 links at 0.60, two per topic in LED order (the fifteenth stops the second round, so
`boards` has one), and writes their texts outside the repository. Each link was read in its
English text, and the figure in `data/images/<id>_eng.png` for the problems that need it, and
judged "same idea" when the same mathematical idea or technique solves both, not merely the
same topic. Chain verdict: yes when at least half of its links are the same idea. 74 links in
all.

| # | query (level, topic) | idea of the query | links: level (year, similarity, same idea) | yes | chain |
|---|---|---|---|---|---|
| 1 | lvl-4_2012_8 (4, arithmetic) | linear system on unknown weights | 0 (2024, .72, y), 1 (2017, .71, n), 2 (2022, .71, n), 5 (2022, .73, y), 7 (2014, .73, y) | 3/5 | yes |
| 2 | lvl-2_2020_15 (2, logic) | degrees in a friendship graph | 4 (2014, .67, n), 5 (2009, .66, y), 6 (2014, .64, n), 7 (2017, .64, n) | 1/4 | no |
| 3 | lvl-5_2015_13 (5, digits) | signs or digits in a year cryptarithm | 2 (2019, .76, y), 3 (2021, .74, n), 4 (2008, .74, n), 6 (2007, .78, y), 7 (2013, .74, n) | 2/5 | no |
| 4 | lvl-0_2016_8 (0, counting) | worst case draws from a bag | 1 (2016, .86, y), 2 (2019, .76, y), 3 (2017, .79, y), 6 (2017, .80, y), 7 (2018, .88, y) | 5/5 | yes |
| 5 | lvl-2_2016_22 (2, areas) | identical rectangles tiling a square | 0 (2016, .87, y), 3 (2024, .83, y), 4 (2018, .87, y), 5 (2014, .85, y), 7 (2013, .83, y) | 5/5 | yes |
| 6 | lvl-6_2011_23 (6, angles) | angle chasing inside a triangle | 2 (2017, .71, n), 3 (2024, .73, n), 4 (2008, .77, y), 5 (2017, .79, y), 7 (2024, .80, n) | 2/5 | no |
| 7 | lvl-1_2015_16 (1, spatial) | overlaying rotated patterns | 2 (2021, .78, n), 4 (2022, .81, y), 5 (2007, .80, n), 6 (2013, .79, n), 7 (2009, .80, n) | 1/5 | no |
| 8 | lvl-6_2010_3 (6, boards) | equal row sums in a number table | 0 (2022, .75, y), 2 (2018, .76, n), 3 (2018, .77, n), 5 (2007, .73, n), 7 (2008, .74, y) | 2/5 | no |
| 9 | lvl-5_2019_5 (5, arithmetic) | circumferences of concentric circles | 0 (2020, .66, n), 2 (2017, .65, n), 4 (2009, .66, n), 6 (2010, .64, n), 7 (2012, .65, n) | 0/5 | no |
| 10 | lvl-1_2018_18 (1, logic) | counting backwards with a regrowth rule | 2 (2020, .68, n), 3 (2020, .67, n), 4 (2011, .62, n), 6 (2014, .68, n), 7 (2015, .63, n) | 0/5 | no |
| 11 | lvl-6_2009_1 (6, digits) | a divisibility test on the options | 1 (2015, .80, n), 3 (2023, .83, y), 4 (2009, .91, y), 5 (2015, .89, y), 7 (2013, .89, n) | 3/5 | yes |
| 12 | lvl-4_2017_11 (4, counting) | zigzag of equilateral triangles on a base line | 1 (2016, .69, n), 2 (2020, .70, n), 5 (2016, .76, n), 6 (2013, .72, n), 7 (2016, .74, n) | 0/5 | no |
| 13 | lvl-1_2016_11 (1, areas) | area of overlapping squares or rectangles | 2 (2024, .79, y), 3 (2024, .77, y), 4 (2007, .79, y), 5 (2014, .78, n), 6 (2007, .78, n) | 3/5 | yes |
| 14 | lvl-3_2016_30 (3, angles) | nested equilateral triangles, parallel sides | 2 (2017, .66, n), 4 (2007, .75, n), 5 (2020, .82, y), 6 (2020, .80, y), 7 (2024, .74, n) | 2/5 | no |
| 15 | lvl-4_2015_30 (4, spatial) | painted faces of a cube cut into small cubes | 1 (2018, .86, y), 2 (2021, .89, y), 3 (2021, .89, y), 5 (2020, .88, y), 6 (2014, .84, n) | 4/5 | yes |

Totals: 33/74 links are the same idea (44.6%); 6/15 chains pass (40%) at 0.6, the
signature's first default.

Precision of a link by similarity (the same 74 links):

| similarity | links | same idea |
|---|---|---|
| 0.60 to 0.70 | 17 | 1/17 = 6% |
| 0.70 to 0.75 | 17 | 5/17 = 29% |
| 0.75 to 0.80 | 20 | 11/20 = 55% |
| 0.80 to 0.85 | 8 | 5/8 = 62% |
| 0.85 and above | 12 | 11/12 = 92% |

| threshold | links kept | precision | recall of the 33 good links |
|---|---|---|---|
| 0.60 | 74/74 | 45% | 100% |
| 0.70 | 57/74 | 56% | 97% |
| 0.75 | 40/74 | 68% | 82% |
| 0.80 | 20/74 | 80% | 48% |

So 0.6 shows a full staircase that is right less than half of the time, and on this sample
0.75 looked like the knee: two links in three the same idea, 82% of the good links kept, a
chain of 3 or more rungs for 64% of the problems instead of 99%. The default of `lineage()`
was set to 0.75 (`DEFAULT_MIN_SIMILARITY`). This threshold was chosen on the same 74 links
that were judged, so it had to be checked on a clean sample (next section).

## Hand judgement, round 2: 15 new chains at the fixed 0.75 (clean sample)

`measure_lineage.py --judge 15 --judge-threshold 0.75 --judge-seed 11 --judge-exclude <the
15 ids above>` picks 15 other validation problems, at random with that seed, among those
with at least 3 links at 0.75 (181 of 281), two per topic in LED order, `boards` one. Same
criterion and same judge, 65 links, texts and figures read as in round 1.

| # | query (level, topic) | idea of the query | links: level (year, similarity, same idea) | yes | chain |
|---|---|---|---|---|---|
| 1 | lvl-5_2017_11 (5, arithmetic) | fractions of a crowd by group | 0 (2019, .80, n), 1 (2022, .80, n), 4 (2016, .84, n), 6 (2017, .79, y), 7 (2019, .80, n) | 1/5 | no |
| 2 | lvl-5_2022_23 (5, logic) | 3-1-0 tournament points, totals | 1 (2022, .85, y), 3 (2020, .85, y), 4 (2011, .80, n), 6 (2022, .87, y), 7 (2014, .87, y) | 4/5 | yes |
| 3 | lvl-6_2014_28 (6, digits) | middle element of an ordered list of digit-restricted numbers | 0 (2017, .77, n), 2 (2017, .78, n), 4 (2023, .80, n), 5 (2019, .77, n), 7 (2022, .80, y) | 1/5 | no |
| 4 | lvl-7_2017_3 (7, counting) | minimum cut in a graph | 1 (2017, .77, n), 4 (2016, .76, n), 5 (2019, .76, n), 6 (2018, .78, n) | 0/4 | no |
| 5 | lvl-6_2008_14 (6, areas) | chord symmetry of a circle cutting a rectangle | 1 (2021, .76, n), 3 (2021, .76, n), 4 (2015, .77, n), 5 (2017, .78, n), 7 (2022, .81, y) | 1/5 | no |
| 6 | lvl-5_2008_28 (5, angles) | lines forming a set of angles | 3 (2023, .76, n), 4 (2017, .78, n), 6 (2015, .75, n), 7 (2015, .78, n) | 0/4 | no |
| 7 | lvl-2_2020_7 (2, spatial) | counting pieces after cutting sheets | 0 (2018, .87, y), 1 (2016, .76, n), 3 (2019, .82, y), 4 (2019, .77, n), 6 (2013, .80, n) | 2/5 | no |
| 8 | lvl-4_2011_20 (4, boards) | tiling a square with a pentomino | 0 (2016, .83, n), 1 (2024, .78, n), 3 (2024, .76, n), 5 (2024, .78, n), 6 (2011, .75, n) | 0/5 | no |
| 9 | lvl-5_2021_18 (5, arithmetic) | divisibility of a total after removing one part | 1 (2015, .75, n), 2 (2022, .78, n), 3 (2021, .81, n) | 0/3 | no |
| 10 | lvl-4_2024_22 (4, logic) | deduce the leftover card from arithmetic clues | 2 (2021, .77, n), 5 (2015, .76, n), 6 (2014, .78, n) | 0/3 | no |
| 11 | lvl-7_2015_26 (7, digits) | numbers as sums of distinct powers of 2 | 0 (2022, .81, n), 3 (2022, .82, n), 4 (2020, .83, n), 5 (2007, .85, n), 6 (2015, .87, y) | 1/5 | no |
| 12 | lvl-3_2017_30 (3, counting) | colourings under an adjacency constraint | 4 (2024, .76, n), 5 (2010, .81, y), 6 (2017, .76, n), 7 (2016, .82, y) | 2/4 | yes |
| 13 | lvl-2_2024_19 (2, areas) | area of a region from the areas around it | 0 (2020, .77, n), 6 (2015, .81, n), 7 (2008, .78, n) | 0/3 | no |
| 14 | lvl-4_2022_28 (4, angles) | angle chasing in isosceles triangles | 3 (2024, .75, y), 5 (2009, .83, n), 6 (2008, .88, y), 7 (2024, .78, n) | 2/4 | yes |
| 15 | lvl-4_2015_7 (4, spatial) | overlapping strips, total length | 0 (2019, .79, n), 2 (2019, .78, n), 3 (2019, .79, n), 6 (2013, .78, n), 7 (2024, .78, n) | 0/5 | no |

Totals of the clean sample: 14/65 links are the same idea (21.5%); 3/15 chains pass (20%).

Precision by similarity, both rounds, links at 0.75 or above only:

| similarity | round 1 (calibration) | round 2 (clean) | both |
|---|---|---|---|
| 0.75 to 0.80 | 11/20 = 55% | 3/41 = 7% | 14/61 = 23% |
| 0.80 to 0.85 | 5/8 = 62% | 4/16 = 25% | 9/24 = 38% |
| 0.85 and above | 11/12 = 92% | 7/8 = 88% | 18/20 = 90% |
| all at 0.75+ | 27/40 = 68% | 14/65 = 22% | 41/105 = 39% |

The clean sample does not confirm 0.75: round 1 was a lucky draw whose strong lineages (the
bag, the painted cube, the rectangles) filled the 0.75 to 0.85 band with good links, and
round 2 shows that band at 7 to 25%. What holds in both rounds is the top band: at 0.85 or
above, 18 of 20 links are the same idea. Validation coverage at 0.85 is 3.6% of the problems
with 3 or more rungs (mean 0.41 rungs), so a threshold that is right nine times in ten shows
a staircase almost never. The default stays at 0.75 as agreed with the reviewer; the web
should show every rung's similarity (the bar of `led_frame`) and may mark rungs at 0.85 or
above as strong. Still one judge; 30 chains, 139 links in all.

Why the 0.75 to 0.85 band is weak: in round 2 the query's topic is wrong or too broad for 7
of the 15 chains (a count of pieces of paper and a strip-overlap problem under `spatial`, a
divisibility problem under `arithmetic`, a minimum cut under `counting`, a pentomino tiling
under `boards`), so the same-topic filter searches the wrong shelf, and bge rewards shared
nouns (football, chocolate, sheets, paper) over the mathematics.

What the round-1 judgement also showed:

- M3Kang gives the same problem at two adjacent levels in the same year (chains 8, 10 and
  15: levels 2 and 3 of 2018, 2020 and 2021; chain 14: levels 5 and 6 of 2020). The chain
  catches these as two rungs; the web could collapse rungs with similarity above 0.98 into one.
- Very high similarities on short stems ("Which of the following numbers is ...", chain 11)
  come from the phrasing, not from the mathematics; the idea still matches in 3 of 5.
- The topic filter decides more than the vector. Chains 9 and 12 fail because the query is
  mis-filed (a circle perimeter under `arithmetic`, a zigzag length under `counting`); the
  word-problem topics `arithmetic` and `logic` have the lowest similarities and the fewest
  good links, the figure topics `areas`, `spatial`, `digits` the most.

## Demo candidates

The three clearest chains (all from round 1, every link at 0.76 or above, so they are the
same at the default 0.75), in order:

1. `lvl-0_2016_8` (level 0, counting): the worst case draw from a bag, 5/5 links, from level 1
   (2016) to level 7 (2018), all text-only, similarities 0.76 to 0.88. A level-0 student sees
   the same idea climb to the last level.
2. `lvl-4_2015_30` (level 4, spatial): the painted cube, 4/5 links at levels 1, 2, 3, 5 (2018
   to 2021), with figures, similarities 0.86 to 0.89.
3. `lvl-2_2016_22` (level 2, areas): identical rectangles that tile a square, 5/5 links at
   levels 0, 3, 4, 5, 7 (2013 to 2024), with figures, similarities 0.83 to 0.87.

Reserve: `lvl-1_2016_11` (level 1, areas), overlapping squares, whose true lineage is level 4
in 2007, level 1 in 2016 and levels 2 and 3 in 2024; from round 2, `lvl-5_2022_23` (level 5,
logic), the 3-1-0 tournament points at levels 1, 3, 6 and 7 (2014 to 2022), 4/5, text-only.

All three are validation ids, so the first call costs one embedding (0.13 s on the board);
`data/val.jsonl` must be present for the text lookup, as it is for retrieval.

## Not done

- The web page and the LED call: `webapp.py` is untouched; the proposal is in INTERFACES.md.
- A second judge, and more than two chains per topic; a topic table with fewer mis-filed
  problems would lift the 0.75 to 0.85 band more than any change in this module.
- Nothing was run on the board; the cost is the measured embedding time plus the laptop's
  Python time.
