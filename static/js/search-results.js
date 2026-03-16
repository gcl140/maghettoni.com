document.addEventListener("DOMContentLoaded", function () {
  var meta = document.getElementById("search-meta");
  if (!meta) return;
  var query = meta.dataset.query || "";
  if (!query) return;

  var elements = document.querySelectorAll("h3, p, td, span");
  var regex = new RegExp("(" + query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");

  elements.forEach(function (el) {
    var html = el.innerHTML;
    el.innerHTML = html.replace(regex, '<span class="bg-yellow-200 px-1 rounded">$1</span>');
  });
});
