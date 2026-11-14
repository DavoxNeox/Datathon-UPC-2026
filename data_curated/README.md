# Curated data (committed)

Files here hold M3Kang problem **ids** and our own labels, never problem text, options or
images (M3Kang is licensed for research use only). They are built on the laptop by the
scripts in `laptop/` and read on the board by `copilot/topics.py` and friends.

| File | Built by | Content |
| --- | --- | --- |
| `topics.json` | `laptop/build_topics.py` (keywords), then `laptop/cluster_topics.py` (keywords + k-means on the index embeddings) | `{"topics": {id: topic_key}, "visual": {topic_key: bool}}` for all 1,747 ids |
| `topics_manual.json` | by hand (B) | 50 ids labelled by reading the text and the image: the gold set for the topic assignment |
| `families.json` | `laptop/build_families.py` | `{id: family_key}` for text-only problems that match a solver family, plus `names_en` |

Rebuild after changing the rules:

```bash
python3 laptop/build_topics.py                      # keywords only, prints the topic table
python3 laptop/cluster_topics.py --k 8 --manual data_curated/topics_manual.json --out data_curated/topics.json
python3 laptop/build_families.py                    # prints the family frequency table
```

Both need `data/train.jsonl`, `data/val.jsonl` and `data/index.db` (not committed).
