document.addEventListener("DOMContentLoaded", function () {
  const config = document.getElementById("maintenance-edit-config");
  const initialUnit = config ? config.dataset.initialUnit : "";
  const initialTenant = config ? config.dataset.initialTenant : "";
  const isEdit = config ? config.dataset.isEdit === "true" : false;

  const propertySelect = document.getElementById("id_property");
  const unitSelect = document.getElementById("id_unit");
  const tenantSelect = document.getElementById("id_tenant");

  function updateUnitsAndTenants() {
    if (!propertySelect || !unitSelect || !tenantSelect) {
      return;
    }

    const propertyId = propertySelect.value;

    if (!propertyId) {
      unitSelect.innerHTML =
        '<option value="">Select a property first</option>';
      tenantSelect.innerHTML =
        '<option value="">Select a property first</option>';
      unitSelect.disabled = true;
      tenantSelect.disabled = true;
      return;
    }

    fetch("/dashboard/api/properties/" + propertyId + "/units-tenants/")
      .then(function (response) {
        if (!response.ok) {
          throw new Error("Failed to fetch units and tenants");
        }
        return response.json();
      })
      .then(function (data) {
        unitSelect.innerHTML = '<option value="">Select a unit</option>';
        data.units.forEach(function (unit) {
          const option = document.createElement("option");
          option.value = unit.id;
          option.textContent =
            "Unit " +
            unit.unit_number +
            " (" +
            unit.bedrooms +
            " bed, " +
            unit.bathrooms +
            " bath)";
          option.selected = String(unit.id) === initialUnit;
          unitSelect.appendChild(option);
        });
        unitSelect.disabled = false;

        tenantSelect.innerHTML = '<option value="">Select a tenant</option>';
        data.tenants.forEach(function (tenant) {
          const option = document.createElement("option");
          option.value = tenant.id;
          option.textContent =
            tenant.first_name +
            " " +
            tenant.last_name +
            " - Unit " +
            (tenant.unit_number || "N/A");
          option.selected = String(tenant.id) === initialTenant;
          tenantSelect.appendChild(option);
        });
        tenantSelect.disabled = false;
      })
      .catch(function (error) {
        console.error("Error loading data:", error);
        unitSelect.innerHTML = '<option value="">Error loading units</option>';
        tenantSelect.innerHTML =
          '<option value="">Error loading tenants</option>';
      });
  }

  // Keep this global because template click handlers call it inline.
  window.updatePriorityClass = function updatePriorityClass() {
    const priorityRadios = document.querySelectorAll('input[name="priority"]');
    priorityRadios.forEach(function (radio) {
      const parentDiv = radio.parentElement;
      if (!parentDiv) {
        return;
      }

      if (radio.checked) {
        parentDiv.classList.add("border-brown-500", "bg-brown-50");
        parentDiv.classList.remove("border-brown-200");
      } else {
        parentDiv.classList.remove("border-brown-500", "bg-brown-50");
        parentDiv.classList.add("border-brown-200");
      }
    });
  };

  if (propertySelect) {
    propertySelect.addEventListener("change", updateUnitsAndTenants);
    if (propertySelect.value) {
      updateUnitsAndTenants();
    }
  }

  window.updatePriorityClass();
  document.querySelectorAll('input[name="priority"]').forEach(function (radio) {
    radio.addEventListener("change", window.updatePriorityClass);
  });

  const costInput = document.getElementById("id_cost");
  if (costInput) {
    costInput.addEventListener("blur", function () {
      const value = parseFloat(this.value);
      if (!Number.isNaN(value) && value >= 0) {
        this.value = value.toFixed(2);
      } else if (this.value.trim() === "") {
        this.value = "";
      }
    });
  }

  if (!isEdit) {
    const titleInput = document.getElementById("id_title");
    if (titleInput) {
      titleInput.focus();
    }
  }

  const form = document.querySelector("form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", function (e) {
    const requiredFields = form.querySelectorAll("[required]");
    let isValid = true;

    requiredFields.forEach(function (field) {
      if (
        !field.value.trim() &&
        field.type !== "radio" &&
        field.type !== "checkbox"
      ) {
        field.classList.add("border-red-500", "bg-red-50");
        isValid = false;
      } else {
        field.classList.remove("border-red-500", "bg-red-50");
      }
    });

    const prioritySelected = document.querySelector(
      'input[name="priority"]:checked',
    );
    const statusSelected = document.querySelector(
      'input[name="status"]:checked',
    );

    if (!prioritySelected) {
      Toastify({
        text: "Please select a priority level!",
        duration: 3000,
        close: true,
        gravity: "top",
        position: "right",
        backgroundColor: "#dc2626",
        className: "rounded-xl shadow-lg",
      }).showToast();
      isValid = false;
    }

    if (!statusSelected) {
      Toastify({
        text: "Please select a status!",
        duration: 3000,
        close: true,
        gravity: "top",
        position: "right",
        backgroundColor: "#dc2626",
        className: "rounded-xl shadow-lg",
      }).showToast();
      isValid = false;
    }

    if (!isValid) {
      e.preventDefault();
      const firstError =
        form.querySelector(".border-red-500") ||
        document.querySelector('input[name="priority"]')?.parentElement ||
        document.querySelector('input[name="status"]')?.parentElement;

      if (firstError) {
        firstError.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  });
});
