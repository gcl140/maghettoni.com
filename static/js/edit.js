function getLocation() {
  if (!navigator.geolocation) {
    alert("Geolocation not supported");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;

      // Fill the textarea with lat/lng
      const addressField = document.getElementById("addressField");
      addressField.value = `${lat.toFixed(6)},${lng.toFixed(6)}`;
      addressField.readOnly = true;
      addressField.classList.add("bg-gray-100", "cursor-not-allowed");

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
      alert("Location permission denied or unavailable");
    },
    { enableHighAccuracy: true }
  );
}

function confirmDelete() {
  if (
    confirm(
      "Are you sure you want to delete this property? This action cannot be undone."
    )
  ) {
    // Here you would typically make an AJAX request or redirect to delete view
    window.location.href = "{% url 'property_delete' property.id %}";
  }
}