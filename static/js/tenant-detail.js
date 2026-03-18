(function () {
  function wireButton(buttonId, message) {
    var button = document.getElementById(buttonId);
    if (!button) return;

    button.addEventListener("click", function () {
      var url = button.dataset.url;
      if (!url) return;
      showConfirm(message, function () {
        window.location.href = url;
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireButton("tenantActivateBtn", "Mark this tenant as active?");
    wireButton("tenantDeactivateBtn", "Mark this tenant as inactive?");
    wireButton(
      "tenantDeleteBtn",
      "Are you sure you want to permanently remove this tenant? This action cannot be undone.",
    );
  });
})();

function showLeasePicker(baseUrl) {
  var overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:99999;display:flex;align-items:center;justify-content:center;';
  var box = document.createElement('div');
  box.style.cssText = 'background:#fff;border-radius:16px;padding:28px 32px;max-width:360px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,.25);font-family:inherit;';
  var title = document.createElement('p');
  title.style.cssText = 'font-weight:700;font-size:16px;color:#3b2512;margin-bottom:6px;text-align:center;';
  title.textContent = 'Select Language';
  var sub = document.createElement('p');
  sub.style.cssText = 'font-size:12px;color:#888;margin-bottom:20px;text-align:center;';
  sub.textContent = 'Choose the language for the lease agreement';
  var btns = document.createElement('div');
  btns.style.cssText = 'display:flex;gap:12px;';
  function makeBtn(label, flag, lang) {
    var b = document.createElement('button');
    b.innerHTML = flag + ' ' + label;
    b.style.cssText = 'flex:1;padding:14px 10px;border:1.5px solid #d1c4bc;background:#faf7f5;color:#3b2512;border-radius:12px;font-size:14px;font-weight:600;cursor:pointer;font-family:inherit;';
    b.onmouseover = function(){ b.style.borderColor='#7c5c45'; b.style.background='#f3ede8'; };
    b.onmouseout  = function(){ b.style.borderColor='#d1c4bc'; b.style.background='#faf7f5'; };
    b.addEventListener('click', function() { document.body.removeChild(overlay); window.open(baseUrl + '?lang=' + lang, '_blank'); });
    return b;
  }
  btns.appendChild(makeBtn('EN', '🇬🇧', 'en'));
  btns.appendChild(makeBtn('SW', '🇹🇿', 'sw'));
  var cancel = document.createElement('button');
  cancel.textContent = 'Cancel';
  cancel.style.cssText = 'display:block;width:100%;margin-top:12px;padding:9px;border:none;background:transparent;color:#9ca3af;font-size:13px;cursor:pointer;font-family:inherit;';
  cancel.addEventListener('click', function() { document.body.removeChild(overlay); });
  overlay.addEventListener('click', function(e){ if(e.target===overlay) document.body.removeChild(overlay); });
  box.appendChild(title); box.appendChild(sub); box.appendChild(btns); box.appendChild(cancel);
  overlay.appendChild(box); document.body.appendChild(overlay);
}

function showQrModal(name, email, phone) {
  var vcard = 'BEGIN:VCARD\nVERSION:3.0\nFN:' + name + '\nEMAIL:' + email + '\nTEL:' + phone + '\nEND:VCARD';
  var url = 'https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=' + encodeURIComponent(vcard);
  var overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:99999;display:flex;align-items:center;justify-content:center;';
  var box = document.createElement('div');
  box.style.cssText = 'background:#fff;border-radius:16px;padding:28px 32px;text-align:center;min-width:280px;box-shadow:0 20px 60px rgba(0,0,0,.25);font-family:inherit;';
  var title = document.createElement('p');
  title.style.cssText = 'font-weight:700;font-size:15px;color:#3b2512;margin-bottom:4px;';
  title.textContent = name;
  var sub = document.createElement('p');
  sub.style.cssText = 'font-size:12px;color:#888;margin-bottom:16px;';
  sub.textContent = 'Scan to save contact';
  var img = document.createElement('img');
  img.src = url; img.alt = 'QR Code';
  img.style.cssText = 'width:220px;height:220px;border:1px solid #e5e7eb;border-radius:8px;';
  var close = document.createElement('button');
  close.textContent = 'Close';
  close.style.cssText = 'margin-top:18px;padding:9px 28px;border:none;background:#7c5c45;color:#fff;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;';
  close.onclick = function() { document.body.removeChild(overlay); };
  overlay.addEventListener('click', function(e){ if(e.target===overlay) document.body.removeChild(overlay); });
  box.appendChild(title); box.appendChild(sub); box.appendChild(img); box.appendChild(close);
  overlay.appendChild(box); document.body.appendChild(overlay);
}
