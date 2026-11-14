# Fixtures for the page

`lesson_hint.json`: one `hints` entry with `kind: "lesson"`, as the server will send it after
the fourth use of the hint button (`HINT_MAX_USES=4`). Until the server serves it, preview the
card by patching `/api/state` in the browser console on the student page (nothing changes on
disk; reload the page to go back to the real state):

```js
const LESSON = /* paste the object from lesson_hint.json */;
const orig = window.fetch;
window.fetch = async (p, o) => {
  const r = await orig(p, o);
  if (!String(p).endsWith("/api/state")) return r;
  const s = await r.json(); s.hints_max = 4; s.hints_left = 0; s.hints = [...s.hints, LESSON];
  return new Response(JSON.stringify(s), {headers: {"Content-Type": "application/json"}});
};
```

Running the sim with four uses: `HINT_MAX_USES=4 python3 python/main.py` (config.env keys can
be overridden from the environment).
