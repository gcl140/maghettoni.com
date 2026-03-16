document.addEventListener("DOMContentLoaded", function () {
  if (typeof Toastify !== "function") {
    return;
  }

  document
    .querySelectorAll("#yuzzaz-toast-messages [data-message]")
    .forEach(function (entry) {
      var tags = entry.dataset.tags || "success";
      var backgroundColor = tags === "error" ? "#FF4C4C" : "#4BB543";
      if (tags === "info") {
        backgroundColor = "#4299e1";
      }

      Toastify({
        text: entry.dataset.message || "",
        duration: Number(entry.dataset.duration || 15000),
        close: true,
        gravity: "top",
        position: "right",
        backgroundColor: backgroundColor,
        stopOnFocus: true,
      }).showToast();
    });
});
