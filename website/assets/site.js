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
