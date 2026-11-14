// Math copilot page. Talks to the JSON endpoints of copilot/webapp.py and polls /api/state.
// Catalan first, English on the switch. No network access beyond this board.
// Layout rule: the problem is the only thing on the screen, in three parts: the statement as text,
// the figure cut out of the M3Kang scan (the scan also holds the statement and the options, which
// the page never shows twice) and the options, as text rows when the OCR read them or as the
// strip of the scan when they are pictures or symbols. Everything else lives behind "Menú".
const T0 = performance.now();
const $ = id => document.getElementById(id);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));

const I18N = {
  cat: {title: "Copilot de mates", student: "Àlies", teacher: "Vista del professor", hint: "Pista",
        solution: "Solució", next: "Continua", mastery: "El teu progrés", close: "Tanca",
        level: "Nivell", topic: "Tema", thinking: "Un moment…", kinds: {neighbour: "Un problema semblant",
        strategy: "Una estratègia", trace: "Un pas de la solució", llm: "Pista del model", solution: "Solució", lesson: "Lliçó"}, lesson_sub: "una idea per pensar-hi",
        manip: {rotate: "Gira i volteja", paths: "Comptador de camins", dice: "El dau"},
        time: "temps", laptop: "portàtil", board: "placa (estimat)", action: "acció", load: "temps de càrrega",
        over: "supera els 60 s", image: "Figura del problema", options_image: "Les opcions", answered: "Ja has respost. Si vols, mira la solució.",
        welcome: "Hola! Com et dius?", course: "Curs", course_help: "Si no tries cap curs, el copilot l'endevina.",
        begin: "Comença", reset: "Canvia d'alumne", auto: "Que ho endevini el copilot",
        confirm_reset: "Segur? Esborra el progrés",
        more: "mostra-ho tot", less: "mostra'n menys", levelName: "Nivell", in_english: "en anglès",
        more_panel: "Menú", board_led: "La placa", timing: "Temps (per al professor)", problem: "Problema",
        theme: {auto: "Tema: automàtic", light: "Tema: clar", dark: "Tema: fosc"}, no_hints: "Ja no queden pistes en aquest problema",
        courses: ["5è de primària", "6è de primària", "1r d'ESO", "2n d'ESO", "3r d'ESO", "4t d'ESO", "1r de batxillerat", "2n de batxillerat"]},
  eng: {title: "Maths copilot", student: "Nickname", teacher: "Teacher view", hint: "Hint",
        solution: "Solution", next: "Continue", mastery: "Your progress", close: "Close",
        level: "Level", topic: "Topic", thinking: "One moment…", kinds: {neighbour: "A similar problem",
        strategy: "A strategy", trace: "A step of the solution", llm: "Model hint", solution: "Solution", lesson: "Lesson"}, lesson_sub: "an idea to think with",
        manip: {rotate: "Rotate and flip", paths: "Path counter", dice: "The die"},
        time: "time", laptop: "laptop", board: "board (estimated)", action: "action", load: "load time",
        over: "over 60 s", image: "Problem figure", options_image: "The options", answered: "Already answered. Have a look at the solution if you like.",
        welcome: "Hi! What's your name?", course: "School year", course_help: "If you don't choose a year, the copilot finds it out.",
        begin: "Start", reset: "Change student", auto: "Let the copilot find out",
        confirm_reset: "Sure? Erase the progress",
        more: "show it all", less: "show less", levelName: "Level", in_english: "in English",
        more_panel: "Menu", board_led: "The board", timing: "Timings (for the teacher)", problem: "Problem",
        theme: {auto: "Theme: automatic", light: "Theme: light", dark: "Theme: dark"}, no_hints: "No hints left on this problem",
        courses: ["Grade 5", "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]},
};
const THEME_GLYPH = {auto: "◐", light: "☀", dark: "☾"};
let lang = "cat", state = null, lastProblem = null, hadAnswer = false, loadReported = false;
const t = () => I18N[lang];
const txt = (obj, key) => obj[key + "_" + (lang === "cat" ? "ca" : "en")] ?? obj[key + "_ca"] ?? "";

async function api(path) {
  const started = performance.now();
  const r = await fetch(path);
  const data = await r.json();
  data._ms = Math.round(performance.now() - started);
  return data;
}

// Short sentences as bullets: young readers skim a list, not a paragraph.
function bullets(text) {
  const parts = String(text || "").split(/(?<=[.!?:])\s+(?=[A-ZÀ-Ú¿¡«"(])/).map(s => s.trim()).filter(Boolean);
  if (parts.length <= 1) return `<p>${esc(text)}</p>`;
  return `<ul class="bul">${parts.map(s => `<li>${esc(s)}</li>`).join("")}</ul>`;
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
  renderDropdown();
  renderTheme();
}

// The course dropdown: a button and a list that opens in the flow of the page (no popup, no native menu).
// The hidden <select id="level"> keeps the value, so the rest of the page reads it as before.
function renderDropdown(open) {
  const sel = $("level"), list = $("level-list"), btn = $("level-button");
  if (open !== undefined) { list.hidden = !open; btn.setAttribute("aria-expanded", String(open)); }
  $("level-text").textContent = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].textContent : "";
  list.innerHTML = [...sel.options].map(o => `<li role="option" tabindex="-1" data-v="${o.value}" aria-selected="${o.value === sel.value}">${esc(o.textContent)}</li>`).join("");
}
function chooseLevel(value) { $("level").value = value; renderDropdown(false); $("level-button").focus(); }
$("level-button").onclick = () => renderDropdown($("level-list").hidden);
$("level-list").addEventListener("click", e => { const li = e.target.closest("li[data-v]"); if (li) chooseLevel(li.dataset.v); });
$("level-button").addEventListener("keydown", e => {
  if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); renderDropdown(true); const items = [...$("level-list").children]; (items.find(li => li.getAttribute("aria-selected") === "true") || items[0]).focus(); }
});
$("level-list").addEventListener("keydown", e => {
  const items = [...$("level-list").children], i = items.indexOf(document.activeElement);
  if (e.key === "ArrowDown") { e.preventDefault(); (items[i + 1] || items[0]).focus(); }
  else if (e.key === "ArrowUp") { e.preventDefault(); (items[i - 1] || items[items.length - 1]).focus(); }
  else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); if (i >= 0) chooseLevel(items[i].dataset.v); }
  else if (e.key === "Escape" || e.key === "Tab") { renderDropdown(false); if (e.key === "Escape") $("level-button").focus(); }
});
document.addEventListener("click", e => { if (!e.target.closest(".dropdown") && !$("level-list").hidden) renderDropdown(false); });

function renderTheme() {
  const mode = window.Theme ? Theme.get() : "auto";
  $("theme-label").textContent = THEME_GLYPH[mode];
  $("theme").title = t().theme[mode];
  $("theme").setAttribute("aria-label", t().theme[mode]);
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

// ---------------------------------------------------------------- the scan, in parts
// An M3Kang scan is 1653 px wide: the statement at the top left in a sans font, the figure to the
// right of it or below it, and the options "A) ... E)" in the last row(s). The page already has the
// statement as text, so it cuts the figure (and, when the OCR could not read them, the options)
// out of the scan. Pixels are read on a canvas at 2 px cells; words are bridged into lines, lines
// are grouped into components, and the components are sorted by shape and position.
const CELL = 2, HGAP = 10;   // cells per step, cells of blank bridged inside a line of text
const CLEAN = /^[\p{L}\p{N}\s.,:;%°€$'"\/+\-×·()²³½¼¾πσ=<>!?…]+$/u;
const optionsClean = o => Object.keys(o || {}).length >= 2 && Object.values(o).every(v => CLEAN.test(v));

function scanComponents(img) {
  const W = img.naturalWidth, H = img.naturalHeight;
  const c = document.createElement("canvas"); c.width = W; c.height = H;
  const ctx = c.getContext("2d", {willReadFrequently: true}); ctx.drawImage(img, 0, 0);
  const d = ctx.getImageData(0, 0, W, H).data;
  const cw = Math.ceil(W / CELL), ch = Math.ceil(H / CELL), ink = new Uint8Array(cw * ch);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const i = 4 * (y * W + x);
    if (d[i] * 299 + d[i + 1] * 587 + d[i + 2] * 114 < 160000) ink[((y / CELL) | 0) * cw + ((x / CELL) | 0)] = 1;
  }
  for (let r = 0; r < ch; r++) {   // bridge the blanks between words
    let last = -99;
    for (let col = 0; col < cw; col++) if (ink[r * cw + col]) {
      if (col - last - 1 > 0 && col - last - 1 <= HGAP) for (let k = last + 1; k < col; k++) ink[r * cw + k] = 1;
      last = col;
    }
  }
  const seen = new Uint8Array(cw * ch), comps = [], stack = [];
  for (let start = 0; start < cw * ch; start++) {
    if (!ink[start] || seen[start]) continue;
    seen[start] = 1; stack.push(start);
    let x0 = cw, x1 = 0, y0 = ch, y1 = 0;
    while (stack.length) {
      const i = stack.pop(), r = (i / cw) | 0, col = i - r * cw;
      if (col < x0) x0 = col; if (col > x1) x1 = col; if (r < y0) y0 = r; if (r > y1) y1 = r;
      const n = [i - cw, i + cw, col > 0 ? i - 1 : -1, col < cw - 1 ? i + 1 : -1];
      for (const j of n) if (j >= 0 && j < cw * ch && ink[j] && !seen[j]) { seen[j] = 1; stack.push(j); }
    }
    comps.push({x0: x0 * CELL, y0: y0 * CELL, x1: Math.min(W, (x1 + 1) * CELL), y1: Math.min(H, (y1 + 1) * CELL)});
  }
  return {comps, W, H};
}

function classifyParts(comps, W, H, clean) {
  for (const c of comps) { c.w = c.x1 - c.x0; c.h = c.y1 - c.y0; }
  const hs = comps.filter(c => c.h >= 12 && c.h <= 64 && c.w >= 0.05 * W).map(c => c.h).sort((a, b) => a - b);
  const lineH = hs.length ? hs[hs.length >> 1] : 30;
  const textlike = c => c.h >= 0.45 * lineH && c.h <= 1.8 * lineH;
  // option rows: bands of at least three options with wide gaps, spread across the page
  const bands = [];
  for (const c of comps.filter(textlike).sort((a, b) => a.y0 - b.y0)) {
    const b = bands.find(b => c.y0 < b.y1 - 0.3 * lineH && c.y1 > b.y0 + 0.3 * lineH);
    if (b) { b.items.push(c); b.y0 = Math.min(b.y0, c.y0); b.y1 = Math.max(b.y1, c.y1); } else bands.push({y0: c.y0, y1: c.y1, items: [c]});
  }
  const isOptions = b => {
    const merged = [];
    for (const c of [...b.items].sort((a, b) => a.x0 - b.x0)) {
      if (merged.length && c.x0 - merged[merged.length - 1].x1 < 1.2 * lineH) merged[merged.length - 1].x1 = Math.max(merged[merged.length - 1].x1, c.x1);
      else merged.push({x0: c.x0, x1: c.x1});
    }
    return merged.length >= 3 && merged[merged.length - 1].x1 - merged[0].x0 >= 0.4 * W;
  };
  const opt = new Set(); bands.filter(isOptions).forEach(b => b.items.forEach(c => opt.add(c)));
  // the text column: its left margin from the long lines, its right limit from the first big thing on the right
  const longLines = comps.filter(c => textlike(c) && c.w >= 0.25 * W && !opt.has(c));
  const textLeft = longLines.length ? Math.min(...longLines.map(c => c.x0)) : 0;
  const bigRight = comps.filter(c => !textlike(c) && !opt.has(c) && c.h > 1.8 * lineH && c.x0 > 0.45 * W);
  const figLeft = bigRight.length ? Math.min(...bigRight.map(c => c.x0)) : W;
  const paragraph = c => c.x0 <= textLeft + lineH && c.w >= 0.35 * W && c.h <= 6 * lineH && c.x1 <= figLeft;
  const stmt = new Set(comps.filter(c => !opt.has(c) && ((textlike(c) && c.x0 <= textLeft + lineH && c.w >= 0.08 * W) || paragraph(c))));
  let grew = true;
  while (grew) {   // pieces of a justified line, and short last lines, that belong to the statement
    grew = false;
    for (const c of comps) {
      if (stmt.has(c) || opt.has(c) || !textlike(c) || c.x1 > figLeft - 0.3 * lineH) continue;
      let sameRow = false, nextLine = false;
      for (const s of stmt) {
        if (c.y0 < s.y1 - 0.2 * lineH && c.y1 > s.y0 + 0.2 * lineH && c.x0 >= s.x1 - lineH) sameRow = true;
        if (c.x0 <= textLeft + lineH && c.y0 - s.y1 >= 0 && c.y0 - s.y1 <= 1.5 * lineH) nextLine = true;
      }
      if (sameRow || nextLine) { stmt.add(c); grew = true; }
    }
  }
  const figure = comps.filter(c => !stmt.has(c) && !opt.has(c) && c.w * c.h >= (0.6 * lineH) ** 2);
  const bbox = (cs, pad) => cs.length ? [Math.max(0, Math.min(...cs.map(c => c.x0)) - pad), Math.max(0, Math.min(...cs.map(c => c.y0)) - pad),
                                         Math.min(W, Math.max(...cs.map(c => c.x1)) + pad), Math.min(H, Math.max(...cs.map(c => c.y1)) + pad)] : null;
  let fb = bbox(figure, 8), ob = bbox([...opt], 6);
  if (fb && (fb[2] - fb[0]) * (fb[3] - fb[1]) < (2 * lineH) ** 2) fb = null;
  if (clean) ob = null;   // the options are readable text: the buttons carry them
  else if (fb && ob && ob[1] - fb[3] < 2 * lineH && Math.min(ob[2], fb[2]) - Math.max(ob[0], fb[0]) >= 0.6 * (ob[2] - ob[0])) {
    fb = [Math.min(fb[0], ob[0]), Math.min(fb[1], ob[1]), Math.max(fb[2], ob[2]), Math.max(fb[3], ob[3])]; ob = null;   // pictures with their letters
  }
  return {figure: fb, options: ob, statement: bbox([...stmt], 0)};
}

function cropPart(img, box, masks) {
  const c = document.createElement("canvas"); c.width = box[2] - box[0]; c.height = box[3] - box[1];
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, c.width, c.height);
  ctx.drawImage(img, box[0], box[1], c.width, c.height, 0, 0, c.width, c.height);
  for (const m of masks) if (m) ctx.fillRect(m[0] - box[0], m[1] - box[1], m[2] - m[0], m[3] - m[1]);   // the text the page already shows
  return c.toDataURL("image/png");
}

function extractParts(img, clean) {
  const {comps, W, H} = scanComponents(img);
  const parts = classifyParts(comps, W, H, clean);
  return {
    figure: parts.figure ? cropPart(img, parts.figure, [parts.statement, parts.options]) : null,
    options: parts.options ? cropPart(img, parts.options, []) : null,
  };
}

// one scan per problem: fetched once, cut once, then reused on every poll
let scan = {id: null, figure: null, options: null, whole: null};
function loadScan(p, clean) {
  scan = {id: p.id, figure: null, options: null, whole: null};
  api("/api/image").then(r => {
    if (!r.image_b64 || scan.id !== p.id) return;
    const img = new Image();
    img.onload = () => {
      if (scan.id !== p.id) return;
      try { Object.assign(scan, extractParts(img, clean)); }
      catch (e) { scan.whole = img.src; }   // anything odd: the whole scan, as before
      if (!scan.figure && !scan.options && !clean) scan.whole = img.src;   // nothing found but the options are unreadable: show the scan
      applyScan();
    };
    img.src = "data:image/png;base64," + r.image_b64;
  });
}
function applyScan() {
  const fig = scan.figure || scan.whole;
  $("figure").hidden = !fig; if (fig) $("img").src = fig; else $("img").removeAttribute("src");
  // small crops (a die, a 5x5 grid) are drawn bigger; the CSS caps them at the column's width
  $("img").onload = () => { const w = $("img").naturalWidth; $("img").style.width = w && w < 500 ? `${Math.round(w * 1.6)}px` : ""; };
  $("strip").hidden = !scan.options; if (scan.options) $("strip-img").src = scan.options; else $("strip-img").removeAttribute("src");
  $("img").alt = t().image; $("strip-img").alt = t().options_image;
}

function renderProblem(p) {
  if (!p) { $("text").textContent = ""; return; }
  const changed = !lastProblem || lastProblem.id !== p.id;
  if (changed) { $("manip-box").hidden = true; $("manip-frame").src = "about:blank"; $("figure").classList.remove("zoomed"); }
  lastProblem = p;
  // the scan's line breaks go; a blank line stays a paragraph; the problem's number goes (the page is not a paper)
  const text = ((lang === "eng" && p.text_eng) || (lang === "cat" && p.text_cat) || p.text || "").replace(/^\s*\d+[.)]\s*/, "").replace(/\n{2,}/g, "\u2029").replace(/\s*\n\s*/g, " ").replace(/\u2029/g, "\n\n");
  const options = (lang === "eng" && p.options_eng) || (lang === "cat" && p.options_cat) || p.options || {};
  const clean = optionsClean(options);
  $("meta").textContent = `${t().level} ${p.level} · ${t().courses[p.level] || ""} · ${lang === "cat" ? p.topic_name_ca : p.topic_name_en}`;
  $("problem-id").textContent = `${t().problem}: ${p.id}`;
  $("text").textContent = text;
  $("letters").classList.toggle("rows", clean);
  $("letters").innerHTML = "ABCDE".split("").map(l =>
    `<button data-l="${l}" aria-label="${l}${clean && options[l] ? ": " + esc(options[l]) : ""}"><span class="l">${l}</span>${clean && options[l] ? `<span class="o">${esc(options[l])}</span>` : ""}</button>`).join("");
  if (p.has_image) { if (changed || scan.id !== p.id) loadScan(p, clean); else applyScan(); }
  else { scan = {id: p.id}; applyScan(); }
}

function renderAnswer(s) {
  const a = s.answer;
  document.querySelectorAll("#letters button").forEach(b => {
    b.disabled = !!a || s.busy;
    b.classList.toggle("right", !!a && b.dataset.l === a.label);
    b.classList.toggle("wrong", !!a && b.dataset.l === a.letter && !a.correct);
  });
  $("verdict").textContent = txt(s.message, "text") || (lang === "cat" ? s.message.ca : s.message.en) || "";
  $("feedback").className = "sheet " + (a ? (a.correct ? "ok" : "bad") : "");
  $("next").hidden = !a;
  // the hint button says what the next press gives: a hint (and how many are left) or, as the last use, the lesson
  const left = s.hints_left ?? Infinity, max = s.hints_max ?? 3, lessonLast = max >= 4;
  $("hint").disabled = !!a || s.busy || left <= 0;
  $("hint").title = left <= 0 ? t().no_hints : "";
  $("hint-label").textContent = left <= 0 || !isFinite(left) ? t().hint : (lessonLast && left === 1 ? t().kinds.lesson : `${t().hint} · ${lessonLast ? left - 1 : left}`);
  $("solution").disabled = s.busy || s.hints.some(h => h.kind === "solution");
  $("status").textContent = s.busy ? t().thinking : (a && !s.hints.some(h => h.kind === "solution") ? t().answered : "");
}

function renderHints(s) {
  $("hints").innerHTML = s.hints.map(h => {
    if (h.kind === "lesson") {
      // the last use of the button: a short lesson on the topic, its own card, never timed; it counts as a use like any rung
      return `<article class="lesson"><div class="kind">${esc(t().kinds.lesson)} · ${esc(t().lesson_sub)}</div>` +
        `<h3>${esc(txt(h, "title"))}</h3>${bullets(txt(h, "text"))}</article>`;
    }
    let body = bullets(txt(h, "text"));
    if (h.kind === "neighbour" && h.problem) {
      const np = h.problem, opts = np.options || {}, long = (np.text || "").length > 160;
      body += `<div class="neighbour ${long ? "clamped" : ""}">${esc((np.text || "").replace(/\s*\n\s*/g, " "))}${Object.keys(opts).length ? "\n" + "ABCDE".split("").filter(l => opts[l]).map(l => `${l}) ${esc(opts[l])}`).join("   ") : ""}</div>` +
        (long ? `<button class="more" data-more>${esc(t().more)}</button>` : "") +
        (np.image_b64 ? `<div class="neighbour"><img src="data:image/png;base64,${np.image_b64}" alt=""></div>` : "");
    }
    if (h.kind === "solution" && h.trace && h.trace.length) {
      body += `<ol>${h.trace.map(step => `<li>${esc(txt(step, "text"))}</li>`).join("")}</ol>`;
    }
    const time = h.estimated_board_seconds ? ` · ${t().board} ${h.estimated_board_seconds.toFixed(1)} s` : "";
    const badge = h.kind === "llm" && h.llm_lang === "eng" && lang === "cat" ? `<span class="badge">${esc(t().in_english)}</span>` : "";
    return `<div class="hint ${h.kind}"><div class="kind">${t().kinds[h.kind] || h.kind}${badge}</div>${body}` +
      `<div class="time">${t().laptop} ${(h.laptop_seconds ?? 0).toFixed(2)} s${time}</div></div>`;
  }).join("");
  // the manipulative of the last strategy card, if any
  const manip = [...s.hints].reverse().find(h => h.manipulative);
  $("manip").hidden = !manip || !!s.answer;
  if (manip) { $("manip").textContent = t().manip[manip.manipulative]; $("manip").dataset.m = manip.manipulative; }
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

function renderTopicProgress(s) {
  // the current topic's mastery, 0 to 5, as the big bar at the top with the topic's name: what the pitch points at
  const p = s.problem; if (!p) return;
  const name = lang === "cat" ? p.topic_name_ca : p.topic_name_en, m = s.mastery[p.topic] || 0;
  $("progress-label").textContent = name;
  $("progress-fill").style.width = `${20 * m}%`;
  $("progress-track").setAttribute("aria-valuenow", m);
  $("progress-track").setAttribute("aria-label", `${name} ${m}/5`);
}

function renderTimeline(s) {
  const rows = s.timeline.slice(-6).reverse();
  $("timeline").innerHTML = `<tr><th>${t().action}</th><th>${t().laptop}</th><th>${t().board}</th></tr>` +
    rows.map(r => `<tr><td>${esc(r.action)}</td><td>${r.laptop_s.toFixed(3)} s</td><td class="${r.board_s > 60 ? "over" : ""}">${r.board_s ? r.board_s.toFixed(1) + " s" : "–"}${r.board_s > 60 ? " · " + t().over : ""}</td></tr>`).join("");
}

function render(s) {
  state = s;
  if (lang !== s.lang) { lang = s.lang; applyI18n(); }
  $("start").hidden = s.started; $("app").hidden = !s.started; $("feedback").hidden = !s.started; $("progress").hidden = !s.started;
  $("reset").hidden = !s.started;
  $("who").textContent = s.started ? s.student + (s.level !== null && s.level !== undefined ? ` · ${t().courses[s.level]}` : "") : t().title;
  drawLed(s.led); renderTimeline(s);
  if (!s.started) { if (!loadReported) { loadReported = true; $("load").textContent = `${t().load}: ${Math.round(performance.now() - T0)} ms`; } return; }
  renderProblem(s.problem); renderAnswer(s); renderHints(s); renderMastery(s); renderTopicProgress(s);
  if (s.answer && !hadAnswer && innerWidth < 1000) setPanel(false);
  hadAnswer = !!s.answer;
  if (!loadReported) { loadReported = true; $("load").textContent = `${t().load}: ${Math.round(performance.now() - T0)} ms`; }
}

async function poll() {
  try { render(await api("/api/state")); } catch (e) { $("status").textContent = "…"; }
}

function setPanel(open) { $("panel").hidden = !open; $("more").setAttribute("aria-expanded", String(open)); document.body.classList.toggle("panel-open", open); }
$("more").onclick = () => setPanel($("panel").hidden);
$("letters").addEventListener("click", async e => { const b = e.target.closest("button[data-l]"); if (b && !b.disabled) render(await api("/api/answer/" + b.dataset.l)); });
$("hint").onclick = async () => { await api("/api/hint"); poll(); };
$("solution").onclick = async () => { await api("/api/solution"); poll(); };
$("next").onclick = async () => render(await api("/api/next"));
$("lang-cat").onclick = async () => render(await api("/api/lang/cat"));
$("lang-eng").onclick = async () => render(await api("/api/lang/eng"));
$("begin").onclick = async () => render(await api(`/api/start/${encodeURIComponent($("student").value.trim() || "demo")}/${$("level").value}`));
$("student").addEventListener("keydown", e => { if (e.key === "Enter") $("begin").click(); });
// reset asks twice, inline: the first press turns the button red with the question, the second erases
let resetArmed = null;
$("reset").onclick = async () => {
  if (!resetArmed) { resetArmed = setTimeout(() => { resetArmed = null; $("reset").classList.remove("confirm"); $("reset").textContent = t().reset; }, 4000); $("reset").classList.add("confirm"); $("reset").textContent = t().confirm_reset; return; }
  clearTimeout(resetArmed); resetArmed = null; $("reset").classList.remove("confirm"); $("reset").textContent = t().reset;
  lastProblem = null; $("manip-box").hidden = true; render(await api("/api/reset"));
};
$("hints").addEventListener("click", e => { const b = e.target.closest("button[data-more]"); if (!b) return; const box = b.previousElementSibling; box.classList.toggle("clamped"); b.textContent = box.classList.contains("clamped") ? t().more : t().less; });
$("manip").onclick = () => { const m = $("manip").dataset.m; $("manip-title").textContent = t().manip[m]; $("manip-frame").src = `manip/${m}.html?lang=${lang}${window.Theme ? Theme.query() : ""}`; $("manip-box").hidden = false; $("manip-box").scrollIntoView({behavior: "smooth", block: "nearest"}); };
$("manip-close").onclick = () => { $("manip-box").hidden = true; $("manip-frame").src = "about:blank"; };
// the figure, bigger in its place: useful on a phone
$("figure").onclick = () => { if ($("img").src) $("figure").classList.toggle("zoomed"); };
$("theme").onclick = () => { if (window.Theme) Theme.next(); renderTheme(); };
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !$("panel").hidden) { setPanel(false); return; }
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.metaKey || e.ctrlKey || e.altKey || !state || !state.started) return;
  const k = e.key.toUpperCase();
  if ("ABCDE".includes(k) && k.length === 1) { const b = document.querySelector(`#letters button[data-l="${k}"]`); if (b && !b.disabled) b.click(); }
  else if (k === "P" || k === "H") $("hint").click();
  else if (k === "N" || (e.key === "Enter" && !$("next").hidden)) $("next").click();
});
applyI18n();
poll();
setInterval(poll, 500);
