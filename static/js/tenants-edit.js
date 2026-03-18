document.addEventListener("DOMContentLoaded", function () {
  var picInput = document.getElementById('id_profile_picture');
  if (picInput) {
    picInput.addEventListener('change', function () {
      if (this.files && this.files[0]) {
        var reader = new FileReader();
        reader.onload = function (e) {
          document.getElementById('tenant-pic-preview').src = e.target.result;
          document.getElementById('tenant-pic-preview-wrap').classList.remove('hidden');
        };
        reader.readAsDataURL(this.files[0]);
      }
    });
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const config = document.getElementById("tenant-edit-config");
  const initialUnit = config ? config.dataset.initialUnit : "";

  const propertySelect = document.getElementById("id_property");
  const unitSelect = document.getElementById("id_unit");

  if (propertySelect && unitSelect) {
    propertySelect.addEventListener("change", function () {
      const propertyId = this.value;

      if (!propertyId) {
        unitSelect.innerHTML =
          '<option value="">Select a unit (optional)</option>';
        unitSelect.disabled = false;
        return;
      }

      unitSelect.disabled = true;
      unitSelect.innerHTML = '<option value="">Loading units...</option>';

      fetch("/dashboard/api/properties/" + propertyId + "/units/available/")
        .then(function (response) {
          if (!response.ok) {
            throw new Error("Failed to load units");
          }
          return response.json();
        })
        .then(function (data) {
          unitSelect.innerHTML =
            '<option value="">Select a unit (optional)</option>';
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
              " bath) - $" +
              unit.monthly_rent;
            option.selected = String(unit.id) === initialUnit;
            unitSelect.appendChild(option);
          });
          unitSelect.disabled = false;
        })
        .catch(function (error) {
          console.error("Error loading units:", error);
          unitSelect.innerHTML =
            '<option value="">Error loading units</option>';
          unitSelect.disabled = false;
        });
    });

    if (propertySelect.value) {
      propertySelect.dispatchEvent(new Event("change"));
    }
  }

  const dateInputs = document.querySelectorAll('input[type="date"]');
  dateInputs.forEach(function (input) {
    if (input.id === "id_move_in_date") {
      const today = new Date().toISOString().split("T")[0];
      input.min = today;
    }
    input.classList.add("cursor-pointer");
  });

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
            '<i class="fas fa-exclamation-circle mr-1"></i> This field is required';
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

    if (!isValid) {
      e.preventDefault();
      const firstError = form.querySelector(".border-red-500");
      if (firstError) {
        firstError.scrollIntoView({ behavior: "smooth", block: "center" });
        firstError.focus();
      }
    }
  });
});
