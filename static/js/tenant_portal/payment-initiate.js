(function () {
  var radios = document.querySelectorAll("#method-cards input[type=radio]");
  var hiddenSelect = document.querySelector("[name=payment_method] option")
    ? document.querySelector("select[name=payment_method]")
    : null;
  var phoneField = document.getElementById("phone-field");
  var cashCaution = document.getElementById("cash-caution");

  function syncMethod() {
    var checked = document.querySelector("#method-cards input:checked");
    if (!checked) {
      return;
    }

    var value = checked.value;
    if (hiddenSelect) {
      hiddenSelect.value = value;
    }

    if (phoneField) {
      phoneField.style.display = value === "mobile_money" ? "" : "none";
    }

    if (cashCaution) {
      var isManual = value === "cash" || value === "cheque";
      cashCaution.classList.toggle("hidden", !isManual);
    }

    radios.forEach(function (radio) {
      var icon = radio.closest("label")?.querySelector(".check-icon");
      if (icon) {
        icon.style.opacity = radio.checked ? "1" : "0";
      }
    });
  }

  radios.forEach(function (radio) {
    radio.addEventListener("change", syncMethod);
  });

  syncMethod();

  if (hiddenSelect) {
    hiddenSelect.addEventListener("change", function () {
      var radio = document.querySelector(
        '#method-cards input[value="' + this.value + '"]',
      );
      if (radio) {
        radio.checked = true;
        syncMethod();
      }
    });
  }
})();
