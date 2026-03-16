(function () {
  var countdown = 90;
  var countdownEl = document.getElementById("countdown");
  var button = document.getElementById("resend-btn");

  if (!countdownEl || !button) {
    return;
  }

  var timer = setInterval(function () {
    countdown -= 1;
    countdownEl.textContent = countdown;
    if (countdown <= 0) {
      clearInterval(timer);
      button.removeAttribute("disabled");
      button.innerHTML =
        '<i class="fas fa-paper-plane mr-2"></i> Resend Activation Email';
      button.classList.remove(
        "bg-gray-700",
        "cursor-not-allowed",
        "opacity-75",
      );
      button.classList.add("bg-black", "hover:bg-black/90");
    }
  }, 1000);
})();
