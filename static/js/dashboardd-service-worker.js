if ("serviceWorker" in navigator) {
  navigator.serviceWorker
    .register("/sw.js", { scope: "/dashboard/" })
    .catch(function (error) {
      console.warn("SW registration failed:", error);
    });
}
