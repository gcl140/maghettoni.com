/* Enforce persisted language preference before Google Translate initialises */
(function () {
  var pref = localStorage.getItem("mag-lang");
  var exp = "expires=Thu, 01 Jan 1970 00:00:00 UTC";
  var host = location.hostname;

  function setCookie(name, value) {
    document.cookie = name + "=" + value + "; path=/";
    if (host && host !== "localhost" && host !== "127.0.0.1") {
      document.cookie = name + "=" + value + "; domain=" + host + "; path=/";
      document.cookie = name + "=" + value + "; domain=." + host + "; path=/";
    }
  }

  function clearCookie(name) {
    document.cookie = name + "=; path=/; " + exp;
    if (host && host !== "localhost" && host !== "127.0.0.1") {
      document.cookie = name + "=; domain=" + host + "; path=/; " + exp;
      document.cookie = name + "=; domain=." + host + "; path=/; " + exp;
    }
  }

  function readCookie(name) {
    var m = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]+)"));
    return m ? decodeURIComponent(m[1]) : "";
  }

  if (!pref) {
    var gt = readCookie("googtrans");
    pref = gt === "/en/sw" ? "sw" : "en";
  }

  document.documentElement.lang = pref === "sw" ? "sw" : "en";

  if (pref === "sw") {
    setCookie("googtrans", "/en/sw");
  } else if (pref === "en") {
    clearCookie("googtrans");
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
