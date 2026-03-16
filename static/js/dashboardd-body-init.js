if (localStorage.getItem("sb_collapsed") === "1") {
  var appBody = document.getElementById("appBody");
  if (appBody) {
    appBody.classList.add("sb-collapsed", "no-sb-transition");
  }
}
