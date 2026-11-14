// Math copilot page. Talks to the JSON endpoints of copilot/webapp.py and polls /api/state.
// Catalan first, English on the switch. No network access beyond this board.
const T0 = performance.now();
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));

const I18N = {
  cat: {title: "Copilot de mates", student: "Alumne", teacher: "Vista del professor", help: "Ajuda", hint: "Pista",
        solution: "Solució", next: "Següent problema", mastery: "Domini per tema", close: "Tanca",
        level: "Nivell", topic: "Tema", thinking: "Pensant…", kinds: {neighbour: "Pista 1 · problema semblant",
        strategy: "Estratègia", trace: "Pas de la solució", llm: "Pista del model", solution: "Solució"},
        manip: {rotate: "Gira i volteja", paths: "Comptador de camins", dice: "El dau"},
        time: "temps", laptop: "portàtil", board: "placa (est.)", action: "acció", load: "càrrega de la pàgina",
        over: "supera els 60 s", image: "Imatge del problema", answered: "Ja has respost. Pots veure la solució."},
  eng: {title: "Maths copilot", student: "Student", teacher: "Teacher view", help: "Help", hint: "Hint",
        solution: "Solution", next: "Next problem", mastery: "Mastery by topic", close: "Close",
        level: "Level", topic: "Topic", thinking: "Thinking…", kinds: {neighbour: "Hint 1 · similar problem",
        strategy: "Strategy", trace: "Solution step", llm: "Model hint", solution: "Solution"},
        manip: {rotate: "Rotate and flip", paths: "Path counter", dice: "The die"},
        time: "time", laptop: "laptop", board: "board (est.)", action: "action", load: "page load",
        over: "over 60 s", image: "Problem picture", answered: "Already answered. You can see the solution."},
};
let lang = "cat", state = null, lastProblem = null, imageKey = null, loadReported = false;
const t = () => I18N[lang];
const txt = (obj, key) => obj[key + "_" + (lang === "cat" ? "ca" : "en")] ?? obj[key + "_ca"] ?? "";

async function api(path) {
  const started = performance.now();
  const r = await fetch(path);
  const data = await r.json();
  data._ms = Math.round(performance.now() - started);
  return data;
}

function applyI18n() {
  document.documentElement.lang = lang === "cat" ? "ca" : "en";
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t()[el.dataset.i18n]; });
  $("lang-cat").classList.toggle("on", lang === "cat");
  $("lang-eng").classList.toggle("on", lang === "eng");
  document.title = t().title;
}

function drawLed(frame) {
  const c = $("led"), ctx = c.getContext("2d");
  ctx.fillStyle = "#111"; ctx.fillRect(0, 0, c.width, c.height);
  (frame || []).forEach((row, r) => row.forEach((v, col) => {
    ctx.fillStyle = v ? `rgba(255,80,40,${0.25 + 0.75 * v / 7})` : "#2a2a2a";
    ctx.beginPath(); ctx.arc(10 * col + 5, 10 * r + 5, 3.4, 0, 2 * Math.PI); ctx.fill();
  }));
}

function renderProblem(p) {
  if (!p) { $("text").textContent = ""; return; }
  const changed = !lastProblem || lastProblem.id !== p.id;
  lastProblem = p;
  const text = (lang === "eng" && p.text_eng) || (lang === "cat" && p.text_cat) || p.text;
  const options = (lang === "eng" && p.options_eng) || (lang === "cat" && p.options_cat) || p.options || {};
  $("meta").textContent = `${t().level} ${p.level} · ${t().topic}: ${lang === "cat" ? p.topic_name_ca : p.topic_name_en} · ${p.id}`;
  $("text").textContent = text;
  $("letters").innerHTML = "ABCDE".split("").map(l =>
    `<button data-l="${l}">${l}${options[l] ? `<small>${esc(options[l])}</small>` : ""}</button>`).join("");
  if (p.has_image) {
    if (changed || imageKey !== p.id) {
      imageKey = p.id;
      api("/api/image").then(r => { if (r.image_b64 && imageKey === p.id) { $("img").src = "data:image/png;base64," + r.image_b64; $("img").hidden = false; } });
    }
  } else { $("img").hidden = true; $("img").removeAttribute("src"); imageKey = null; }
  $("img").alt = t().image;
}

function renderAnswer(s) {
  const a = s.answer;
  document.querySelectorAll("#letters button").forEach(b => {
    b.disabled = !!a || s.busy;
    b.classList.toggle("right", !!a && b.dataset.l === a.label);
    b.classList.toggle("wrong", !!a && b.dataset.l === a.letter && !a.correct);
  });
  $("verdict").textContent = txt(s.message, "text") || (lang === "cat" ? s.message.ca : s.message.en) || "";
  $("verdict").className = "verdict " + (a ? (a.correct ? "ok" : "bad") : "");
  $("next").hidden = !a;
  $("hint").disabled = !!a || s.busy;
  $("solution").disabled = s.busy || s.hints.some(h => h.kind === "solution");
  $("status").textContent = s.busy ? t().thinking : (a && !s.hints.some(h => h.kind === "solution") ? t().answered : "");
  document.querySelectorAll("#rungs span").forEach((dot, i) => dot.classList.toggle("on", i < Math.min(s.rung, 3)));
}

function renderHints(s) {
  $("hints").innerHTML = s.hints.map(h => {
    let body = `<div>${esc(txt(h, "text"))}</div>`;
    if (h.kind === "neighbour" && h.problem) {
      const np = h.problem, opts = np.options || {};
      body += `<div class="neighbour">${esc(np.text)}${Object.keys(opts).length ? "\n" + "ABCDE".split("").filter(l => opts[l]).map(l => `${l}) ${esc(opts[l])}`).join("   ") : ""}` +
        (np.image_b64 ? `<img src="data:image/png;base64,${np.image_b64}" alt="">` : "") + `</div>`;
    }
    if (h.kind === "solution" && h.trace && h.trace.length) {
      body += `<ol>${h.trace.map(step => `<li>${esc(txt(step, "text"))}</li>`).join("")}</ol>`;
    }
    const time = h.estimated_board_seconds ? ` · ${t().board} ${h.estimated_board_seconds.toFixed(1)} s` : "";
    return `<div class="hint ${h.kind}"><div class="kind">${t().kinds[h.kind] || h.kind} · ${lang === "cat" ? "esglaó" : "rung"} ${h.rung}</div>${body}` +
      `<div class="time">${t().laptop} ${(h.laptop_seconds ?? 0).toFixed(2)} s${time}</div></div>`;
  }).join("");
  // the manipulative of the last strategy card, if any
  const manip = [...s.hints].reverse().find(h => h.manipulative);
  $("manip").hidden = !manip || !!s.answer;
  if (manip) { $("manip").textContent = "🧩 " + t().manip[manip.manipulative]; $("manip").dataset.m = manip.manipulative; }
}

function renderMastery(s) {
  const topics = ["arithmetic", "logic", "digits", "counting", "areas", "angles", "spatial", "boards"];
  const label = {arithmetic: ["Aritmètica", "Arithmetic"], logic: ["Lògica", "Logic"], digits: ["Xifres", "Digits"],
    counting: ["Comptatge", "Counting"], areas: ["Àrees", "Areas"], angles: ["Angles", "Angles"],
    spatial: ["Espacial", "Spatial"], boards: ["Taulers", "Boards"]};
  $("mastery").innerHTML = topics.map(k => `<span>${label[k][lang === "cat" ? 0 : 1]}</span>` +
    `<div class="bar"><div style="width:${20 * (s.mastery[k] || 0)}%"></div></div>`).join("");
}

function renderTimeline(s) {
  const rows = s.timeline.slice(-6).reverse();
  $("timeline").innerHTML = `<tr><th>${t().action}</th><th>${t().laptop}</th><th>${t().board}</th></tr>` +
    rows.map(r => `<tr><td>${esc(r.action)}</td><td>${r.laptop_s.toFixed(3)} s</td><td class="${r.board_s > 60 ? "over" : ""}">${r.board_s ? r.board_s.toFixed(1) + " s" : "–"}${r.board_s > 60 ? " · " + t().over : ""}</td></tr>`).join("");
}

function render(s) {
  state = s;
  if (lang !== s.lang) { lang = s.lang; applyI18n(); }
  $("student").value === "" && ($("student").value = s.student);
  renderProblem(s.problem); renderAnswer(s); renderHints(s); renderMastery(s); renderTimeline(s); drawLed(s.led);
  if (!loadReported) { loadReported = true; $("load").textContent = `${t().load}: ${Math.round(performance.now() - T0)} ms`; }
}

async function poll() {
  try { render(await api("/api/state")); } catch (e) { $("status").textContent = "…"; }
}

$("letters").addEventListener("click", async e => { const b = e.target.closest("button[data-l]"); if (b && !b.disabled) render(await api("/api/answer/" + b.dataset.l)); });
$("hint").onclick = async () => { await api("/api/hint"); poll(); };
$("solution").onclick = async () => { await api("/api/solution"); poll(); };
$("next").onclick = async () => render(await api("/api/next"));
$("lang-cat").onclick = async () => render(await api("/api/lang/cat"));
$("lang-eng").onclick = async () => render(await api("/api/lang/eng"));
$("student").addEventListener("change", async () => render(await api("/api/student/" + encodeURIComponent($("student").value || "demo"))));
$("manip").onclick = () => { const m = $("manip").dataset.m; $("dialog-title").textContent = t().manip[m]; $("dialog-frame").src = `manip/${m}.html?lang=${lang}`; $("dialog").showModal(); };
$("dialog-close").onclick = () => { $("dialog").close(); $("dialog-frame").src = "about:blank"; };
document.addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT" || e.metaKey || e.ctrlKey || e.altKey || $("dialog").open) return;
  const k = e.key.toUpperCase();
  if ("ABCDE".includes(k) && k.length === 1) { const b = document.querySelector(`#letters button[data-l="${k}"]`); if (b && !b.disabled) b.click(); }
  else if (k === "P" || k === "H") $("hint").click();
  else if (k === "N") $("next").click();
});
applyI18n();
poll();
setInterval(poll, 500);
