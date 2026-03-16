function getLocation() {
  if (!navigator.geolocation) {
    showAlert("Geolocation not supported", "error");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;

      // Fill the address field (renders as name="address" so it submits correctly)
      const addressField = document.getElementById("addressField");
      if (addressField && !addressField.value.trim()) {
        addressField.value = `${lat.toFixed(6)},${lng.toFixed(6)}`;
        addressField.readOnly = true;
        addressField.classList.add("bg-gray-100", "cursor-not-allowed");
      }

      // Show success message
      Toastify({
        text: "Location acquired successfully!",
        duration: 3000,
        close: true,
        gravity: "top",
        position: "right",
        backgroundColor: "#38a169",
      }).showToast();

      // const successDiv = document.getElementById("location-success");
      // successDiv.classList.remove("hidden");
    },
    (error) => {
      console.error(error);
      showAlert("Location permission denied or unavailable", "error");
    },
    { enableHighAccuracy: true },
  );
}

function confirmDelete() {
  if (
    confirm(
      "Are you sure you want to delete this property? This action cannot be undone.",
    )
  ) {
    // Here you would typically make an AJAX request or redirect to delete view
    window.location.href = "{% url 'property_delete' property.id %}";
  }
}
