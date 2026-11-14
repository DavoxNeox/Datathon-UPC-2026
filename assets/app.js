// Math copilot page. Talks to the JSON endpoints of copilot/webapp.py and polls /api/state.
// Catalan first, English on the switch. No network access beyond this board.
// Layout rule: the problem is the only thing on the screen; the picture is the statement when
// the data has one (M3Kang pictures carry the text and the options), the text sits behind a chip.
const T0 = performance.now();
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));

const I18N = {
  cat: {title: "Copilot de mates", student: "Nom o àlies", teacher: "Vista del professor", help: "Ajuda", hint: "Pista",
        solution: "Solució", next: "Següent problema", mastery: "El teu progrés", close: "Tanca",
        level: "Nivell", topic: "Tema", thinking: "Un moment…", kinds: {neighbour: "Un problema semblant",
        strategy: "Una estratègia", trace: "Un pas de la solució", llm: "Pista del model", solution: "Solució", lesson: "Lliçó"},
        manip: {rotate: "Gira i volteja", paths: "Comptador de camins", dice: "El dau"},
        time: "temps", laptop: "portàtil", board: "placa (estimat)", action: "acció", load: "temps de càrrega",
        over: "supera els 60 s", image: "Imatge del problema", answered: "Ja has respost. Si vols, mira la solució.",
        welcome: "Hola! Com et dius?", course: "Curs", course_help: "Si no tries cap curs, el copilot l'endevina amb tres o quatre problemes.",
        begin: "Comença", reset: "Canvia d'alumne", auto: "Que ho endevini el copilot",
        confirm_reset: "Vols esborrar el progrés d'aquest alumne i tornar a l'inici?",
        more: "mostra-ho tot", less: "mostra'n menys", levelName: "Nivell", in_english: "en anglès",
        read_in: {eng: "Llegeix-lo en anglès", cat: "Llegeix-lo en català"}, hide_other: {eng: "Amaga l'anglès", cat: "Amaga el català"},
        other_kind: {eng: "Esglaó 0 · en anglès · no compta com a pista", cat: "Esglaó 0 · en català · no compta com a pista"},
        show_text: "Mostra el text", hide_text: "Amaga el text", more_panel: "Més", board_led: "La placa",
        timing: "Temps (per al professor)", problem: "Problema",
        theme: {auto: "Tema: automàtic", light: "Tema: clar", dark: "Tema: fosc"}, no_hints: "Ja no queden pistes en aquest problema",
        courses: ["5è de primària", "6è de primària", "1r d'ESO", "2n d'ESO", "3r d'ESO", "4t d'ESO", "1r de batxillerat", "2n de batxillerat"]},
  eng: {title: "Maths copilot", student: "Name or nickname", teacher: "Teacher view", help: "Help", hint: "Hint",
        solution: "Solution", next: "Next problem", mastery: "Your progress", close: "Close",
        level: "Level", topic: "Topic", thinking: "One moment…", kinds: {neighbour: "A similar problem",
        strategy: "A strategy", trace: "A step of the solution", llm: "Model hint", solution: "Solution", lesson: "Lesson"},
        manip: {rotate: "Rotate and flip", paths: "Path counter", dice: "The die"},
        time: "time", laptop: "laptop", board: "board (estimated)", action: "action", load: "load time",
        over: "over 60 s", image: "Problem picture", answered: "Already answered. Have a look at the solution if you like.",
        welcome: "Hi! What's your name?", course: "School year", course_help: "If you don't choose a year, the copilot finds it out with three or four problems.",
        begin: "Start", reset: "Change student", auto: "Let the copilot find out",
        confirm_reset: "Erase this student's progress and go back to the start?",
        more: "show it all", less: "show less", levelName: "Level", in_english: "in English",
        read_in: {eng: "Read it in English", cat: "Read it in Catalan"}, hide_other: {eng: "Hide the English", cat: "Hide the Catalan"},
        other_kind: {eng: "Rung 0 · in English · not counted as a hint", cat: "Rung 0 · in Catalan · not counted as a hint"},
        show_text: "Show the text", hide_text: "Hide the text", more_panel: "More", board_led: "The board",
        timing: "Timings (for the teacher)", problem: "Problem",
        theme: {auto: "Theme: automatic", light: "Theme: light", dark: "Theme: dark"}, no_hints: "No hints left on this problem",
        courses: ["Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]},
};
const THEME_GLYPH = {auto: "◐", light: "☀", dark: "☾"};
// an open book, inline so nothing is fetched; it takes the colour of its parent
const BOOK = '<svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true"><path fill="currentColor" d="M1.5 3A.5.5 0 0 1 2 2.5h4A2.5 2.5 0 0 1 8 3.6 2.5 2.5 0 0 1 10 2.5h4a.5.5 0 0 1 .5.5v9a.5.5 0 0 1-.5.5h-4c-.9 0-1.6.5-2 1.1-.4-.6-1.1-1.1-2-1.1H2a.5.5 0 0 1-.5-.5zm6 1.6c0-.6-.7-1.1-1.5-1.1H2.5v8H6c.6 0 1.1.1 1.5.4zm1 7.3c.4-.3.9-.4 1.5-.4h3.5v-8H10c-.8 0-1.5.5-1.5 1.1z"/></svg>';
let lang = "cat", state = null, lastProblem = null, imageKey = null, loadReported = false;
let textOpen = matchMedia("(max-width: 640px)").matches;   // the statement text when the picture already shows it: closed on a laptop, open on a phone (the picture is too wide to read there); the student's choice stays
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
  const sel = $("level"), keep = sel.value;
  sel.innerHTML = `<option value="auto">${esc(t().auto)}</option>` + t().courses.map((c, i) => `<option value="${i}">${esc(c)} (${t().levelName.toLowerCase()} ${i})</option>`).join("");
  sel.value = keep || "auto";
  renderTheme();
  renderTextToggle();
}

function renderTheme() {
  const mode = window.Theme ? Theme.get() : "auto";
  $("theme-label").textContent = THEME_GLYPH[mode];
  $("theme").title = t().theme[mode];
  $("theme").setAttribute("aria-label", t().theme[mode]);
}

function renderTextToggle() {
  const b = $("toggle-text");
  b.textContent = textOpen ? t().hide_text : t().show_text;
  b.setAttribute("aria-expanded", String(textOpen));
}

function drawLed(frame) {
  const c = $("led"), ctx = c.getContext("2d");
  ctx.fillStyle = "#121212"; ctx.fillRect(0, 0, c.width, c.height);
  (frame || []).forEach((row, r) => row.forEach((v, col) => {
    if (v) { ctx.shadowColor = "rgba(255,90,40,.9)"; ctx.shadowBlur = 8; } else { ctx.shadowBlur = 0; }
    ctx.fillStyle = v ? `rgba(255,96,48,${0.35 + 0.65 * v / 7})` : "#262626";
    ctx.beginPath(); ctx.arc(20 * col + 10, 20 * r + 10, v ? 7.5 : 6, 0, 2 * Math.PI); ctx.fill();
  }));
  ctx.shadowBlur = 0;
}

function optionLines(options) {
  return "ABCDE".split("").filter(l => options[l]).map(l => `${l}) ${options[l]}`).join("   ");
}

function renderProblem(p) {
  if (!p) { $("text").textContent = ""; return; }
  const changed = !lastProblem || lastProblem.id !== p.id;
  lastProblem = p;
  const text = (lang === "eng" && p.text_eng) || (lang === "cat" && p.text_cat) || p.text;
  const options = (lang === "eng" && p.options_eng) || (lang === "cat" && p.options_cat) || p.options || {};
  const hasOptions = Object.keys(options).length > 0;
  $("meta").textContent = `${t().level} ${p.level} · ${t().courses[p.level] || ""} · ${lang === "cat" ? p.topic_name_ca : p.topic_name_en}`;
  $("problem-id").textContent = `${t().problem}: ${p.id}`;
  $("text").textContent = text;
  // the picture carries the statement and the options: letters only, in the picture's order;
  // without a picture the text is the statement and the options go on the buttons
  const pictureFirst = !!p.has_image;
  $("figure").hidden = !pictureFirst;
  $("toggle-text").hidden = !pictureFirst;
  $("statement").hidden = pictureFirst && !textOpen;
  $("options-text").textContent = pictureFirst && hasOptions ? optionLines(options) : "";
  $("letters").classList.toggle("rows", !pictureFirst && hasOptions);
  $("letters").innerHTML = "ABCDE".split("").map(l =>
    `<button data-l="${l}" aria-label="${l}${!pictureFirst && options[l] ? ": " + esc(options[l]) : ""}"><span class="l">${l}</span>${!pictureFirst && options[l] ? `<span class="o">${esc(options[l])}</span>` : ""}</button>`).join("");
  if (pictureFirst) {
    if (changed || imageKey !== p.id) {
      imageKey = p.id;
      api("/api/image").then(r => { if (r.image_b64 && imageKey === p.id) { $("img").src = "data:image/png;base64," + r.image_b64; } });
    }
  } else { $("img").removeAttribute("src"); imageKey = null; }
  $("img").alt = t().image;
}

function renderTranslation(s) {
  // rung 0: the same problem in the other language, under the statement; never its label
  const other = s.other_language, tr = s.translation;
  $("translate").hidden = !s.translation_available;
  if (s.translation_available) { $("translate").textContent = tr ? t().hide_other[other] : t().read_in[other]; $("translate").classList.toggle("on", !!tr); }
  $("other").hidden = !tr;
  if (!tr) return;
  $("other-kind").textContent = t().other_kind[tr.language];
  $("other-text").textContent = tr.text;
  $("other-options").textContent = optionLines(tr.options || {});
}

function renderAnswer(s) {
  const a = s.answer;
  document.querySelectorAll("#letters button").forEach(b => {
    b.disabled = !!a || s.busy;
    b.classList.toggle("right", !!a && b.dataset.l === a.label);
    b.classList.toggle("wrong", !!a && b.dataset.l === a.letter && !a.correct);
  });
  $("verdict").textContent = txt(s.message, "text") || (lang === "cat" ? s.message.ca : s.message.en) || "";
  $("feedback").className = "feedback " + (a ? (a.correct ? "ok" : "bad") : "");
  $("next").hidden = !a;
  const left = s.hints_left ?? Infinity, max = s.hints_max ?? 3;
  $("hint").disabled = !!a || s.busy || left <= 0;
  $("hint").title = left <= 0 ? t().no_hints : "";
  // the dots are the hints left on this problem: they go out from the left as hints are used (solution and
  // rung 0 do not count). The last use is not a hint but a short lesson on the topic: a small book, not a dot.
  const dots = $("rungs");
  if (dots.children.length !== max || dots.dataset.lang !== lang) {
    dots.dataset.lang = lang;
    dots.innerHTML = Array.from({length: max}, (_, i) => i === max - 1 && max > 1 ?
      `<span class="book" title="${esc(t().kinds.lesson)}" aria-label="${esc(t().kinds.lesson)}">${BOOK}</span>` : "<span></span>").join("");
  }
  [...dots.children].forEach((dot, i) => dot.classList.toggle("on", i >= max - Math.min(left, max)));
  $("solution").disabled = s.busy || s.hints.some(h => h.kind === "solution");
  $("status").textContent = s.busy ? t().thinking : (a && !s.hints.some(h => h.kind === "solution") ? t().answered : "");
}

function renderHints(s) {
  $("hints").innerHTML = s.hints.map(h => {
    if (h.kind === "lesson") {
      // the fourth use of the button: a short lesson on the topic, its own card, never timed
      return `<article class="lesson"><div class="kind">${BOOK} ${esc(t().kinds.lesson)}</div>` +
        `<h3>${esc(txt(h, "title"))}</h3><p>${esc(txt(h, "text"))}</p></article>`;
    }
    let body = `<div>${esc(txt(h, "text"))}</div>`;
    if (h.kind === "neighbour" && h.problem) {
      const np = h.problem, opts = np.options || {}, long = (np.text || "").length > 160;
      body += `<div class="neighbour ${long ? "clamped" : ""}">${esc(np.text)}${Object.keys(opts).length ? "\n" + "ABCDE".split("").filter(l => opts[l]).map(l => `${l}) ${esc(opts[l])}`).join("   ") : ""}</div>` +
        (long ? `<button class="more" data-more>${esc(t().more)}</button>` : "") +
        (np.image_b64 ? `<div class="neighbour"><img src="data:image/png;base64,${np.image_b64}" alt=""></div>` : "");
    }
    if (h.kind === "solution" && h.trace && h.trace.length) {
      body += `<ol>${h.trace.map(step => `<li>${esc(txt(step, "text"))}</li>`).join("")}</ol>`;
    }
    const time = h.estimated_board_seconds ? ` · ${t().board} ${h.estimated_board_seconds.toFixed(1)} s` : "";
    const badge = h.kind === "llm" && h.llm_lang === "eng" && lang === "cat" ? `<span class="badge">${esc(t().in_english)}</span>` : "";
    return `<div class="hint ${h.kind}"><div class="kind">${t().kinds[h.kind] || h.kind} · ${lang === "cat" ? "esglaó" : "rung"} ${h.rung}${badge}</div>${body}` +
      `<div class="time">${t().laptop} ${(h.laptop_seconds ?? 0).toFixed(2)} s${time}</div></div>`;
  }).join("");
  // the manipulative of the last strategy card, if any
  const manip = [...s.hints].reverse().find(h => h.manipulative);
  $("manip").hidden = !manip || !!s.answer;
  if (manip) { $("manip").textContent = "🧩 " + t().manip[manip.manipulative]; $("manip").dataset.m = manip.manipulative; }
}

function renderMastery(s) {
  // something that grows: five segments per topic that light up, never a mark
  const topics = ["arithmetic", "logic", "digits", "counting", "areas", "angles", "spatial", "boards"];
  const label = {arithmetic: ["Aritmètica", "Arithmetic"], logic: ["Lògica", "Logic"], digits: ["Nombres", "Numbers"],
    counting: ["Comptar", "Counting"], areas: ["Àrees", "Areas"], angles: ["Angles", "Angles"],
    spatial: ["Espai", "Space"], boards: ["Taulers", "Boards"]};
  $("mastery").innerHTML = topics.map(k => `<span>${label[k][lang === "cat" ? 0 : 1]}</span>` +
    `<div class="segs" aria-label="${label[k][lang === "cat" ? 0 : 1]} ${s.mastery[k] || 0}/5">${[1, 2, 3, 4, 5].map(i => `<span class="${i <= (s.mastery[k] || 0) ? "on" : ""}"></span>`).join("")}</div>`).join("");
}

function renderTimeline(s) {
  const rows = s.timeline.slice(-6).reverse();
  $("timeline").innerHTML = `<tr><th>${t().action}</th><th>${t().laptop}</th><th>${t().board}</th></tr>` +
    rows.map(r => `<tr><td>${esc(r.action)}</td><td>${r.laptop_s.toFixed(3)} s</td><td class="${r.board_s > 60 ? "over" : ""}">${r.board_s ? r.board_s.toFixed(1) + " s" : "–"}${r.board_s > 60 ? " · " + t().over : ""}</td></tr>`).join("");
}

function render(s) {
  state = s;
  if (lang !== s.lang) { lang = s.lang; applyI18n(); }
  $("start").hidden = s.started; $("app").hidden = !s.started;
  $("who").hidden = !s.started; $("reset").hidden = !s.started;
  $("who").textContent = s.student + (s.level !== null && s.level !== undefined ? ` · ${t().courses[s.level]}` : "");
  drawLed(s.led); renderTimeline(s);
  if (!s.started) { if (!loadReported) { loadReported = true; $("load").textContent = `${t().load}: ${Math.round(performance.now() - T0)} ms`; } return; }
  renderProblem(s.problem); renderTranslation(s); renderAnswer(s); renderHints(s); renderMastery(s);
  if (!loadReported) { loadReported = true; $("load").textContent = `${t().load}: ${Math.round(performance.now() - T0)} ms`; }
}

async function poll() {
  try { render(await api("/api/state")); } catch (e) { $("status").textContent = "…"; }
}

$("letters").addEventListener("click", async e => { const b = e.target.closest("button[data-l]"); if (b && !b.disabled) render(await api("/api/answer/" + b.dataset.l)); });
$("hint").onclick = async () => { await api("/api/hint"); poll(); };
$("translate").onclick = async () => render(await api("/api/translate/" + (state && state.translation ? "hide" : "show")));
$("solution").onclick = async () => { await api("/api/solution"); poll(); };
$("next").onclick = async () => render(await api("/api/next"));
$("lang-cat").onclick = async () => render(await api("/api/lang/cat"));
$("lang-eng").onclick = async () => render(await api("/api/lang/eng"));
$("begin").onclick = async () => render(await api(`/api/start/${encodeURIComponent($("student").value.trim() || "demo")}/${$("level").value}`));
$("student").addEventListener("keydown", e => { if (e.key === "Enter") $("begin").click(); });
$("reset").onclick = async () => { if (confirm(t().confirm_reset)) { lastProblem = null; render(await api("/api/reset")); } };
$("hints").addEventListener("click", e => { const b = e.target.closest("button[data-more]"); if (!b) return; const box = b.previousElementSibling; box.classList.toggle("clamped"); b.textContent = box.classList.contains("clamped") ? t().more : t().less; });
$("manip").onclick = () => { const m = $("manip").dataset.m; $("dialog-title").textContent = t().manip[m]; $("dialog-frame").src = `manip/${m}.html?lang=${lang}${window.Theme ? Theme.query() : ""}`; $("dialog").showModal(); };
$("dialog-close").onclick = () => $("dialog").close();
$("dialog").addEventListener("close", () => { $("dialog-frame").src = "about:blank"; $("zoom").hidden = true; $("dialog-frame").hidden = false; });  // also after Escape
// the picture, bigger: useful on a phone, where M3Kang's wide scans get small
$("figure").onclick = () => { if (!$("img").src) return; $("dialog-title").textContent = t().image; $("zoom").src = $("img").src; $("zoom").hidden = false; $("dialog-frame").hidden = true; $("dialog").showModal(); };
$("toggle-text").onclick = () => { textOpen = !textOpen; renderTextToggle(); if (state) renderProblem(state.problem); };
$("theme").onclick = () => { if (window.Theme) Theme.next(); renderTheme(); };
$("more").onclick = () => { const open = $("panel").hidden; $("panel").hidden = !open; $("more").setAttribute("aria-expanded", String(open)); };
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !$("panel").hidden) { $("more").click(); return; }
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.metaKey || e.ctrlKey || e.altKey || $("dialog").open || !state || !state.started) return;
  const k = e.key.toUpperCase();
  if ("ABCDE".includes(k) && k.length === 1) { const b = document.querySelector(`#letters button[data-l="${k}"]`); if (b && !b.disabled) b.click(); }
  else if (k === "P" || k === "H") $("hint").click();
  else if (k === "T" && !$("translate").hidden) $("translate").click();
  else if (k === "N") $("next").click();
});
applyI18n();
poll();
setInterval(poll, 500);
