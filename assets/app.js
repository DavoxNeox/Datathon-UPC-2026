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
        more_panel: "Menú", board_led: "La placa", timing: "Temps (per al professor)", problem: "Problema", option: "opció",
        theme: {auto: "Tema: automàtic", light: "Tema: clar", dark: "Tema: fosc"}, no_hints: "Ja no queden pistes en aquest problema",
        read_in: {eng: "Llegeix-lo en anglès", cat: "Llegeix-lo en català"}, hide_other: {eng: "Amaga l'anglès", cat: "Amaga el català"},
        other_kind: {eng: "En anglès · no compta com a pista", cat: "En català · no compta com a pista"},
        show_scan: "veure l'escaneig original", hide_scan: "amagar l'escaneig", original_scan: "Escaneig original",
        no_hints_after: "Aquest servidor no dona pistes després de respondre.",
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
        more_panel: "Menu", board_led: "The board", timing: "Timings (for the teacher)", problem: "Problem", option: "option",
        theme: {auto: "Theme: automatic", light: "Theme: light", dark: "Theme: dark"}, no_hints: "No hints left on this problem",
        read_in: {eng: "Read it in English", cat: "Read it in Catalan"}, hide_other: {eng: "Hide the English", cat: "Hide the Catalan"},
        other_kind: {eng: "In English · not counted as a hint", cat: "In Catalan · not counted as a hint"},
        show_scan: "see the original scan", hide_scan: "hide the scan", original_scan: "Original scan",
        no_hints_after: "This server gives no hints after an answer.",
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
// letters, digits, punctuation and the maths the OCR writes (×, √, π, powers, ≤, ∞, braces); shapes such as △ ○ □ are not text
const CLEAN = /^[\p{L}\p{N}\s.,:;%°€$'"\/+\-=<>!?…×√·—–{}∞≤≥÷*′″＇（）#^_|\[\]~±≠≈π∈→]+$/u;
const NOISY = /\d\s+\d|\p{L}\d\s*$|[²³]\d/u;   // "2 11 cm2", "3cm2", "4cm²2": the OCR stumbled on a fraction or a power
const optionsClean = o => Object.keys(o || {}).length >= 2 && Object.values(o).every(v => v.trim() && CLEAN.test(v) && !NOISY.test(v));
// two habits of the OCR on these scans: a V for a root sign, and a stray letter of the next option at the end
const tidyOption = v => String(v).replace(/V(?=\s?\d)/g, "√").replace(/^(.*\d.*?)\s+[A-E]$/, "$1").trim();

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
  const raw = ink.slice();   // before bridging: the cuts inside an option need the real blanks
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
  return {comps, W, H, ink: raw, cw, ch};
}

// Inside one option of the scan ("A) 15"), the value starts after the first blank gap that follows a
// label-sized run of ink; the cut keeps the value only. Returns the box unchanged when unsure.
function trimLabel(box, ink, cw, lineH) {
  const c0 = Math.floor(box[0] / CELL), c1 = Math.ceil(box[2] / CELL), r0 = Math.floor(box[1] / CELL), r1 = Math.ceil(box[3] / CELL);
  const col = c => { for (let r = r0; r < r1; r++) if (ink[r * cw + c]) return 1; return 0; };
  // the label is the first group of ink runs separated by tiny gaps ("A" and ")"); the value starts after a real gap
  let c = c0; while (c < c1 && !col(c)) c++;
  const s0 = c; let e0 = c;
  while (c < c1) {
    while (c < c1 && col(c)) c++;
    e0 = c; let blank = 0; while (c < c1 && !col(c)) { c++; blank++; }
    if (c >= c1) return box;             // nothing after the label
    if (blank >= 3) break;               // a real gap: the value begins here
  }
  const labelW = (e0 - s0) * CELL;
  if (labelW < 0.6 * lineH || labelW > 3 * lineH) return box;
  return [Math.max(box[0], c * CELL - 4), box[1], box[2], box[3]];
}

function classifyParts(comps, W, H, clean, ink, cw, ch) {
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
  const opt = new Set(), pieces = [];   // the options one by one, in reading order, for the buttons
  const optBands = bands.filter(isOptions).sort((a, b) => a.y0 - b.y0);
  for (const b of optBands) {
    b.items.forEach(c => opt.add(c));
    // a numerator, a superscript or a unit that the band missed: anything small whose middle lies on the row
    for (const c of comps) {
      if (opt.has(c) || c.w >= 0.3 * W || c.h >= 3 * lineH) continue;
      const mid = (c.y0 + c.y1) / 2;
      if (mid >= b.y0 - 0.6 * lineH && mid <= b.y1 + 0.6 * lineH && c.x0 >= b.items[0].x0 - 2 * lineH) { b.items.push(c); opt.add(c); b.y0 = Math.min(b.y0, c.y0); b.y1 = Math.max(b.y1, c.y1); }
    }
    const merged = [];
    for (const c of [...b.items].sort((a, b) => a.x0 - b.x0)) {
      if (merged.length && c.x0 - merged[merged.length - 1].x1 < 1.2 * lineH) merged[merged.length - 1].x1 = Math.max(merged[merged.length - 1].x1, c.x1);
      else merged.push({x0: c.x0, x1: c.x1});
    }
    merged.forEach(m => pieces.push([Math.max(0, m.x0 - 4), Math.max(0, b.y0 - 4), Math.min(W, m.x1 + 4), Math.min(H, b.y1 + 4)]));
  }
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
  // five options in the scan and none readable: each one goes on its button, without its letter
  let perButton = !clean && ob && pieces.length === 5 ? pieces.map(b => trimLabel(b, ink, cw, lineH)).map(b => ({box: b, mask: null})) : null;
  // options drawn as pictures: five letters each next to its own picture (left of it or under it), or bridged into it
  if (!clean && !perButton) {
    const labels = comps.filter(c => textlike(c) && !stmt.has(c) && c.w >= 0.5 * lineH && c.w <= 2.2 * lineH);
    const bigs = figure.filter(c => !textlike(c) && c.w * c.h >= (1.5 * lineH) ** 2);
    const mid = c => (c.y0 + c.y1) / 2, pics = [];
    for (const l of labels) {
      const right = bigs.filter(c => c.y0 < l.y1 + lineH && c.y1 > l.y0 - lineH && c.x0 - l.x1 >= -0.3 * lineH && c.x0 - l.x1 <= 2.5 * lineH)
        .sort((a, b) => (a.x0 - l.x1 + Math.abs(mid(a) - mid(l))) - (b.x0 - l.x1 + Math.abs(mid(b) - mid(l))));
      const above = bigs.filter(c => c.x0 < l.x1 + lineH && c.x1 > l.x0 - lineH && l.y0 - c.y1 >= -0.3 * lineH && l.y0 - c.y1 <= 1.5 * lineH)
        .sort((a, b) => (l.y0 - a.y1) - (l.y0 - b.y1));
      const pic = right[0] || above[0];
      if (pic) pics.push({at: l, pic, mask: null});
    }
    const taken = new Set(pics.map(p => p.pic));
    for (const c of bigs) {
      if (taken.has(c)) continue;
      const m = labelRect(c, ink, cw, ch, lineH);
      if (m) pics.push({at: {y0: m[1], x0: m[0]}, pic: c, mask: m});
    }
    if (pics.length === 5 && new Set(pics.map(p => p.pic)).size === 5) {
      pics.sort((a, b) => Math.round(a.at.y0 / (2 * lineH)) - Math.round(b.at.y0 / (2 * lineH)) || a.at.x0 - b.at.x0);
      perButton = pics.map(p => ({box: [Math.max(0, p.pic.x0 - 6), Math.max(0, p.pic.y0 - 6), Math.min(W, p.pic.x1 + 6), Math.min(H, p.pic.y1 + 6)], mask: p.mask}));
      const used = new Set([...pics.map(p => p.pic), ...pics.map(p => p.at)]);
      fb = bbox(figure.filter(c => !used.has(c)), 8);
      if (fb && (fb[2] - fb[0]) * (fb[3] - fb[1]) < (2 * lineH) ** 2) fb = null;
      ob = null;
    }
  }
  return {figure: fb, options: perButton ? null : ob, pieces: perButton, statement: bbox([...stmt], 0)};
}

function cropPart(img, box, masks) {
  const c = document.createElement("canvas"); c.width = box[2] - box[0]; c.height = box[3] - box[1];
  const ctx = c.getContext("2d");
  ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, c.width, c.height);
  ctx.drawImage(img, box[0], box[1], c.width, c.height, 0, 0, c.width, c.height);
  for (const m of masks) if (m) ctx.fillRect(m[0] - box[0], m[1] - box[1], m[2] - m[0], m[3] - m[1]);   // the text the page already shows
  return c;
}

// The scans are black on white. On the page the white goes: every pixel becomes ink with the alpha of its
// darkness. Strokes and the edges of shapes take the theme's ink colour, so lines read on a dark page;
// the inside of a filled shape (dark pixels with dark neighbours 3 px away in every direction) keeps its
// own colour, so "the black square" stays black and grey stays grey, with a light rim around it. A
// saturated colour keeps its hue (lightened in the dark theme). The light theme tints the same way:
// black ink on the warm page. No white card anywhere.
const cssVar = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const hexRgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
function isDarkTheme() { const [br, bg, bb] = hexRgb(cssVar("--bg") || "#ffffff"); return br * 299 + bg * 587 + bb * 114 < 128000; }
function tinted(raw) {
  const [ir, ig, ib] = hexRgb(cssVar("--ink") || "#1f2430"), dark = isDarkTheme();
  const w = raw.width, h = raw.height;
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const ctx = c.getContext("2d"); ctx.drawImage(raw, 0, 0);
  const im = ctx.getImageData(0, 0, w, h), d = im.data;
  const darkAt = (x, y) => x >= 0 && y >= 0 && x < w && y < h && Math.min(d[4 * (y * w + x)], d[4 * (y * w + x) + 1], d[4 * (y * w + x) + 2]) < 110;
  const out = new Uint8ClampedArray(d.length);
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = 4 * (y * w + x), r = d[i], g = d[i + 1], b = d[i + 2], mn = Math.min(r, g, b), mx = Math.max(r, g, b);
    const darkness = 255 - mn;   // 0 on white; the scan's faint noise (under 60) goes, ink reaches full by 170
    const a = darkness < 60 ? 0 : Math.min(255, Math.round((darkness - 60) * 255 / 110));
    out[i + 3] = Math.min(d[i + 3], a);
    if (!a) continue;
    const interior = dark && mn < 110 && darkAt(x - 3, y) && darkAt(x + 3, y) && darkAt(x, y - 3) && darkAt(x, y + 3);
    if (interior) { out[i] = r; out[i + 1] = g; out[i + 2] = b; out[i + 3] = 255; }   // a fill keeps its colour, black stays black
    else if (mx - mn < 40) { out[i] = ir; out[i + 1] = ig; out[i + 2] = ib; }         // strokes and edges in the theme's ink
    else if (dark) { out[i] = r + (255 - r) * .4; out[i + 1] = g + (255 - g) * .4; out[i + 2] = b + (255 - b) * .4; }
    else { out[i] = r; out[i + 1] = g; out[i + 2] = b; }
  }
  im.data.set(out); ctx.putImageData(im, 0, 0);
  return c.toDataURL("image/png");
}

function extractParts(img, clean) {
  const {comps, W, H, ink, cw, ch} = scanComponents(img);
  const parts = classifyParts(comps, W, H, clean, ink, cw, ch);
  return {
    figure: parts.figure ? cropPart(img, parts.figure, [parts.statement, parts.options]) : null,
    options: parts.options ? cropPart(img, parts.options, []) : null,
    pieces: parts.pieces ? parts.pieces.map(p => cropPart(img, p.box, [p.mask])) : null,
  };
}

const toCanvas = img => { const c = document.createElement("canvas"); c.width = img.naturalWidth; c.height = img.naturalHeight; c.getContext("2d").drawImage(img, 0, 0); return c; };
// one scan per problem: fetched once, cut once, then reused on every poll
let scan = {id: null, figure: null, options: null, pieces: null, whole: null, full: null, showFull: false, colours: false};
function loadScan(p, clean) {
  scan = {id: p.id, figure: null, options: null, pieces: null, whole: null, full: null, showFull: false,
        };
  api("/api/image").then(r => {
    if (!r.image_b64 || scan.id !== p.id) return;
    const img = new Image();
    img.onload = () => {
      if (scan.id !== p.id) return;
      scan.full = toCanvas(img);
      try { Object.assign(scan, extractParts(img, clean)); }
      catch (e) { scan.whole = scan.full; }   // anything odd: the whole scan, as before
      if (!scan.figure && !scan.options && !scan.pieces && !clean) scan.whole = scan.full;   // nothing found but the options are unreadable: show the scan
      applyScan();
    };
    img.src = "data:image/png;base64," + r.image_b64;
  });
}
const setSrc = (img, url) => { if (!url) img.removeAttribute("src"); else if (img.getAttribute("src") !== url) img.src = url; };
function applyScan() {
  // tinted once per theme, then reused on every poll
  const key = cssVar("--bg");
  if (scan.tintKey !== key) {
    const fig = scan.figure || scan.whole;
    scan.tinted = {figure: fig ? tinted(fig) : "", options: scan.options ? tinted(scan.options) : "", pieces: (scan.pieces || []).map(tinted), full: ""};
    scan.tintKey = key;
  }
  const tt = scan.tinted || {figure: "", options: "", pieces: [], full: ""};
  $("fig-cap").hidden = !scan.whole;   // the whole scan stands in for a figure: say so
  // the whole scan, one click away (not offered when the page already fell back to it)
  const canToggle = !!scan.full && !scan.whole;
  $("whole-toggle").hidden = !canToggle; $("whole-toggle").textContent = scan.showFull ? t().hide_scan : t().show_scan;
  if (scan.showFull && canToggle && !tt.full) tt.full = tinted(scan.full);
  $("whole").hidden = !(scan.showFull && canToggle); setSrc($("whole-img"), scan.showFull && canToggle ? tt.full : "");
  $("whole-img").alt = t().image;
  $("figure").hidden = !tt.figure; setSrc($("img"), tt.figure);
  $("img").onload = fitFigure;
  $("strip").hidden = !tt.options; setSrc($("strip-img"), tt.options);
  $("img").alt = t().image; $("strip-img").alt = t().options_image;
  // the answers themselves on the buttons, when the scan had them and the OCR did not
  document.querySelectorAll("#letters button").forEach((b, i) => {
    const pic = b.querySelector(".pic");
    if (tt.pieces[i]) {
      const img = pic || b.appendChild(Object.assign(document.createElement("img"), {className: "pic"}));
      const label = (b.getAttribute("aria-label") || "").split(": ")[1];
      img.alt = label || `${t().option} ${b.dataset.l}`;
      setSrc(img, tt.pieces[i]);
    }
    else if (pic) pic.remove();
  });
  $("letters").classList.toggle("pics", tt.pieces.length > 0);
}
// the neighbour problem's picture, tinted the same way, once per problem
const tintCache = new Map();
function tintedHintImage(key, b64) {
  if (tintCache.has(key)) return tintCache.get(key);
  tintCache.set(key, "");
  const img = new Image(); img.onload = () => tintCache.set(key, tinted(toCanvas(img))); img.src = "data:image/png;base64," + b64;
  return "";
}
function retint() { tintCache.clear(); scan.tintKey = null; if (state && state.started) { applyScan(); renderHints(state); } }
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", retint);

// The figure never grows past the question: its height is the text's height (and at most a third of the
// window, and at most 1.25 times its own size); the CSS keeps it under 30 % of the column. On a phone it
// sits above the text at its natural size. Measured twice, because the text wraps around the figure.
function fitFigure() {
  const img = $("img");
  if (!img.naturalWidth || $("figure").hidden) return;
  if (matchMedia("(max-width: 640px)").matches || $("figure").classList.contains("zoomed")) { img.style.height = ""; return; }
  const once = () => {
    const textH = $("text").getBoundingClientRect().height, nw = img.naturalWidth, nh = img.naturalHeight;
    const tall = nh / nw > 1.2;   // a tall, narrow figure (a hand, a tower) under a short question would become a thumbnail
    let h = Math.min(tall ? Infinity : Math.max(90, textH), innerHeight * 0.34, nh * 1.25);
    // never under a fifth of the column, unless the crop itself is smaller than that
    const minW = Math.min(0.2 * $("app").getBoundingClientRect().width, nw * 1.25);
    h = Math.min(Math.max(h, minW * nh / nw), innerHeight * 0.34);
    img.style.height = `${Math.round(h)}px`;
  };
  once(); requestAnimationFrame(once);
}
addEventListener("resize", fitFigure);

function renderProblem(p) {
  if (!p) { $("text").textContent = ""; return; }
  const changed = !lastProblem || lastProblem.id !== p.id;
  if (changed) { $("manip-box").hidden = true; $("manip-frame").src = "about:blank"; $("figure").classList.remove("zoomed"); }
  lastProblem = p;
  // the scan's line breaks go; a blank line stays a paragraph; the problem's number goes (the page is not a paper)
  const text = ((lang === "eng" && p.text_eng) || (lang === "cat" && p.text_cat) || p.text || "").replace(/^\s*\d+[.)]\s*/, "").replace(/\n{2,}/g, "\u2029").replace(/\s*\n\s*/g, " ").replace(/\u2029/g, "\n\n");
  const raw = (lang === "eng" && p.options_eng) || (lang === "cat" && p.options_cat) || p.options || {};
  const options = Object.fromEntries(Object.entries(raw).map(([k, v]) => [k, tidyOption(v)]));
  const clean = optionsClean(options);
  $("meta").textContent = `${t().level} ${p.level} · ${t().courses[p.level] || ""} · ${lang === "cat" ? p.topic_name_ca : p.topic_name_en}`;
  $("problem-id").textContent = `${t().problem}: ${p.id}`;
  if ($("text").textContent !== text) { $("text").textContent = text; requestAnimationFrame(fitFigure); }
  const short = clean && Object.values(options).every(v => v.length <= 10);   // "42 cm", "3√2 cm": one row; sentences: one per row
  $("letters").classList.toggle("rows", clean && !short);
  $("letters").classList.toggle("short", short);
  const readable = v => v && CLEAN.test(v) && !NOISY.test(v);   // an option the OCR read well, usable as a label even when the picture is shown
  if (changed || $("letters").dataset.lang !== lang) $("letters").innerHTML = "ABCDE".split("").map(l =>
    `<button data-l="${l}" aria-label="${l}${readable(options[l]) ? ": " + esc(options[l]) : ""}"><span class="l">${l}</span>${clean && options[l] ? `<span class="o">${esc(options[l])}</span>` : ""}</button>`).join("");
  $("letters").dataset.lang = lang;
  if (p.has_image) { if (changed || scan.id !== p.id) loadScan(p, clean); else applyScan(); }
  else { scan = {id: p.id}; applyScan(); }
}

function renderTranslation(s) {
  // rung 0: the same problem in the other language, under the statement; never its label; no use spent
  const other = s.other_language, tr = s.translation;
  $("translate").hidden = !s.translation_available;
  if (s.translation_available) { $("translate").textContent = tr ? t().hide_other[other] : t().read_in[other]; $("translate").classList.toggle("on", !!tr); }
  $("other").hidden = !tr;
  if (!tr) return;
  $("other-kind").textContent = t().other_kind[tr.language];
  $("other-text").textContent = (tr.text || "").replace(/^\s*\d+[.)]\s*/, "").replace(/\s*\n\s*/g, " ");
  const opts = tr.options || {};
  $("other-options").textContent = "ABCDE".split("").filter(l => opts[l]).map(l => `${l}) ${tidyOption(opts[l])}`).join("   ");
}

function renderAnswer(s) {
  const a = s.answer;
  document.querySelectorAll("#letters button").forEach(b => {
    b.disabled = !!a || s.busy;
    b.classList.toggle("right", !!a && b.dataset.l === a.label);
    b.classList.toggle("wrong", !!a && b.dataset.l === a.letter && !a.correct);
  });
  // the verdict stays on the sheet while the problem is open, even when a later hint clears the server's message
  const msg = txt(s.message, "text") || (lang === "cat" ? s.message.ca : s.message.en) || "";
  if (msg || !a) verdictKept = {id: s.problem && s.problem.id, lang, text: msg};
  $("verdict").textContent = msg || (verdictKept.id === (s.problem && s.problem.id) && verdictKept.lang === lang ? verdictKept.text : "");
  $("feedback").className = "sheet " + (a ? (a.correct ? "ok" : "bad") : "");
  const solved = s.hints.some(h => h.kind === "solution");
  $("next").hidden = !(a || solved);
  $("hint").hidden = solved; $("solution").hidden = solved || !!a;   // answered: the right button itself offers the next step
  // the hint button says what the next press gives: a hint (and how many are left) or, as the last use, the lesson
  const left = s.hints_left ?? Infinity, max = s.hints_max ?? 3, lessonLast = max >= 4;
  // the right button: a hint while there are some (also after the answer: it still teaches), else the solution
  const hintLabel = left <= 0 || !isFinite(left) ? t().hint : (lessonLast && left === 1 ? t().kinds.lesson : `${t().hint} · ${lessonLast ? left - 1 : left}`);
  const offerSolution = !!a && left <= 0;
  $("hint").disabled = s.busy || (!a && left <= 0);
  $("hint").title = !a && left <= 0 ? t().no_hints : "";
  $("hint").dataset.role = offerSolution ? "solution" : "hint";
  $("hint-label").textContent = offerSolution ? t().solution : hintLabel;
  $("solution").disabled = s.busy || s.hints.some(h => h.kind === "solution");
  $("status").textContent = s.busy ? t().thinking : (a && !solved ? t().answered : "");
}

const expanded = new Set();   // "mostra-ho tot" pressed, by problem and hint index
let scrolledSolution = null;   // the problem whose solution the page already scrolled to
let verdictKept = {id: null, lang: null, text: ""};   // the last verdict shown, per problem and language
let hintsSig = "";
function renderHints(s) {
  const pid = s.problem ? s.problem.id : "";
  const sig = JSON.stringify([pid, lang, cssVar("--bg"), s.hints.map((h, i) => [h.kind, h.rung, txt(h, "text"), h.problem && h.problem.id, h.problem && tintCache.get(h.problem.id || h.rung) ? 1 : 0, expanded.has(pid + ":" + i)])]);
  if (sig !== hintsSig) {
    hintsSig = sig; $("hints").innerHTML = hintsHtml(s, pid);
    const sol = $("hints").querySelector(".hint.solution");
    if (sol && scrolledSolution !== pid) { scrolledSolution = pid; sol.scrollIntoView({behavior: "smooth", block: "start"}); }
  }
  // the manipulative of the last strategy card, if any
  const manip = [...s.hints].reverse().find(h => h.manipulative);
  $("manip").hidden = !manip || !!s.answer;
  if (manip) { $("manip").textContent = t().manip[manip.manipulative]; $("manip").dataset.m = manip.manipulative; }
}
function hintsHtml(s, pid) {
  return s.hints.map((h, i) => {
    if (h.kind === "lesson") {
      // the last use of the button: a short lesson on the topic, its own card, never timed; it counts as a use like any rung
      return `<article class="lesson"><div class="kind">${esc(t().kinds.lesson)} · ${esc(t().lesson_sub)}</div>` +
        `<h3>${esc(txt(h, "title"))}</h3>${bullets(txt(h, "text"))}</article>`;
    }
    // the solution's text repeats its steps: keep its first sentence (the option) and the numbered steps
    const hasTrace = h.kind === "solution" && h.trace && h.trace.length;
    let body = hasTrace ? `<p>${esc(txt(h, "text").split(/(?<=[.!?])\s+/)[0])}</p>` : bullets(txt(h, "text"));
    if (h.kind === "neighbour" && h.problem) {
      const np = h.problem, opts = np.options || {}, long = (np.text || "").length > 160 && !expanded.has(pid + ":" + i);
      body += `<div class="neighbour ${long ? "clamped" : ""}">${esc((np.text || "").replace(/\s*\n\s*/g, " "))}${Object.keys(opts).length ? "\n" + "ABCDE".split("").filter(l => opts[l]).map(l => `${l}) ${esc(opts[l])}`).join("   ") : ""}</div>` +
        ((np.text || "").length > 160 ? `<button class="more" data-more="${i}">${esc(long ? t().more : t().less)}</button>` : "") +
        (np.image_b64 && tintedHintImage(np.id || h.rung, np.image_b64) ? `<div class="neighbour pic"><img src="${tintedHintImage(np.id || h.rung, np.image_b64)}" alt=""></div>` : "");
    }
    if (h.kind === "solution" && h.trace && h.trace.length) {
      body += `<ol>${h.trace.map(step => `<li>${esc(txt(step, "text"))}</li>`).join("")}</ol>`;
    }
    const time = h.estimated_board_seconds ? ` · ${t().board} ${h.estimated_board_seconds.toFixed(1)} s` : "";
    const badge = h.kind === "llm" && h.llm_lang === "eng" && lang === "cat" ? `<span class="badge">${esc(t().in_english)}</span>` : "";
    return `<div class="hint ${h.kind}"><div class="kind">${t().kinds[h.kind] || h.kind}${badge}</div>${body}` +
      `<div class="time">${t().laptop} ${(h.laptop_seconds ?? 0).toFixed(2)} s${time}</div></div>`;
  }).join("");
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
  drawLed(s.led); renderTimeline(s); renderMastery(s);   // also on the start screen, so a reset empties the map
  if (!s.started) { if (!loadReported) { loadReported = true; $("load").textContent = `${t().load}: ${Math.round(performance.now() - T0)} ms`; } return; }
  renderProblem(s.problem); renderTranslation(s); renderAnswer(s); renderHints(s); renderMastery(s); renderTopicProgress(s);
  if (s.answer && !hadAnswer) setPanel(false);
  hadAnswer = !!s.answer;
  if (!loadReported) { loadReported = true; $("load").textContent = `${t().load}: ${Math.round(performance.now() - T0)} ms`; }
}

async function poll() {
  try { render(await api("/api/state")); } catch (e) { $("status").textContent = "…"; }
}

// The settings popup: opened from the menu icon, closed with its X, Escape or a click on the scrim.
// Focus moves into the card and comes back to the icon, so it works the same from the keyboard.
function setPanel(open) {
  if (open === !$("panel").hidden) return;
  $("panel").hidden = !open; $("more").setAttribute("aria-expanded", String(open));
  if (open) $("panel-close").focus(); else if (document.activeElement && $("panel").contains(document.activeElement)) $("more").focus();
}
$("more").onclick = () => setPanel($("panel").hidden);
$("panel-close").onclick = () => setPanel(false);
$("panel").addEventListener("pointerdown", e => { if (e.target === $("panel")) setPanel(false); });
$("letters").addEventListener("click", async e => { const b = e.target.closest("button[data-l]"); if (b && !b.disabled) render(await api("/api/answer/" + b.dataset.l)); });
const pressed = b => { b.disabled = true; $("status").textContent = t().thinking; };
$("translate").onclick = async () => render(await api("/api/translate/" + (state && state.translation ? "hide" : "show")));
$("whole-toggle").onclick = () => { scan.showFull = !scan.showFull; applyScan(); };
$("hint").onclick = async () => {
  pressed($("hint"));
  if ($("hint").dataset.role === "solution") { await api("/api/solution"); return poll(); }
  const r = await api("/api/hint");
  if (r.error === "already answered") $("status").textContent = t().no_hints_after;   // an old server: say so, never show the solution unasked
  poll();
};
$("solution").onclick = async () => { pressed($("solution")); await api("/api/solution"); poll(); };
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
$("hints").addEventListener("click", e => { const b = e.target.closest("button[data-more]"); if (!b || !state) return; const key = (state.problem ? state.problem.id : "") + ":" + b.dataset.more; if (expanded.has(key)) expanded.delete(key); else expanded.add(key); renderHints(state); });
$("manip").onclick = () => { const m = $("manip").dataset.m; $("manip-title").textContent = t().manip[m]; $("manip-frame").src = `manip/${m}.html?lang=${lang}${window.Theme ? Theme.query() : ""}`; $("manip-box").hidden = false; $("manip-box").scrollIntoView({behavior: "smooth", block: "nearest"}); };
$("manip-close").onclick = () => { $("manip-box").hidden = true; $("manip-frame").src = "about:blank"; };
// the figure, bigger in its place: useful on a phone
$("figure").onclick = () => { if ($("img").src) { $("figure").classList.toggle("zoomed"); fitFigure(); } };
$("theme").onclick = () => { if (window.Theme) Theme.next(); renderTheme(); retint(); };
document.addEventListener("keydown", e => {
  if (e.key === "Escape" && !$("panel").hidden) { setPanel(false); return; }
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.metaKey || e.ctrlKey || e.altKey || !state || !state.started) return;
  const k = e.key.toUpperCase();
  if ("ABCDE".includes(k) && k.length === 1) { const b = document.querySelector(`#letters button[data-l="${k}"]`); if (b && !b.disabled) b.click(); }
  else if (k === "P" || k === "H") $("hint").click();
  else if (k === "T" && !$("translate").hidden) $("translate").click();
  else if (k === "N" || (e.key === "Enter" && !$("next").hidden)) $("next").click();
});
applyI18n();
poll();
setInterval(poll, 500);
