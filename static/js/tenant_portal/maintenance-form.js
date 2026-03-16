(function () {
  var cards = document.querySelectorAll(".priority-card");
  cards.forEach(function (card) {
    var radio = card.querySelector("input[type=radio]");
    var check = card.querySelector(".pcheck");

    if (!radio || !check) {
      return;
    }

    radio.addEventListener("change", function () {
      cards.forEach(function (innerCard) {
        var innerCheck = innerCard.querySelector(".pcheck");
        if (innerCheck) {
          innerCheck.style.opacity = "0";
        }
        innerCard.classList.remove(
          "bg-amber-500/5",
          "bg-green-500/5",
          "bg-orange-500/5",
          "bg-red-500/5",
        );
      });
      check.style.opacity = "1";
    });

    if (radio.checked) {
      check.style.opacity = "1";
    }

    card.addEventListener("click", function () {
      radio.checked = true;
      radio.dispatchEvent(new Event("change"));
    });
  });
})();
