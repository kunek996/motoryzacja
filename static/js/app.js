// TuneHub – progressive enhancement only. Everything works without JS.
(function () {
  "use strict";

  // Long filter panels start collapsed on phones (unless a filter is active).
  if (window.matchMedia("(max-width: 860px)").matches && !/[?&](q|make|car_model|category|fuel|stage|language)=[^&]/.test(location.search)) {
    document.querySelectorAll("details[data-collapse-mobile]").forEach(function (d) { d.removeAttribute("open"); });
  }

  // Language switcher: submit on change.
  document.querySelectorAll("[data-autosubmit]").forEach(function (el) {
    el.addEventListener("change", function () { el.form.submit(); });
  });

  // Confirmation for destructive forms: <form data-confirm="Are you sure?">
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // Close open dropdown menus when clicking elsewhere.
  document.addEventListener("click", function (e) {
    document.querySelectorAll("details.menu[open]").forEach(function (d) {
      if (!d.contains(e.target)) d.removeAttribute("open");
    });
  });

  // Dependent make -> model select (filters).
  document.querySelectorAll("select[data-models-url]").forEach(function (makeSelect) {
    var target = document.getElementById(makeSelect.dataset.modelsTarget);
    if (!target) return;
    makeSelect.addEventListener("change", function () {
      var first = target.options[0] ? target.options[0].cloneNode(true) : null;
      target.innerHTML = "";
      if (first) { first.selected = true; target.appendChild(first); }
      if (!makeSelect.value) return;
      fetch(makeSelect.dataset.modelsUrl + "?make=" + encodeURIComponent(makeSelect.value), { credentials: "same-origin" })
        .then(function (r) { return r.ok ? r.json() : { models: [] }; })
        .then(function (data) {
          data.models.forEach(function (m) {
            var opt = document.createElement("option");
            opt.value = m.id;
            opt.textContent = m.label;
            target.appendChild(opt);
          });
        })
        .catch(function () {});
    });
  });

  // Inline formset: "add parameter" button clones the empty form template.
  document.querySelectorAll("[data-formset]").forEach(function (box) {
    var prefix = box.dataset.formset;
    var total = document.getElementById("id_" + prefix + "-TOTAL_FORMS");
    var max = document.getElementById("id_" + prefix + "-MAX_NUM_FORMS");
    var tpl = box.querySelector("template");
    var rows = box.querySelector("[data-rows]");
    var add = box.querySelector("[data-add-row]");
    if (!total || !tpl || !rows || !add) return;
    add.addEventListener("click", function () {
      var n = parseInt(total.value, 10);
      if (max && n >= parseInt(max.value, 10)) return;
      var html = tpl.innerHTML.replace(/__prefix__/g, String(n));
      rows.insertAdjacentHTML("beforeend", html);
      total.value = String(n + 1);
      var inputs = rows.lastElementChild && rows.lastElementChild.querySelectorAll("input");
      if (inputs && inputs[0]) inputs[0].focus();
    });
  });

  // Show selected file names for multi-file inputs.
  document.querySelectorAll("input[type=file][multiple]").forEach(function (input) {
    var out = document.createElement("div");
    out.className = "helptext";
    input.insertAdjacentElement("afterend", out);
    input.addEventListener("change", function () {
      out.textContent = Array.prototype.map.call(input.files, function (f) {
        return f.name + " (" + Math.ceil(f.size / 1024) + " KB)";
      }).join(", ");
    });
  });
})();
