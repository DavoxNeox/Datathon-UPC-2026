# Data, licence and reproducibility: what the public repository leaks, what it cannot reproduce, and how to fix both

Reviewed from the worktree at `5cc2ded` (= the `origin/main` named in the brief) after a `git fetch`; `origin/main`
is now `8501c23` (11 more commits: the content-curation and demo-pitch merges), and every command below ran over
**all** remote refs, so the new files are covered. The repository `DavoxNeox/Datathon-UPC-2026` is **already public**
(`gh repo view` → `visibility: PUBLIC`), so everything named here is published today, not "when we publish".

**Summary (5 lines)**
1. No M3Kang problem is reconstructible from the repository or its history: no `.jsonl`/`.db`/image was ever added except the five invented `data/sample_problems.jsonl`; the only verbatim fragments are one 52-character first sentence plus its five options and label (`data/README.md:11`, copied from the organizers' `README.md:769`) and an 87-character test fixture that is a 65% near-copy of a real statement (`tests/test_solvers.py:89`).
2. `docs/content-review.md:21-33` (on `origin/main` since `8501c23`) is a **label-by-id table**: the correct letter of all 13 demo problems, 13/13 equal to the dataset label. Nothing else in any branch maps ids to labels.
3. Reviewer C1 is half wrong: the 8 `Co-Authored-By` trailers on `origin/main` are the **organizers'** commits inherited from `upstream/main` (author `mpous`, 11-13 Nov); rewriting them is not ours to do. The team's own 13 trailers sit on three stale branches (`origin/data`, `origin/hints-app`, `origin/trainer`) that are public and should be deleted; `hint_quality.json:40` still names the tool.
4. `prepare_m3kang.py` is deterministic (sha256 split; verified 281 val ids, 0 overlap, 16.1%) but pins nothing: no dataset revision (the cached snapshot is `e772e61`, equal to the current HF sha), `>=` in `requirements.txt`, and the OCR package `rapidocr_onnxruntime` requires Python `<3.13`, so the documented install fails on the board (3.13) and on this laptop (3.14). Measured here: 38 min for 3,494 rows with OCR, 36 s for the index.
5. The licence story is right in `docs/README-final-draft.md:284-292` (MIT code, research-only data, ids only) but the root `README.md` is still the organizers' guide, the draft has 19 `[[TODO]]`s including a stale `[[TODO add LICENSE]]` (LICENSE exists since `86f162c`), and no doc tells the jury how to obtain the data, which revision, with which Python, or that `results/` is git-ignored (reviewer I11).

## What I ran

All from the worktree; nothing was modified except this file. "READ" = conclusions from reading, "RAN" = verified by running.

| Command (abridged) | Outcome |
| --- | --- |
| `git branch -r` | 16 remote branches on `origin`, plus `upstream/main` (organizers' repo `mpous/datathon-UPC-maths-qualcomm-arduino-unoq`). RAN |
| `git log --all --format='%an <%ae>' \| sort \| uniq -c` | `101 N. Betancort <lizard@Ns-MacBook-Pro.local>`, `8 mpous <marc.pous@gmail.com>`, `6 Marc Pous <marc.pous@gmail.com>`. RAN |
| `git log --all --format='%H %s%n%b' \| grep -i claude` | 8 `Co-Authored-By: Claude Opus 5.5` (all upstream/mpous), 13 `Co-Authored-By: Claude Fable 5.1` (team, only on `origin/data`, `origin/hints-app`, `origin/trainer`, none reachable from `origin/main`), 1 upstream subject `f2c7248 Add steps 13-15 and Claude skills...`. RAN |
| `git log origin/main --format='%h %an' --grep='Co-Authored-By: Claude'` | 8 commits, all author `mpous`, all present in `upstream/main` (`git log upstream/main --grep=... \| wc -l` → 8). RAN |
| `git grep -n -i claude -- . ':!.claude' ':!.skills'` | `README.md:1104-1124` (organizers' section, byte-identical to upstream: `git diff upstream/main origin/main -- README.md .skills` is empty), `.gitignore:18`, `data_curated/hint_quality.json:40`. RAN |
| `git rev-list --all \| xargs -I{} git ls-tree -r {} --name-only \| sort -u \| grep -Ei 'jsonl\|\.db$\|\.png\|\.jpe?g\|\.csv\|^data/\|parquet\|zip'` | Only `data/README.md` and `data/sample_problems.jsonl`, ever. RAN |
| `git count-objects -vH`; largest blobs | 2.84 MiB loose + 97 KiB pack; largest blob 56 KB (`README.md`), then 49 KB (`data_curated/topics.json`). No big files. RAN |
| Leak scan (`scratchpad/leak_scan.py`, `leak_runs.py`): every 28-char window of every `text` in `~/m3kang-data/{train,val}.jsonl` (3,494 rows, 626,193 windows) and every option string ≥ 12 chars against **every text blob in every ref** (495 objects), then the longest common run per hit with `difflib` keyed by (id, language) | Real quotes: `data/README.md` and `README.md` (52 chars of `lvl-0_2015_13/eng`, prefix `13. f`, options and label identical to the dataset), `tests/test_solvers.py:89` (54 of 129 chars of `lvl-3_2021_5/eng`, prefix `how m`, ratio 0.65). Generic phrases only (≤ 37 chars, "which of the following"-type): `copilot/solvers/digit_count.py:1` (33), `assets/manip/dice.html` (35), `docs/lineage.md` (34, branch), `docs/reviews/...` (37, branch), `data_curated/demo_set.json` (29, Catalan), `LICENSE` (30, boilerplate). `docs/error-analysis*.md`, `docs/results-A.md`, `strategies.json`, `families.json`, `topics*.json`: no hit. RAN |
| Label tables: regex `id … [A-E]` over all blobs, then compared to dataset labels | `docs/content-review.md` (origin/main): 13 rows, 13/13 equal to the label (column "answer (checked)"). `docs/error-signatures.md` (branch): 20 rows, 0/20 equal (column is the *wrong* option chosen, fine). `demo_set.json`: 13 problems, no answer/label field, last step holds the answer in prose by design. RAN |
| `python3 -I` id check of `data/sample_problems.jsonl` | `sample-1..5` ids absent from train and val; texts absent (sample-5 shares a 39-char generic Catalan opener with `lvl-4_2016_21/cat`, ratio 0.56: invented, fine). File authored by the organizers (`f58d355`). RAN |
| `python3 laptop/prepare_m3kang.py --help`, `python3 laptop/validate_demo_set.py --help` | Both print help on Python 3.14 (argparse only at import). The validator's copy check is `statement[:60] in field` (`validate_demo_set.py:71`): catches a copied prefix only. RAN |
| Split stability: recompute `int(sha256(id),16) % 1000 < 150` for every id | 281 val ids all < 150, 1,466 train ids all ≥ 150, overlap 0, val share 16.1% of ids (nominal 15%). `hashlib`, not `hash()`: stable across Python versions. RAN |
| Dataset revision: `ls ~/.cache/huggingface/hub/datasets--qualcomm--M3Kang/snapshots/`; `curl https://huggingface.co/api/datasets/qualcomm/M3Kang` | Cached snapshot `e772e611d45679cf48f1c92618b2963a40d1d584` = current HF `sha`; `gated: false`, `lastModified 2026-02-13`, tag `license:other`, 18 files. `prepare_m3kang.py:62` calls `hf_hub_download` with no `revision`. RAN |
| Timing: `stat -f '%SB %Sm'` on the HF blob, `.ocr_cache.jsonl`, `train.jsonl`, `index.db` | Parquet shard 0 downloaded 12:57-12:59 (393 MB); OCR cache born 12:57:52, last written 13:36:03 → **38 min** for 3,494 rows (eng+cat) with RapidOCR on this Mac; `index.db` 13:36:26 → 13:37:02 = **36 s** on the laptop. RAN |
| `curl https://pypi.org/pypi/rapidocr_onnxruntime/json` / `rapidocr` / `pyarrow` | `rapidocr_onnxruntime 1.4.4 requires_python <3.13,>=3.6`; `rapidocr 3.10.0 requires_python >=3.8,<4`; `pyarrow 26.0.1 >=3.11`. No interpreter on this Mac has `pyarrow` (3.14 and system 3.9 both fail), so `prepare_m3kang.py` could not be run end-to-end here. RAN |
| `python3 -m unittest discover tests` | 168 tests OK, 1 skipped, 0.9 s (baseline holds). RAN |
| `git check-ignore -v` on `data/.ocr_cache.jsonl results/hints_val.jsonl results/ablations.csv docs/runs/x.csv laptop/out.jsonl docs/x.jsonl` | first three ignored; `docs/runs/*.csv`, `laptop/*.jsonl`, `docs/*.jsonl` **not** ignored (only `data/*` and `results/*` are). RAN |
| Reviewer's findings C1, I10, I11, M10 in `origin/team/review-22fa88:docs/reviews/review-main-2026-11-14.md` | READ, and used below. |
| `laptop/prepare_m3kang.py`, `laptop/validate_demo_set.py`, `laptop/*.py` imports, `INTERFACES.md:25-38`, `data/README.md`, `data_curated/README.md`, `.gitignore`, `LICENSE`, `config.env`, `docs/README-final-draft.md` §3 and "Credits and licenses", `docs/project-hub-draft.md`, `docs/error-analysis*.md`, `docs/results-A.md` | READ |

Schema check (READ): `prepare_m3kang.py:193-197` writes exactly the `Problem` keys of `INTERFACES.md:26-34` (`id, language, level, year, text_only, text, options, label`); `topic` is the optional key added later. `options` is `{}` when OCR fails. Offline behaviour (READ): without internet `hf_hub_download` raises unless the shard is cached and `HF_HUB_OFFLINE=1` is set; `--parquet <file>` bypasses the hub entirely; RapidOCR ships its ONNX models inside the wheel, so OCR itself needs no network; the OCR cache `data/.ocr_cache.jsonl` is appended per row, so an interrupted run resumes. Imports in `laptop/*.py` are stdlib plus the three packages in `requirements.txt` plus `copilot.*`; nothing else.

## Proposals

### P1. Reviewer C1, corrected: the main-branch trailers are the organizers'; delete our three stale public branches and fix `hint_quality.json`
- **Where**: `git log origin/main --grep='Co-Authored-By'` (8 commits, author `mpous`, all in `upstream/main`); `origin/data`, `origin/hints-app`, `origin/trainer` (13 team commits with the trailer, e.g. `af10724`, `5e579d7`, `79c6897`, `f0641ae`); `data_curated/hint_quality.json:40`.
- **Problem / opportunity**: Reviewer C1 counts 8 trailers on `origin/main` and proposes `git filter-repo` on a fresh clone. Those 8 commits are not ours: `f58d355 … 2ede686` are the organizers' upstream commits (`git diff upstream/main origin/main -- README.md .skills` is empty; `upstream/main` has the same 8). Rewriting them breaks the shared ancestry with upstream and rewrites another author's history. The team's own violations are the 13 commits on three branches that were superseded by squashed merges but are still public, and the `judge` string. The repository is public now, so this is live.
- **Proposal**: (1) `git push origin --delete data hints-app trainer` (and the other dead team branches `data-phase11`, `hints-demo`, `trainer-demo`, `infra` once merged), by the controller, after `git log origin/main..origin/<branch>` shows nothing unmerged that is wanted; (2) edit `hint_quality.json:40` to `"judge": "D, draft of 2026-11-14; the team must redo it"`; (3) leave `origin/main` history alone and say so in a one-line note in the final README's credits ("the setup guide and its history are the organizers' work"); (4) the subject of upstream `f2c7248` mentions the tool as a feature of the organizers' kit, which is their choice.
- **Impact (jury or student)**: high. The rule exists because the repository is judged as the team's work; today a visitor who opens the branch list sees the trailers.
- **Effort**: S.
- **Risk**: deleting a remote branch loses nothing merged; check each with `git log origin/main..origin/<b> --oneline` first. Does not touch INTERFACES.md. Safe before the demo.
- **How to measure**: `git fetch --prune && git log --all --format='%b' | grep -ci 'co-authored-by: claude'` → 8 (all upstream); `git grep -i claude -- . ':!.claude' ':!.skills' ':!README.md' ':!.gitignore'` → empty.
- **Verified**: ran.

### P2. Remove the label-by-id table of the 13 demo problems from `docs/content-review.md`
- **Where**: `origin/main:docs/content-review.md:19-33` (table column "answer (checked)"), added in `179b96e` / merged in `8501c23`.
- **Problem / opportunity**: 13 rows `| id | level | topic | figure | answer (checked) | why |`; the letter equals the dataset label in 13/13 cases (checked against `val.jsonl`/`train.jsonl`, counts only). It is the only id→label mapping anywhere in the repository's history, it covers exactly the problems shown live, and the repository is public: a student (or a jury member) can look up the demo answers. The brief's rule is "refer to problems by id, never with the label" (rung 0 was built around it, `819ce58`). The reviewer did not see it (the file landed after `2dbfbf5`).
- **Proposal**: replace the column by `verified` = `yes`, keep the "why" prose (it does not state letters; two "why" cells mention which option is the trap, which is fine). If the team wants the letters for rehearsal, keep them in the git-ignored `results/` (e.g. `results/demo_answers.txt`) or in the trainer's own `data/students.db`. Add a unit test `tests/test_no_labels_in_docs.py`: for every tracked `*.md`/`*.json` outside `tests/`, fail on the regex `lvl-\d_\d{4}_\d+\s*\|[^\n|]*\|[^\n|]*\|[^\n|]*\|\s*[A-E]\s*\|` and on JSON objects with both `"id": "lvl-…"` and `"label"`.
- **Impact (jury or student)**: medium. It does not reconstruct the dataset, but "guide without revealing" is a jury criterion and this reveals the demo's answers in the public repo.
- **Effort**: S.
- **Risk**: none for the code; `laptop/validate_demo_set.py` does not read this file. Safe before the demo.
- **How to measure**: the new test passes; `git show origin/main:docs/content-review.md | grep -cE '\| [A-E] \|'` → 0.
- **Verified**: ran (table detection and 13/13 label match).

### P3. Replace the near-verbatim M3Kang statement in `tests/test_solvers.py:89` and the docstring example in `digit_count.py:1`; add a repository-wide text-leak test
- **Where**: `tests/test_solvers.py:89` (the `text` passed to `solvers.classify`, 87 chars, prefix `how m`; 54-char longest common run with `lvl-3_2021_5/eng`, 129 chars, `difflib` ratio 0.65); `copilot/solvers/digit_count.py:1` (33-char run with the same problem; its `_MATCH` regex at line 16 is generic and fine); `laptop/validate_demo_set.py:69-72`.
- **Problem / opportunity**: the fixture is the real statement with the numbers changed: two thirds of the sentence is verbatim. The repository is public; the licence is research-only. The current guard (`validate_demo_set.py:71`, `statement[:60] in field`) only looks at `demo_set.json` and only at a copied *prefix*, so it would miss this case and any paraphrase that drops the first word.
- **Proposal**: (1) rewrite line 89 as an invented sentence that still matches `_MATCH` (an invented question in the team's own words, about counting numbers with a given digit total) and rephrase the docstring at `digit_count.py:1` the same way; (2) add `tests/test_no_m3kang_text.py`, skipped when `data/val.jsonl`/`train.jsonl` are absent (same pattern as the retrieval tests): load every text of both files, normalise whitespace and case, build the set of 40-char windows, and scan every file in `git ls-files` (text only) for a window hit; print `path:line` and the problem id only. On this Mac the full scan over 495 blobs took under two minutes; over the working tree it is seconds. 40 chars gives no false positive among the hits above (the longest generic phrase was 37).
- **Impact (jury or student)**: medium. A jury member checking the licence paragraph would find the sentence in 10 seconds with a search; the test makes the "ids only" claim provable.
- **Effort**: M (S for the two edits, S for the test).
- **Risk**: the test must `skipTest` without data so the board's 125 tests and CI are unaffected; it must not print text. Does not touch INTERFACES.md. Safe before the demo.
- **How to measure**: `python3 -m unittest tests.test_no_m3kang_text` → OK with data linked; the scratchpad scan rerun shows no run ≥ 40 chars.
- **Verified**: ran (the scan); the test itself is a proposal.

### P4. Replace the real example problem in `data/README.md` (and note the one in the organizers' `README.md`)
- **Where**: `data/README.md:10-12` (example record of `lvl-0_2015_13`: first sentence, 52 chars, the five options and the label, all equal to the dataset); same text at `README.md:769` (organizers' file, byte-identical to upstream).
- **Problem / opportunity**: both files were written by the organizers (`f58d355`), and their own guide says at `README.md:1218` to check the licence before showing an example problem. The team republishes it. It is one sentence of 1,747, so the leak is cosmetic, but it is the only place where a label is next to its options and statement.
- **Proposal**: in `data/README.md` use `sample-1` from `data/sample_problems.jsonl` as the example (invented, same schema), or the `INTERFACES.md:26-37` shape with `"text": "..."`. When the draft README replaces the root `README.md` (P9), the second copy disappears; until then leave the organizers' file as is and mention it in the credits as theirs.
- **Impact (jury or student)**: low. Easy, and it removes the only options+label pairing in the tree.
- **Effort**: S.
- **Risk**: none. Safe before the demo.
- **How to measure**: rerun of the leak scan shows no hit on `data/README.md`.
- **Verified**: ran (options and label equality checked, counts only).

### P5. Pin the M3Kang revision in `prepare_m3kang.py` and record it in `data/README.md`
- **Where**: `laptop/prepare_m3kang.py:29-31` (`DATASET`, `SHARD`, `SHARDS = {"high_quality": 4, "standard": 10}`), `:62` (`hf_hub_download(DATASET, name, repo_type="dataset")`, no `revision`), `data/README.md`.
- **Problem / opportunity**: the models are pinned to the byte (`config.env:14,16,32,34`: revisions and SHA-256, and llama.cpp `2cbe0ec` in `config.env:7` matches `README-final-draft.md:71` and `project-hub-draft.md:32`), but the dataset is not. The shard file name encodes the shard count (`-of-00004`), so any re-upload of M3Kang changes the file names and the download fails, or silently changes the split's contents. The cached snapshot used for every figure in `docs/results-A.md` is `e772e611d45679cf48f1c92618b2963a40d1d584` (= the current HF `sha`, last modified 2026-02-13, not gated).
- **Proposal**: add `REVISION = "e772e611d45679cf48f1c92618b2963a40d1d584"` and `--revision` (default `REVISION`) to `parse_args`; pass `revision=args.revision` to `hf_hub_download`; print it in `report()`; write a `data/manifest.json` next to the outputs with `{dataset, revision, shards, languages, val_fraction, n_train, n_val, options_read, ocr_package, ocr_version, python}`. Since the manifest holds no text, copy it to `data_curated/dataset_manifest.json` and commit it, so a reader can verify they rebuilt the same 281-id validation set. Document `HF_HUB_OFFLINE=1` and `--parquet` for a laptop without internet. Mention in the README that the dataset is not gated (no token needed).
- **Impact (jury or student)**: medium. "Reproducible" is in the jury's reading of a public repo; today a reader cannot know which M3Kang the 23.1% was measured on.
- **Effort**: S.
- **Risk**: none for the board (laptop script). Safe before the demo.
- **How to measure**: `python3 laptop/prepare_m3kang.py --limit 20 --no-ocr --out /tmp/x` prints the revision; `data_curated/dataset_manifest.json` has `n_val_ids: 281`.
- **Verified**: ran (revision and gating lookup); the code change is read-only reasoning.

### P6. Make `laptop/requirements.txt` installable with a stated Python: pin versions and either require 3.11/3.12 or move to `rapidocr`
- **Where**: `laptop/requirements.txt:2-4` (`huggingface_hub>=0.24`, `pyarrow>=15`, `rapidocr_onnxruntime>=1.3`); `docs/README-final-draft.md:119` ("needs Python 3.12 or older for the OCR package"); `README.md:59` (organizers: "Python 3.10 or later"); `laptop/prepare_m3kang.py:149-150,181`.
- **Problem / opportunity**: `rapidocr_onnxruntime` 1.4.4 declares `requires_python <3.13`; `pyarrow` 26 declares `>=3.11`. The board runs 3.13, this laptop 3.14: `pip install -r laptop/requirements.txt` fails on both, and the organizers' "3.10 or later" is wrong at both ends (the only window is 3.11-3.12). Nothing is pinned, so a rerun in six months installs different OCR models and a different 62% options rate (`README.md:755`). The draft's sentence is correct but buried in a comment.
- **Proposal**: (a) minimum: pin `huggingface_hub==<installed>`, `pyarrow==<installed>`, `rapidocr_onnxruntime==1.4.4` and put `python_requires: 3.11-3.12` in a comment and in README §3.2 as a sentence, not a trailing comment; (b) better: switch to `rapidocr>=3` (supports 3.13), adapting `prepare_m3kang.py:149-150,181`: `from rapidocr import RapidOCR`, and the call returns an object with `.boxes`, `.txts`, `.scores` instead of a list of `(box, text, score)` tuples, so `parse_options(list(zip(out.boxes, out.txts, out.scores)))`. Then rebuild to a scratch `--out` and compare the options-read rate and the per-id options against the existing `.ocr_cache.jsonl` (same keys), and keep the old cache if the rate drops.
- **Impact (jury or student)**: medium. A jury member following §3.2 on a current Python stops at the first command.
- **Effort**: S for (a), M for (b) (38 min OCR rerun plus the comparison).
- **Risk**: (b) changes OCR output and could change `options` for some ids, which changes solver inputs and the baseline figures; do (b) only after the demo, (a) is safe now. No INTERFACES.md change.
- **How to measure**: `python3.12 -m venv v && v/bin/pip install -r laptop/requirements.txt` succeeds; for (b) the options-read count stays ≥ 62% of 3,494 and the set of ids with 5 options is reported.
- **Verified**: ran (PyPI metadata); the code change is read-only reasoning.

### P7. Defence in depth in `.gitignore`, and a home for the evidence CSVs (reviewer I11)
- **Where**: `.gitignore:1-8` (`data/*`, `results/*` only), `docs/README-final-draft.md:164` ("All runs are in `results/ablations.csv`"), `docs/error-analysis.md:7` (cites `eval-20261114-134204-A-baseline-eng281.csv`, not in the tree), `results/.gitkeep`.
- **Problem / opportunity**: `git check-ignore` shows `laptop/*.jsonl`, `docs/*.jsonl`, `docs/runs/*.csv` and any `*.png`/`*.parquet` outside `data/` are **not** ignored; one `--out docs` or a stray `--save-images` path commits text or images. Meanwhile the reviewer's I11 stands: the public repo holds no CSV for any figure. The CSVs hold ids, letters, times and logprobs (no text), so they can be committed.
- **Proposal**: add to `.gitignore`: `*.jsonl`, `!data/sample_problems.jsonl`, `*.parquet`, `*.png`, `*.jpg`, `.ocr_cache.jsonl`, `images/`; create `docs/runs/` and un-ignore it explicitly (`!docs/runs/*.csv`); copy there `eval-…-A-baseline-eng281.csv`, the Catalan 281 run, the board `predictions.csv` and `ablations.csv`, and point `README-final-draft.md:164`, `docs/error-analysis.md:7` and `docs/results-A.md:109` at them. Add to the P3 test a check that every `docs/runs/*.csv` has no column named `text`/`options`/`hint` and no cell longer than 40 characters.
- **Impact (jury or student)**: medium. The jury asks "measure before/after"; the numbers need their evidence in the public tree.
- **Effort**: S.
- **Risk**: committing a CSV with a free-text column would leak; the cell-length check prevents it. `results/hints_val.jsonl` (LLM hint text) stays ignored on purpose. Safe before the demo.
- **How to measure**: `git check-ignore laptop/out.jsonl docs/x.png` → ignored; `ls docs/runs/*.csv` lists the four files named in the docs.
- **Verified**: ran (`git check-ignore`); the rest is read-only.

### P8. Commit identity for a public repository
- **Where**: `git log --all --format='%an <%ae>'`: `101 N. Betancort <lizard@Ns-MacBook-Pro.local>`; the organizers appear twice (`mpous` / `Marc Pous`, same address).
- **Problem / opportunity**: the team's address is a machine-local hostname: GitHub links none of the 101 commits to a profile, and the hostname (a personal device name) is published. The name is consistent and fine. The two organizer identities are theirs.
- **Proposal**: in the main checkout and every worktree, `git config user.email "<github-id>@users.noreply.github.com"` (or the team's shared address) for commits from now on; do **not** rewrite history (the controller merges from several sessions; a rewrite would strand every open branch). Optionally add a `.mailmap` with one line mapping the local address to the noreply one, so `git shortlog` and GitHub's contributor view are consistent.
- **Impact (jury or student)**: low. Cosmetic, but a public repository with 101 unlinked commits looks like an import.
- **Effort**: S.
- **Risk**: none. Safe before the demo.
- **How to measure**: `git log -1 --format='%ae'` after the next commit shows the noreply address.
- **Verified**: ran.

### P9. Finish the licence and data paragraphs of the public README (builds on reviewer M10)
- **Where**: `README.md` (root, 1,260 lines, the organizers' guide, byte-identical to upstream), `docs/README-final-draft.md:1-8` (says it replaces the root README), `:101-130` (§3.1-3.2), `:282-292` ("Credits and licenses", `[[TODO add LICENSE]]` at `:292`), `LICENSE` (MIT, "The Math on the Edge team", added `86f162c`), `docs/project-hub-draft.md:24,35,104`.
- **Problem / opportunity**: the research-only statement is correct and well placed (`:284-286`: "no problem text, image or index is in this repository; only problem ids and our labels"), but (1) the TODO about the licence is stale, (2) no doc says how a reader obtains the data: that M3Kang is on Hugging Face, not gated, 393 MB for shard 0, prepared by `prepare_m3kang.py` in about 40 min with OCR (measured 38 min here) plus 36 s for the index on a laptop or a few minutes on the board (`README.md:1007`), at revision `e772e61`, with Python 3.11-3.12 on the laptop and 3.13 on the board (`README.md:260`), (3) `README-final-draft.md:111` still claims "all 125 tests pass" against 168 today, (4) 19 `[[TODO]]`s remain and the root README is not yet the team's, so a visitor today reads the organizers' guide with no mention of the project. Reviewer M10 covers the unverified citations; this is the data/licence half.
- **Proposal**: write §3.2 as: where the data comes from (link, revision, licence sentence, "not in this repository, not redistributed"), the exact three commands, the measured time, the Python constraint, and what `data_curated/` contains (link to its README, which is already precise). Replace `:292` with "Our code: MIT, see `LICENSE`". Update `:111` to the current count. Add one sentence that the organizers' setup guide moved to `docs/setup-guide.md` (keep it, it is their licence and credit) and swap the root README for the draft once the TODOs are closed.
- **Impact (jury or student)**: high. "Public repo with README" and "MIT licence" are two of the listed jury criteria; the licence handling of M3Kang is the one place a jury can disqualify.
- **Effort**: M (the data/licence section is S; closing the TODOs is the team's).
- **Risk**: none for the code. Safe before the demo; the root swap can wait until after.
- **How to measure**: `grep -c 'TODO' README.md` → 0 after the swap; the README states revision, Python versions and the time; the `LICENSE` TODO is gone.
- **Verified**: read only (timing and gating were run).

### P10. A reproducible-figures manifest: tie every number to a revision, a commit and a CSV
- **Where**: `docs/results-A.md` (figures), `laptop/prepare_m3kang.py:213-230` (`report()` prints and forgets), `eval.py` / `results/ablations.csv` (records the git commit per run, `README.md:842`), `config.env:52-59` (board constants with date and llama.cpp commit).
- **Problem / opportunity**: the chain is almost complete: ablations carry the commit, `config.env` carries model SHA-256 and the llama.cpp commit, the split is a pure function of the id. The two missing links are the dataset revision (P5) and the OCR package version, which decide `options` and therefore which problems the solvers and the bias prior see. Nothing records them; the `.ocr_cache.jsonl` is git-ignored and lives in `~/m3kang-data`.
- **Proposal**: have `report()` write the manifest of P5 and have `eval.py` copy `dataset.revision` and `ocr_version` from `data/manifest.json` into each `ablations.csv` row (two new columns, empty when the manifest is missing). Add a "Reproduce every figure" table to `docs/results-A.md`: figure → command → CSV in `docs/runs/` → commit → dataset revision.
- **Impact (jury or student)**: medium. Turns "we measured" into "you can rerun".
- **Effort**: S (after P5 and P7).
- **Risk**: `ablations.csv` gains two columns; `laptop/error_analysis.py` and `measure_*.py` read it by name, so append-only is safe. No INTERFACES.md change. Safe before the demo.
- **How to measure**: a new `eval.py --limit 5` row shows the revision; the table in `results-A.md` has one CSV per figure.
- **Verified**: read only.

## Discarded

- **Rewriting `origin/main` history to remove the 8 trailers (reviewer C1's fix)**: the commits are the organizers' (`mpous`), identical in `upstream/main`; rewriting them forks the team's history from upstream and alters another author's commits. P1 handles what is ours.
- **Committing `val.jsonl` "ids only" or the OCR cache**: the cache holds option text read from the images (research-only); the ids are already derivable from `data_curated/topics.json` plus the sha256 rule, so P5's manifest with counts is enough.
- **Publishing demo problem images or statements for the Project Hub article**: research-only licence; describe them (the `figure_en` fields of `demo_set.json` already do) and show the board, not the problem.
- **Rewriting the author e-mail across history**: would strand every open team branch and session; P8 fixes it going forward.

## Table

| n | title | impact | effort | safe before demo |
| --- | --- | --- | --- | --- |
| P1 | Reviewer C1 corrected: delete the three stale public branches with trailers, fix `hint_quality.json:40`, leave upstream history alone | high | S | yes |
| P2 | Remove the 13-row id→answer table from `docs/content-review.md`, add a label-table test | medium | S | yes |
| P3 | Replace the near-verbatim statement in `tests/test_solvers.py:89` and `digit_count.py:1`, add a repo-wide text-leak test | medium | M | yes |
| P4 | Replace the real example problem in `data/README.md` with `sample-1` | low | S | yes |
| P5 | Pin the M3Kang revision (`e772e61`) in `prepare_m3kang.py`, write and commit a dataset manifest | medium | S | yes |
| P6 | Pin `requirements.txt`, state Python 3.11-3.12, or migrate to `rapidocr` for 3.13+ | medium | S / M | (a) yes, (b) no |
| P7 | `.gitignore` for `*.jsonl`/images everywhere, `docs/runs/` with the four evidence CSVs (I11) | medium | S | yes |
| P8 | Non-personal, GitHub-linked commit e-mail from now on, `.mailmap` | low | S | yes |
| P9 | Finish the licence/data paragraphs of the public README (revision, Python, time, how to get the data) | high | M | yes |
| P10 | Manifest columns in `ablations.csv` and a reproduce-every-figure table | medium | S | yes |

## Addendum (controller, after fast-forwarding to origin/main 7a67b77)

P2 must be widened: `docs/demo/demo-problems.md` (merged in `7baefaf`) states the correct letter of every demo problem
in prose ("Correct answer: C", "the label is E") and lists their five option values. Same fix as P2: keep the letters
and option values in a git-ignored rehearsal file (`results/demo_answers.txt`), leave ids, topics, rungs and clicks in
the doc, and let the proposed `tests/test_no_labels_in_docs.py` also match `(answer|label|resposta)[^.\n]{0,20}\b[A-E]\b`
next to an `lvl-` id in `docs/**/*.md`.
