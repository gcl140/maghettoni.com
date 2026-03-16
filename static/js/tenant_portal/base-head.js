(function () {
  var pref = localStorage.getItem('mag-lang');
  var exp = 'expires=Thu, 01 Jan 1970 00:00:00 UTC';
  if (pref === 'sw') {
    document.cookie = 'googtrans=/en/sw; path=/';
    document.cookie = 'googtrans=/en/sw; domain=.' + location.hostname + '; path=/';
  } else if (pref === 'en') {
    ['/', location.pathname].forEach(function (p) {
      document.cookie = 'googtrans=; path=' + p + '; ' + exp;
      document.cookie = 'googtrans=; domain=' + location.hostname + '; path=' + p + '; ' + exp;
    });
  }
})();

window.googleTranslateElementInit = function () {
  new google.translate.TranslateElement(
    {
      pageLanguage: "en",
      includedLanguages: "sw",
      autoDisplay: false,
    },
    "google_translate_element",
  );
};

(function suppressGoogleBanner() {
  function hideBanner() {
    var frames = document.querySelectorAll(
      "iframe.goog-te-banner-frame, .goog-te-banner-frame",
    );
    frames.forEach(function (frame) {
      frame.style.setProperty("display", "none", "important");
    });

    if (document.body && document.body.style.top !== "0px") {
      document.body.style.setProperty("top", "0", "important");
      document.body.style.setProperty("position", "static", "important");
    }
  }

  var obs = new MutationObserver(hideBanner);
  document.addEventListener("DOMContentLoaded", function () {
    hideBanner();
    obs.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["style"],
    });
  });
})();
