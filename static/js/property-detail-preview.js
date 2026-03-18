(function () {
  function openDocPreview(url, title, type) {
    var modal = document.getElementById("doc-preview-modal");
    var body = document.getElementById("doc-preview-body");
    var titleEl = document.getElementById("doc-preview-title");
    var icon = document.getElementById("doc-preview-icon");
    var openBtn = document.getElementById("doc-preview-open");

    if (!modal || !body || !titleEl || !icon || !openBtn) {
      return;
    }

    titleEl.textContent = title;
    openBtn.href = url;
    body.innerHTML = "";

    if (type === "image") {
      icon.className = "fas fa-image text-green-600 text-sm";
      var img = document.createElement("img");
      img.src = url;
      img.alt = title;
      img.className = "max-w-full max-h-full mx-auto block object-contain p-4";
      img.style.maxHeight = "75vh";
      body.appendChild(img);
    } else if (type === "pdf") {
      icon.className = "fas fa-file-pdf text-red-600 text-sm";
      var iframe = document.createElement("iframe");
      iframe.src = url;
      iframe.className = "w-full border-0";
      iframe.style.height = "75vh";
      iframe.title = title;
      body.appendChild(iframe);
    } else {
      icon.className = "fas fa-file-alt text-blue-600 text-sm";
      body.innerHTML =
        '<div class="flex flex-col items-center justify-center h-64 gap-4 text-gray-500">' +
        '<i class="fas fa-file-alt text-5xl text-gray-300"></i>' +
        '<p class="text-sm">Preview not available for this file type.</p>' +
        '<a href="' +
        url +
        '" target="_blank" rel="noopener noreferrer" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">' +
        '<i class="fas fa-external-link-alt mr-2"></i>Open File</a>' +
        "</div>";
    }

    modal.style.display = "flex";
    document.body.style.overflow = "hidden";
  }

  function closeDocPreview() {
    var modal = document.getElementById("doc-preview-modal");
    var body = document.getElementById("doc-preview-body");
    if (!modal || !body) {
      return;
    }
    modal.style.display = "none";
    body.innerHTML = "";
    document.body.style.overflow = "";
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeDocPreview();
    }
  });

  window.openDocPreview = openDocPreview;
  window.closeDocPreview = closeDocPreview;
})();

(function () {
  // Move fullscreen modal to body to escape stacking context
  var modal = document.getElementById('img-fullscreen-modal');
  if (modal) document.body.appendChild(modal);

  var slides = document.querySelectorAll('.prop-slide');
  var dots = document.querySelectorAll('.slide-dot');
  var counter = document.getElementById('slide-counter');
  var cur = 0;
  if (slides.length <= 1) return;

  function show(n) {
    slides[cur].classList.add('opacity-0', 'pointer-events-none');
    if (dots[cur]) dots[cur].className = dots[cur].className.replace('bg-white', 'bg-white/40');
    cur = (n + slides.length) % slides.length;
    slides[cur].classList.remove('opacity-0', 'pointer-events-none');
    if (dots[cur]) dots[cur].className = dots[cur].className.replace('bg-white/40', 'bg-white');
    if (counter) counter.textContent = (cur + 1) + ' / ' + slides.length;
  }

  window.slideMove = function (d) { show(cur + d); };
  window.goSlide = function (n) { show(n); };
})();

window.openImgModal = function (src) {
  document.getElementById('img-fullscreen-src').src = src;
  document.getElementById('img-fullscreen-modal').style.display = 'flex';
};
