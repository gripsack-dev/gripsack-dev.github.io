/* gripsack site behavior: palette picker and local syntax highlighting.
   Palettes are pure CSS (html[data-palette] blocks in site.css); this
   script only sets the attribute and persists the choice. No deps. */
(function () {
  var KEY = "gripsack-palette";
  var DEFAULT = "catppuccin-mocha";

  function apply(name) {
    if (name && name !== DEFAULT) {
      document.documentElement.setAttribute("data-palette", name);
    } else {
      document.documentElement.removeAttribute("data-palette");
    }
    var buttons = document.querySelectorAll("[data-set-palette]");
    for (var i = 0; i < buttons.length; i++) {
      var selected = buttons[i].getAttribute("data-set-palette") === (name || DEFAULT);
      buttons[i].classList.toggle("active", selected);
      buttons[i].setAttribute("aria-pressed", String(selected));
    }
    /* the readout on docs rails is plain text — keep it in sync too */
    var labels = document.querySelectorAll("[data-palette-name]");
    for (var j = 0; j < labels.length; j++) {
      labels[j].textContent = name || DEFAULT;
    }
  }

  var stored = null;
  try { stored = localStorage.getItem(KEY); } catch (e) { /* private mode */ }
  apply(stored);

  document.addEventListener("click", function (ev) {
    var target = ev.target;
    var pal = target.closest ? target.closest("[data-set-palette]") : null;
    if (pal) {
      var name = pal.getAttribute("data-set-palette");
      apply(name);
      try { localStorage.setItem(KEY, name === DEFAULT ? "" : name); } catch (e) {}
      return;
    }
  });
})();

/* syntax highlighting: a tiny tokenizer for the handful of languages the
   site shows — no library, no CDN. Runs over pre > code.language-* on
   documentation pages and the homepage. Token colors follow the palette. */
(function () {
  var DEFS = {
    python: [
      ["c", /#[^\n]*/],
      ["s", /[rubfRUBF]{0,2}"""[\s\S]*?"""|[rubfRUBF]{0,2}'''[\s\S]*?'''|[rubfRUBF]{0,2}"(?:\\.|[^"\\\n])*"|[rubfRUBF]{0,2}'(?:\\.|[^'\\\n])*'/],
      ["f", /@[\w.]+/],
      ["k", /\b(?:from|import|def|class|return|if|elif|else|for|while|in|not|and|or|is|None|True|False|with|as|lambda|raise|try|except|finally|pass|yield|async|await|break|continue)\b/],
      ["n", /\b\d[\d_]*(?:\.\d+)?\b/],
      ["f", /[A-Za-z_]\w*(?=\()/]
    ],
    toml: [
      ["c", /#[^\n]*/],
      ["s", /"(?:\\.|[^"\\\n])*"|'[^'\n]*'/],
      ["f", /\[\[?[\w.\-]+\]?\]/],
      ["k", /\b(?:true|false)\b/],
      ["n", /\b\d[\d_]*(?:\.\d+)?\b/]
    ],
    typescript: [
      ["c", /\/\/[^\n]*|\/\*[\s\S]*?\*\//],
      ["s", /"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\]|\$\{[^}]*\})*`/],
      ["k", /\b(?:import|from|export|const|let|var|function|return|if|else|new|class|extends|type|interface|async|await|of|in|typeof|true|false|null|undefined)\b/],
      ["n", /\b\d[\d_]*(?:\.\d+)?\b/],
      ["f", /[A-Za-z_$][\w$]*(?=\()/]
    ],
    json: [
      ["s", /"(?:\\.|[^"\\])*"/],
      ["k", /\b(?:true|false|null)\b/],
      ["n", /-?\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b/]
    ],
    bash: [
      ["c", /#[^\n]*/],
      ["s", /"(?:\\.|[^"\\])*"|'[^']*'/],
      ["n", /(?:^|[ \t])--?[a-zA-Z][\w-]*/],
      ["f", /^[ \t]*[a-zA-Z_][\w.:-]*/]
    ],
    diag: [
      ["err", /error\[[^\]\n]+\]/],
      ["s", /"(?:\\.|[^"\\\n])*"|'[^'\n]*'/],
      ["loc", /-->|\S+\.\w+:\d+:\d+/]
    ]
  };
  DEFS.javascript = DEFS.typescript;

  function esc(t) {
    return t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function highlight(codeEl) {
    var m = /language-(\w+)/.exec(codeEl.className);
    if (!m) return;
    var def = DEFS[m[1]];
    if (!def) return;
    var re = new RegExp(
      def.map(function (r) { return "(" + r[1].source + ")"; }).join("|"),
      "gm"
    );
    var text = codeEl.textContent, out = "", last = 0, match;
    while ((match = re.exec(text)) !== null) {
      if (match[0] === "") { re.lastIndex++; continue; }
      out += esc(text.slice(last, match.index));
      for (var g = 0; g < def.length; g++) {
        if (match[g + 1] !== undefined) {
          out += '<span class="' + def[g][0] + '">' + esc(match[0]) + "</span>";
          break;
        }
      }
      last = re.lastIndex;
    }
    codeEl.innerHTML = out + esc(text.slice(last));
  }

  document.querySelectorAll("pre > code").forEach(highlight);
})();

