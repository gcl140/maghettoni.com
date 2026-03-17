(function () {
  function wireButton(buttonId, message) {
    var button = document.getElementById(buttonId);
    if (!button) return;

    button.addEventListener("click", function () {
      var url = button.dataset.url;
      if (!url) return;
      showConfirm(message, function () {
        window.location.href = url;
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireButton("tenantActivateBtn", "Mark this tenant as active?");
    wireButton("tenantDeactivateBtn", "Mark this tenant as inactive?");
    wireButton(
      "tenantDeleteBtn",
      "Are you sure you want to permanently remove this tenant? This action cannot be undone.",
    );
  });
})();
