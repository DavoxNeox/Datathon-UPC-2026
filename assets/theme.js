// Theme switch shared by every page in assets/: auto (follow the system), light or dark.
// The choice lives in localStorage; an iframe (the manipulatives) gets it as ?theme= instead.
// Runs before the page paints so the first frame already has the right colours.
(function () {
  var KEY = "copilot-theme", MODES = ["auto", "light", "dark"];
  function stored() {
    var fromUrl = new URLSearchParams(location.search).get("theme");
    if (MODES.indexOf(fromUrl) > 0) return fromUrl;
    try { var v = localStorage.getItem(KEY); return MODES.indexOf(v) > 0 ? v : "auto"; } catch (e) { return "auto"; }
  }
  function apply(mode) {
    if (mode === "auto") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", mode);
  }
  window.Theme = {
    MODES: MODES,
    get: stored,
    set: function (mode) {
      if (MODES.indexOf(mode) < 0) mode = "auto";
      try { if (mode === "auto") localStorage.removeItem(KEY); else localStorage.setItem(KEY, mode); } catch (e) { /* private mode */ }
      apply(mode);
      return mode;
    },
    next: function () { return window.Theme.set(MODES[(MODES.indexOf(stored()) + 1) % MODES.length]); },
    // the mode a child page (iframe) should be given, as a query parameter
    query: function () { var m = stored(); return m === "auto" ? "" : "&theme=" + m; },
  };
  apply(stored());
})();
