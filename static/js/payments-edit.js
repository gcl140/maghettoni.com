document.addEventListener("DOMContentLoaded", function () {
  const config = document.getElementById("payments-edit-config");
  const isEdit = config ? config.dataset.isEdit === "true" : false;

  const tenantSelect = document.getElementById("id_tenant");
  const propertySelect = document.getElementById("id_property");
  const tenantUnitInfo = document.getElementById("tenant-unit-info");

  function updateTenantInfo() {
    if (!tenantSelect || !tenantUnitInfo) {
      return;
    }

    const tenantId = tenantSelect.value;

    if (!tenantId) {
      tenantUnitInfo.innerHTML =
        '<p class="text-sm text-gray-500">Chagua mpangaji kwanza</p>';
      return;
    }

    fetch("/dashboard/api/tenants/" + tenantId + "/details/")
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Failed to load tenant details");
        }
        return response.json();
      })
      .then(function (data) {
        if (data.unit) {
          tenantUnitInfo.innerHTML =
            '<div class="flex items-center">' +
            '<i class="fas fa-door-open text-brown-600 mr-3"></i>' +
            "<div>" +
            '<p class="text-sm font-semibold text-gray-900">Chumba ' +
            data.unit.unit_number +
            "</p>" +
            '<p class="text-xs text-gray-600">' +
            data.unit.bedrooms +
            " vyumba vya kulala • " +
            data.unit.bathrooms +
            " bafu</p>" +
            '<p class="text-xs font-medium text-gray-800 mt-1">Kodi: TZS ' +
            data.unit.monthly_rent +
            "/mwezi</p>" +
            "</div>" +
            "</div>";
        } else {
          tenantUnitInfo.innerHTML =
            '<div class="flex items-center">' +
            '<i class="fas fa-exclamation-triangle text-yellow-600 mr-3"></i>' +
            "<div>" +
            '<p class="text-sm font-semibold text-gray-900">Hakuna chumba kilichowekwa</p>' +
            '<p class="text-xs text-gray-600">Mpangaji huyu hajawekewa chumba bado</p>' +
            "</div>" +
            "</div>";
        }

        if (data.property_id && propertySelect) {
          propertySelect.value = data.property_id;
        }
      })
      .catch(function (error) {
        console.error("Error loading tenant details:", error);
        tenantUnitInfo.innerHTML =
          '<p class="text-sm text-red-500">Hitilafu katika kupakia maelezo</p>';
      });
  }

  if (tenantSelect) {
    tenantSelect.addEventListener("change", updateTenantInfo);
    if (tenantSelect.value) {
      updateTenantInfo();
    }
  }

  const amountInput = document.getElementById("id_amount");
  if (amountInput) {
    amountInput.addEventListener("blur", function () {
      const value = parseFloat(this.value);
      if (!Number.isNaN(value) && value >= 0) {
        this.value = value.toFixed(2);
      }
    });

    amountInput.addEventListener("focusout", function () {
      const value = this.value.replace(/,/g, "");
      if (!Number.isNaN(parseFloat(value)) && value !== "") {
        this.value = parseFloat(value).toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
      }
    });

    amountInput.addEventListener("focus", function () {
      this.value = this.value.replace(/,/g, "");
    });
  }

  const paymentDateInput = document.getElementById("id_payment_date");
  const dueDateInput = document.getElementById("id_due_date");
  if (paymentDateInput && dueDateInput) {
    const today = new Date().toISOString().split("T")[0];
    paymentDateInput.max = today;

    paymentDateInput.addEventListener("change", function () {
      if (paymentDateInput.value && !dueDateInput.value) {
        const paymentDate = new Date(paymentDateInput.value);
        const dueDate = new Date(paymentDate);
        dueDate.setDate(dueDate.getDate() + 30);
        dueDateInput.value = dueDate.toISOString().split("T")[0];
      }
    });
  }

  const statusSelect = document.getElementById("id_status");
  if (statusSelect) {
    function updateStatusStyle() {
      const statusColors = {
        completed: "border-green-500 bg-green-50 text-green-800",
        pending: "border-yellow-500 bg-yellow-50 text-yellow-800",
        failed: "border-red-500 bg-red-50 text-red-800",
        refunded: "border-blue-500 bg-blue-50 text-blue-800",
      };

      Object.values(statusColors).forEach(function (colorClass) {
        statusSelect.classList.remove.apply(
          statusSelect.classList,
          colorClass.split(" "),
        );
      });

      if (statusColors[statusSelect.value]) {
        statusSelect.classList.add.apply(
          statusSelect.classList,
          statusColors[statusSelect.value].split(" "),
        );
      }
    }

    statusSelect.addEventListener("change", updateStatusStyle);
    updateStatusStyle();
  }

  const form = document.querySelector("form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", function (e) {
    const requiredFields = form.querySelectorAll("[required]");
    let isValid = true;

    requiredFields.forEach(function (field) {
      if (!field.value.trim()) {
        field.classList.add("border-red-500", "bg-red-50");
        isValid = false;

        if (
          !field.nextElementSibling ||
          !field.nextElementSibling.classList.contains("error-message")
        ) {
          const errorDiv = document.createElement("p");
          errorDiv.className = "mt-1 text-sm text-red-600 error-message";
          errorDiv.innerHTML =
            '<i class="fas fa-exclamation-circle mr-1"></i> Sehemu hii inahitajika';
          field.parentNode.insertBefore(errorDiv, field.nextSibling);
        }
      } else {
        field.classList.remove("border-red-500", "bg-red-50");
        const errorMsg = field.nextElementSibling;
        if (
          errorMsg &&
          errorMsg.classList &&
          errorMsg.classList.contains("error-message")
        ) {
          errorMsg.remove();
        }
      }
    });

    if (amountInput && amountInput.value) {
      const amount = parseFloat(amountInput.value.replace(/,/g, ""));
      if (Number.isNaN(amount) || amount <= 0) {
        amountInput.classList.add("border-red-500", "bg-red-50");
        isValid = false;

        Toastify({
          text: "Kiasi cha malipo lazima kiwe nambari chanya!",
          duration: 3000,
          close: true,
          gravity: "top",
          position: "right",
          backgroundColor: "#dc2626",
          className: "rounded-xl shadow-lg",
        }).showToast();
      }
    }

    if (!isValid) {
      e.preventDefault();
      const firstError = form.querySelector(".border-red-500");
      if (firstError) {
        firstError.scrollIntoView({ behavior: "smooth", block: "center" });
        firstError.focus();
      }
    }
  });

  if (!isEdit && amountInput) {
    setTimeout(function () {
      amountInput.focus();
    }, 300);
  }
});
