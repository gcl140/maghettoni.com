(function () {
  var tel = document.getElementById("id_telephone");
  if (!tel) {
    return;
  }

  tel.addEventListener("input", function () {
    var value = tel.value.replace(/\s+/g, "");
    if (!value.startsWith("+255")) {
      value = value.replace(/^\+?0*/, "");
      value = "+255" + value;
    }
    if (value.startsWith("+2550")) {
      value = "+255" + value.slice(5);
    }
    tel.value = value;
  });
})();
