document.addEventListener("DOMContentLoaded", function () {
  const rentInput = document.getElementById("id_monthly_rent");
  if (rentInput) {
    rentInput.addEventListener("blur", function () {
      const value = parseFloat(this.value);
      if (!Number.isNaN(value) && value >= 0) {
        this.value = value.toFixed(2);
      }
    });
  }

  const bedroomsInput = document.getElementById("id_bedrooms");
  if (bedroomsInput && rentInput && rentInput.parentNode) {
    const priceSuggestions = {
      0: "800 - 1200",
      1: "1200 - 1800",
      2: "1800 - 2500",
      3: "2500 - 3500",
      4: "3500 - 5000",
    };

    bedroomsInput.addEventListener("change", function () {
      const beds = parseInt(this.value, 10) || 0;
      const suggestion = priceSuggestions[beds] || priceSuggestions[4];

      let tooltip = document.getElementById("price-suggestion");
      if (!tooltip) {
        tooltip = document.createElement("div");
        tooltip.id = "price-suggestion";
        tooltip.className =
          "mt-2 p-3 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-800";
        rentInput.parentNode.appendChild(tooltip);
      }

      tooltip.innerHTML =
        '<i class="fas fa-lightbulb mr-1"></i>' +
        "<strong>Market suggestion:</strong> $" +
        suggestion +
        " per month for " +
        beds +
        " bedroom" +
        (beds !== 1 ? "s" : "");
    });
  }

  const form = document.querySelector("form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", function (e) {
    const requiredFields = form.querySelectorAll("[required]");
    let isValid = true;

    requiredFields.forEach(function (field) {
      if (!field.value.trim() && field.type !== "checkbox") {
        field.classList.add("border-red-500", "bg-red-50");
        isValid = false;
      } else {
        field.classList.remove("border-red-500", "bg-red-50");
      }
    });

    if (!isValid) {
      e.preventDefault();
      const firstError = form.querySelector(".border-red-500");
      if (firstError) {
        firstError.scrollIntoView({ behavior: "smooth", block: "center" });
        firstError.focus();
      }

      Toastify({
        text: "Please fill in all required fields!",
        duration: 3000,
        close: true,
        gravity: "top",
        position: "right",
        backgroundColor: "#dc2626",
        className: "rounded-xl shadow-lg",
      }).showToast();
    }
  });
});
