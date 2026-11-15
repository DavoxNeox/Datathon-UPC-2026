"""A tiny JSON client for llama-server, using only the standard library."""
import json
import urllib.parse
import urllib.request

from .config import CONFIG

# LLM_DEFAULT_SLOT (default -1 = let the server choose): the server slot every generation request goes to unless it
# names one (id_slot). Only for a server started with --parallel 2 or more, where copilot/pal.py keeps its own slot
# (PAL_SLOT) so that think and the solvers never evict its cached block. On a --parallel 1 server leave it at -1.
DEFAULT_SLOT = int(CONFIG.get("LLM_DEFAULT_SLOT", "-1") or -1)

# What the server's prompt cache holds, as far as this process knows: for each host:port and slot, the messages
# before the last user message of the last chat request that completed. With --cache-ram 0 a slot keeps only
# that prompt, so a stage can tell whether its stable prefix is still cached (copilot/pal.py). A generation
# request without messages, or one that fails, leaves it unknown (None).
LAST_CHAT = {}


def cache_key(url, slot=-1):
    return f"{urllib.parse.urlsplit(url).netloc}#{slot}"


def remember(url, payload, done=True):
    if not isinstance(payload, dict) or not ("messages" in payload or "prompt" in payload):
        return  # /tokenize and embeddings do not touch the generation slot
    key = cache_key(url, payload.get("id_slot", -1))
    LAST_CHAT[key] = list(payload["messages"][:-1]) if done and "messages" in payload else None


def post(url, payload, timeout):
    if DEFAULT_SLOT >= 0 and isinstance(payload, dict) and ("messages" in payload or "prompt" in payload) \
            and "id_slot" not in payload:
        payload = dict(payload, id_slot=DEFAULT_SLOT)
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    remember(url, payload, done=False)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read())
    remember(url, payload)
    return result


def get(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read())
