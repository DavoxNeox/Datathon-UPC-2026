"""Correct the model's letter bias with its own log probabilities.

A 0.8B model reading a competition problem answers close to chance, and it loves
some letters: the README's baseline chose D 21 times and A 14 times out of 40, and on
our laptop it answered A to all five sample problems. The log probabilities of the
five letters (copilot/llm.letter_scores) make the bias measurable and removable:

    corrected(l) = log p(l | problem) - alpha * log prior(l)

where prior(l) is the model's average probability of letter l over a calibration set
of TRAINING problems (calibrate_bias.py), renormalised over A to E. alpha = 1 removes
the prior fully; alpha = 0 is the raw model. When the best and second-best corrected
scores are closer than min_margin, the model has no real preference and we answer
the most common letter in the training labels instead (D, 25%).

The calibration lives in data_curated/letter_prior.json: five numbers, alpha,
min_margin and how they were measured. No problem text. It is safe to commit.
"""
import json
import math
import os

from .config import CONFIG, ROOT

LETTERS = "ABCDE"
DEFAULT_PATH = os.path.join(ROOT, "data_curated", "letter_prior.json")


def normalize(logprobs):
    """Log-softmax over the five letters: the rest of the vocabulary is impossible under the grammar."""
    values = [logprobs[l] for l in LETTERS]
    top = max(values)
    log_total = top + math.log(sum(math.exp(v - top) for v in values))
    return {l: logprobs[l] - log_total for l in LETTERS}


def prior_from_runs(runs):
    """prior(l) = log of the mean renormalised probability of l over the calibration runs."""
    sums = {l: 0.0 for l in LETTERS}
    for logprobs in runs:
        normed = normalize(logprobs)
        for l in LETTERS:
            sums[l] += math.exp(normed[l])
    return {l: math.log(sums[l] / len(runs)) for l in LETTERS}


def corrected_scores(logprobs, prior, alpha):
    normed = normalize(logprobs)
    return {l: normed[l] - alpha * prior[l] for l in LETTERS}


def choose(logprobs, prior, alpha=1.0, min_margin=0.0, fallback="D"):
    """Return (letter, margin). margin is best minus second-best corrected score, in nats."""
    scores = corrected_scores(logprobs, prior, alpha)
    ranked = sorted(LETTERS, key=lambda l: (-scores[l], l))  # ties broken alphabetically: deterministic
    margin = scores[ranked[0]] - scores[ranked[1]]
    if margin < min_margin:
        return fallback, margin
    return ranked[0], margin


def load(path=None):
    """The calibration dict, or None when there is none (then the pipeline runs the raw baseline)."""
    path = path or CONFIG.get("LETTER_BIAS_PRIOR") or DEFAULT_PATH
    if not os.path.isabs(path):
        path = os.path.join(ROOT, path)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if set(data.get("prior", {})) != set(LETTERS):
        return None
    data.setdefault("alpha", 1.0)
    data.setdefault("min_margin", 0.0)
    data.setdefault("fallback", CONFIG["FALLBACK_ANSWER"])
    return data
