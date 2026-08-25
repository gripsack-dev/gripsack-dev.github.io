/* gripsack site behavior: palette picker + copy buttons.
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
      buttons[i].classList.toggle(
        "active",
        buttons[i].getAttribute("data-set-palette") === (name || DEFAULT)
      );
    }
    /* the readout on docs rails is plain text — keep it in sync too */
    var labels = document.querySelectorAll("[data-palette-name]");
    for (var j = 0; j < labels.length; j++) {
      labels[j].textContent = name || DEFAULT;
    }
    /* theme-reactive demo: one GIF per palette (rendered by the app
       repo's demo workflow); unknown/missing variants fall back to the
       default render */
    var demo = document.querySelector("[data-demo-img]");
    if (demo) {
      var base = demo.getAttribute("data-demo-base") || "./img/demo";
      var src = name && name !== DEFAULT ? base + "-" + name + ".gif" : base + ".gif";
      if (demo.getAttribute("src") !== src) {
        demo.onerror = function () {
          demo.onerror = null;
          demo.src = base + ".gif";
        };
        demo.src = src;
      }
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
    var copy = target.closest ? target.closest("[data-copy]") : null;
    if (copy) {
      var text = copy.getAttribute("data-copy");
      var done = function () {
        var label = copy.textContent;
        copy.textContent = "copied";
        copy.classList.add("ok");
        setTimeout(function () {
          copy.textContent = label;
          copy.classList.remove("ok");
        }, 1200);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, done);
      } else {
        var ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); } catch (e) {}
        ta.remove();
        done();
      }
    }
  });
})();

/* syntax highlighting: a tiny tokenizer for the handful of languages the
   site shows — no library, no CDN. Runs over pre > code.language-* (the
   docs pages' fenced blocks; home-page snippets are hand-spanned and have
   no <code>, so they're untouched). Token colors are the pre .k/.s/.f/.n/.c
   rules in site.css, so highlighting re-themes with the palette picker. */
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

/* code tabs: [data-tab] toggles the sibling [data-pane] panels */
document.addEventListener("click", function (ev) {
  var btn = ev.target.closest ? ev.target.closest("[data-tab]") : null;
  if (!btn) return;
  var bar = btn.parentElement;
  var win = bar.closest(".window") || bar.parentElement;
  var name = btn.getAttribute("data-tab");
  bar.querySelectorAll("[data-tab]").forEach(function (b) {
    b.classList.toggle("active", b === btn);
  });
  win.querySelectorAll("[data-pane]").forEach(function (p) {
    p.hidden = p.getAttribute("data-pane") !== name;
  });
});
