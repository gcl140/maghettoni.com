(function () {
  var steps = document.querySelectorAll("[data-step]");
  if (!steps.length) {
    return;
  }

  var confirmForm = document.getElementById("confirm-form");
  var cancelLink = document.getElementById("cancel-link");
  var title = document.getElementById("proc-title");
  var subtitle = document.getElementById("proc-subtitle");

  var delays = [800, 1600, 2400, 3000];

  steps.forEach(function (step, index) {
    setTimeout(function () {
      if (index > 0) {
        var prev = steps[index - 1];
        var prevIcon = prev.querySelector(".step-icon");
        if (prevIcon) {
          prevIcon.innerHTML =
            '<i class="fas fa-check text-green-400 text-xs"></i>';
          prevIcon.className =
            "step-icon w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 bg-green-500/20";
        }
        prev.classList.remove("opacity-40");
      }

      if (index < steps.length) {
        var cur = steps[index];
        var curIcon = cur.querySelector(".step-icon");
        if (curIcon) {
          curIcon.innerHTML =
            '<i class="fas fa-spinner fa-spin text-amber-400 text-xs"></i>';
          curIcon.className =
            "step-icon w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 bg-amber-500/20";
        }
        cur.classList.remove("opacity-40");
      }
    }, delays[index]);
  });

  setTimeout(function () {
    var last = steps[steps.length - 1];
    var lastIcon = last.querySelector(".step-icon");
    if (lastIcon) {
      lastIcon.innerHTML =
        '<i class="fas fa-check text-green-400 text-xs"></i>';
      lastIcon.className =
        "step-icon w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 bg-green-500/20";
    }
    last.classList.remove("opacity-40");

    if (title) {
      title.textContent = "Done!";
    }
    if (subtitle) {
      subtitle.textContent = "Click the button below to confirm your payment.";
    }
    if (confirmForm) {
      confirmForm.classList.remove("hidden");
    }
    if (cancelLink) {
      cancelLink.classList.remove("hidden");
    }
  }, 3800);
})();
