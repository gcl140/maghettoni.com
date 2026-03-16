/* Enforce persisted language preference before Google Translate initialises */
(function () {
  var pref = localStorage.getItem("mag-lang");
  var exp = "expires=Thu, 01 Jan 1970 00:00:00 UTC";
  if (pref === "sw") {
    document.cookie = "googtrans=/en/sw; path=/";
    document.cookie =
      "googtrans=/en/sw; domain=." + location.hostname + "; path=/";
  } else if (pref === "en") {
    document.cookie = "googtrans=; path=/; " + exp;
    document.cookie =
      "googtrans=; domain=" + location.hostname + "; path=/; " + exp;
  }
})();

function googleTranslateElementInit() {
  new google.translate.TranslateElement(
    {
      pageLanguage: "en",
      includedLanguages: "sw",
      autoDisplay: false,
    },
    "google_translate_element",
  );
}
