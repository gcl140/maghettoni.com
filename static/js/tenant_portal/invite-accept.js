function togglePw(id, btn) {
  var input = document.getElementById(id);
  if (!input) {
    return;
  }

  var showing = input.type === "text";
  input.type = showing ? "password" : "text";
  btn.innerHTML =
    '<i class="fas fa-eye' + (showing ? "" : "-slash") + ' text-sm"></i>';
}

(function () {
  var pw = document.getElementById("pw1");
  if (!pw) {
    return;
  }

  var segs = [
    document.getElementById("s1"),
    document.getElementById("s2"),
    document.getElementById("s3"),
    document.getElementById("s4"),
  ];
  var label = document.getElementById("strength-label");

  var levels = [
    { color: "bg-red-500", text: "Dhaifu sana" },
    { color: "bg-orange-500", text: "Dhaifu" },
    { color: "bg-amber-500", text: "Wastani" },
    { color: "bg-green-500", text: "Nguvu" },
  ];

  pw.addEventListener("input", function () {
    var value = this.value;
    var score = 0;

    if (value.length >= 8) {
      score += 1;
    }
    if (/[A-Z]/.test(value)) {
      score += 1;
    }
    if (/[0-9]/.test(value)) {
      score += 1;
    }
    if (/[^A-Za-z0-9]/.test(value)) {
      score += 1;
    }

    segs.forEach(function (seg, index) {
      if (!seg) {
        return;
      }
      var cls = index < score ? levels[score - 1].color : "bg-brown-600";
      seg.className = "strength-seg h-1.5 flex-1 rounded " + cls;
    });

    if (label) {
      label.textContent = value.length ? levels[score - 1]?.text || "" : "";
    }
  });
})();
