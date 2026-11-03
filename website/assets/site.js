/* Gripsack site behavior: palette picker and locally bundled Prism.
   Palettes are pure CSS (html[data-palette] blocks in site.css);
   the saved choice and syntax colors stay independent of source text. */
(function () {
  var KEY = "gripsack-palette";
  var DEFAULT = "paper";
  var pickers = document.querySelectorAll("[data-palette-select]");

  function apply(name) {
    var valid = pickers.length && Array.prototype.some.call(pickers[0].options, function (option) {
      return option.value === name;
    });
    name = valid ? name : DEFAULT;
    document.documentElement.setAttribute("data-palette", name);
    for (var i = 0; i < pickers.length; i++) pickers[i].value = name;
  }

  var stored = null;
  try { stored = localStorage.getItem(KEY); } catch (e) { /* private mode */ }
  apply(stored);
  for (var i = 0; i < pickers.length; i++) {
    pickers[i].closest("label").hidden = false;
    pickers[i].addEventListener("change", function () {
      apply(this.value);
      try { localStorage.setItem(KEY, this.value); } catch (e) { /* private mode */ }
    });
  }
  window.addEventListener("storage", function (event) {
    if (event.key === KEY) apply(event.newValue);
  });

  // Native disclosure remains expanded and usable when JavaScript is disabled.
  var menu = document.querySelector(".docs-menu");
  if (menu) {
    var narrow = window.matchMedia("(max-width: 880px)");
    function sizeMenu() { menu.open = !narrow.matches; }
    sizeMenu();
    narrow.addEventListener("change", sizeMenu);
  }

  // Deferred scripts run after parsing; absent highlighting leaves readable code.
  if (window.Prism) window.Prism.highlightAll();
})();

