"""Ask the small language model for one letter, A to E."""
from .config import CONFIG
from .client import post

URL = f"http://127.0.0.1:{CONFIG['LLM_PORT']}/v1/chat/completions"

# Keep the system prompt stable: llama-server caches the start of the prompt,
# so text that never changes is only read once.
SYSTEM = ("You solve multiple-choice math competition problems for school students. "
          "Read the problem and the options, then reply with the letter of the correct option.")


def format_problem(problem, sees_image=False):
    lines = [problem["text"].strip()]
    options = problem.get("options") or {}
    for letter in "ABCDE":
        if letter in options:
            lines.append(f"{letter}) {options[letter]}")
    if not options:
        lines.append("(The options are in the picture.)" if sees_image else
                     "(The options are in a picture that you can't see. Pick the most likely letter.)")
    return "\n".join(lines)


def build_messages(problem, examples=(), image_b64=None):
    """image_b64 is a PNG as base64 text. Only a server started with --mmproj can see it."""
    messages = [{"role": "system", "content": SYSTEM}]
    for ex in examples:  # solved problems retrieved with RAG, if any
        messages.append({"role": "user", "content": format_problem(ex) + "\nAnswer:"})
        messages.append({"role": "assistant", "content": ex["label"]})
    text = format_problem(problem, sees_image=bool(image_b64)) + "\nAnswer:"
    if image_b64:
        content = [{"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_b64}},
                   {"type": "text", "text": text}]
    else:
        content = text
    messages.append({"role": "user", "content": content})
    return messages


def answer_letter(problem, examples=(), timeout=60, image_b64=None, url=URL):
    """Return (letter, timings). The grammar makes any other output impossible."""
    response = post(url, {
        "messages": build_messages(problem, examples, image_b64),
        "grammar": "root ::= [A-E]",
        "max_tokens": 1,
        "temperature": 0,
        "seed": int(CONFIG["SEED"]),
        "cache_prompt": True,
    }, timeout=timeout)
    letter = response["choices"][0]["message"]["content"].strip()
    return letter, response.get("timings", {})


LETTERS = "ABCDE"


def letter_scores(problem, examples=(), timeout=60, url=URL, top=20):
    """Return (letter, {letter: logprob}, timings) in ONE request, with no extra tokens.

    The model's log probability of each letter A to E as the first answer token.
    top_logprobs lists the model's top candidates BEFORE the grammar is applied
    (tokens such as "To" or "The" appear too), so ask for enough of them: with 10,
    all five letters were present on our tests. A letter that is still missing gets
    one nat less than the worst listed candidate.
    """
    response = post(url, {
        "messages": build_messages(problem, examples),
        "grammar": "root ::= [A-E]",
        "max_tokens": 1,
        "temperature": 0,
        "seed": int(CONFIG["SEED"]),
        "cache_prompt": True,
        "logprobs": True,
        "top_logprobs": top,
    }, timeout=timeout)
    choice = response["choices"][0]
    letter = choice["message"]["content"].strip()
    candidates = {}
    for token in (choice.get("logprobs") or {}).get("content") or []:
        for item in token.get("top_logprobs", []):
            candidates[item["token"]] = item["logprob"]
        break  # only the first (and only) generated token
    floor = (min(candidates.values()) if candidates else 0.0) - 1.0
    scores = {l: candidates.get(l, floor) for l in LETTERS}
    return letter, scores, response.get("timings", {})
