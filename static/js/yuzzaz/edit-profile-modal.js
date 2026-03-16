// Preview profile picture before upload
const profilePictureInput = document.getElementById("profile-picture-input");

if (profilePictureInput) {
  profilePictureInput.addEventListener("change", function () {
    const file = this.files[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
      const preview = document.getElementById("avatar-preview");
      if (!preview) {
        return;
      }

      if (preview.tagName === "IMG") {
        preview.src = e.target.result;
      } else {
        const img = document.createElement("img");
        img.id = "avatar-preview";
        img.src = e.target.result;
        img.className =
          "w-16 h-16 rounded-full object-cover border-2 border-amber-400";
        img.alt = "Avatar";
        preview.replaceWith(img);
      }
    };

    reader.readAsDataURL(file);
  });
}
