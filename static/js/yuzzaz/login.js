(function () {
  var pwd = document.getElementById("password");
  var btn = document.getElementById("togglePassword");
  if (!pwd || !btn) {
    return;
  }

  var icon = btn.querySelector("i");
  btn.addEventListener("click", function () {
    var isHidden = pwd.type === "password";
    pwd.type = isHidden ? "text" : "password";
    if (icon) {
      icon.classList.toggle("fa-eye");
      icon.classList.toggle("fa-eye-slash");
    }
  });
})();
