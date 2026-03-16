(function () {
  function showAnalysisModal() {
    var modal = document.getElementById("rentAnalysisModal");
    if (modal) {
      modal.classList.remove("hidden");
    }
  }

  function hideAnalysisModal() {
    var modal = document.getElementById("rentAnalysisModal");
    if (modal) {
      modal.classList.add("hidden");
    }
  }

  function triggerVacancyAlert(card) {
    var url = card && card.dataset ? card.dataset.alertUrl : "";
    if (!url) {
      if (typeof showAlert === "function") {
        showAlert("Vacancy alert URL is missing.", "error");
      }
      return;
    }

    card.style.pointerEvents = "none";
    card.style.opacity = "0.6";
    fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        if (typeof showAlert === "function") {
          showAlert(data.message, data.count > 0 ? "info" : "success");
        }
      })
      .catch(function () {
        if (typeof showAlert === "function") {
          showAlert("Could not send vacancy alert. Try again.", "error");
        }
      })
      .finally(function () {
        card.style.pointerEvents = "";
        card.style.opacity = "";
      });
  }

  function filterUnits(status) {
    document.querySelectorAll("tbody tr").forEach(function (row) {
      if (row.classList.contains("hover:bg-brown-50")) {
        var statusSpan = row.querySelector("span");
        if (
          status === "all" ||
          (status === "occupied" &&
            statusSpan &&
            statusSpan.textContent.includes("Occupied")) ||
          (status === "vacant" &&
            statusSpan &&
            statusSpan.textContent.includes("Vacant"))
        ) {
          row.classList.remove("hidden");
        } else {
          row.classList.add("hidden");
        }
      }
    });
  }

  function createConfetti() {
    var colors = ["#603b2b", "#8b6e5e", "#d4a574", "#f8f3e6"];
    for (var index = 0; index < 30; index += 1) {
      var confetti = document.createElement("div");
      confetti.style.cssText =
        "position: fixed;" +
        "width: 8px;" +
        "height: 8px;" +
        "background: " +
        colors[Math.floor(Math.random() * colors.length)] +
        ";" +
        "border-radius: " +
        (Math.random() > 0.5 ? "50%" : "0") +
        ";" +
        "z-index: 9999;" +
        "pointer-events: none;" +
        "left: " +
        Math.random() * 100 +
        "vw;" +
        "top: -20px;" +
        "animation: fall " +
        (Math.random() * 2 + 1) +
        "s linear forwards;";
      document.body.appendChild(confetti);
      setTimeout(
        function (node) {
          node.remove();
        },
        2000,
        confetti,
      );
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("tr.hover\\:bg-brown-50").forEach(function (row) {
      row.addEventListener("click", function (event) {
        if (
          !event.target.closest("a") &&
          !event.target.closest("button") &&
          !event.target.closest("form")
        ) {
          var descriptionRow = this.nextElementSibling;
          if (
            descriptionRow &&
            descriptionRow.classList.contains("bg-brown-50/50")
          ) {
            descriptionRow.classList.toggle("hidden");
          }
        }
      });
    });

    if (document.querySelectorAll('[class*="success"]').length > 0) {
      setTimeout(createConfetti, 500);
    }

    var alertCard = document.getElementById("vacancyAlertCard");
    if (alertCard) {
      alertCard.addEventListener("click", function () {
        triggerVacancyAlert(alertCard);
      });
    }

    var analysisCard = document.getElementById("rentAnalysisCard");
    if (analysisCard) {
      analysisCard.addEventListener("click", showAnalysisModal);
    }

    var analysisClose = document.getElementById("rentAnalysisClose");
    if (analysisClose) {
      analysisClose.addEventListener("click", hideAnalysisModal);
    }

    var analysisModal = document.getElementById("rentAnalysisModal");
    if (analysisModal) {
      analysisModal.addEventListener("click", function (event) {
        if (event.target === analysisModal) {
          hideAnalysisModal();
        }
      });
    }
  });

  window.filterUnits = filterUnits;
})();
