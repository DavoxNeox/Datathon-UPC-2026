"""A tiny JSON client for llama-server, using only the standard library."""
import json
import urllib.request


import urllib.parse

# What the server's prompt cache holds, as far as this process knows: for each host:port, the messages before
# the last user message of the last chat request that completed. With --parallel 1 and --cache-ram 0 the
# server keeps only that prompt, so a stage can tell whether its stable prefix is still cached
# (copilot/pal.py). A generation request without messages, or one that fails, leaves it unknown (None).
LAST_CHAT = {}


def remember(url, payload, done=True):
    if not isinstance(payload, dict) or not ("messages" in payload or "prompt" in payload):
        return  # /tokenize and embeddings do not touch the generation slot
    key = urllib.parse.urlsplit(url).netloc
    LAST_CHAT[key] = list(payload["messages"][:-1]) if done and "messages" in payload else None


def post(url, payload, timeout):
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
