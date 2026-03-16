(function () {
  function navigateWithConfirm(message, url) {
    if (url && window.confirm(message)) {
      window.location.href = url;
    }
  }

  function wireButton(buttonId, message) {
    var button = document.getElementById(buttonId);
    if (!button) {
      return;
    }

    button.addEventListener("click", function () {
      navigateWithConfirm(message, button.dataset.url);
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
