document.addEventListener("DOMContentLoaded", function () {
  if (typeof Toastify !== "function") {
    return;
  }

  document
    .querySelectorAll("#dashboard-toast-messages [data-message]")
    .forEach(function (entry) {
      var tags = entry.dataset.tags || "info";
      var backgroundColor = "#2563eb";

      if (tags === "success") {
        backgroundColor = "#16a34a";
      } else if (tags === "error") {
        backgroundColor = "#dc2626";
      } else if (tags === "warning") {
        backgroundColor = "#d97706";
      }

      Toastify({
        text: entry.dataset.message || "",
        duration: 5000,
        close: true,
        gravity: "top",
        position: "right",
        backgroundColor: backgroundColor,
        style: { borderRadius: "10px", fontSize: "14px" },
      }).showToast();
    });
});
