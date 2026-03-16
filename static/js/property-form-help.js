document.addEventListener("DOMContentLoaded", function () {
  var actionButtons = document.querySelectorAll(".js-help-action");

  actionButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var targetId = btn.getAttribute("data-focus-target");
      if (!targetId) return;

      var target = document.getElementById(targetId);
      if (!target) return;

      if (btn.getAttribute("data-action") === "pick-image") {
        target.click();
        return;
      }

      target.scrollIntoView({ behavior: "smooth", block: "center" });
      if (typeof target.focus === "function") {
        target.focus({ preventScroll: true });
      }
    });
  });
});
