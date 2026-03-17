/* btn-loading.js — universal button loading state
 *
 * 1. Auto-intercepts every <form> submit and shows a spinner on the submit button.
 * 2. Exports window.btnLoading(btn, promise) for AJAX buttons.
 *
 * Opt out on any button with:  data-no-loading
 * Custom text on any button with:  data-loading-text="Saving..."
 */
(function () {
  'use strict';

  // ── Core helpers ──────────────────────────────────────────────────────────

  function setLoading(btn) {
    if (!btn || btn.disabled || btn.dataset.loading) return false;
    btn.dataset.loading = '1';
    btn.dataset.originalHtml = btn.innerHTML;
    btn.disabled = true;
    const text = btn.dataset.loadingText || 'Loading...';
    btn.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right:6px;"></i>' + text;
    return true;
  }

  function clearLoading(btn) {
    if (!btn || !btn.dataset.loading) return;
    btn.disabled = false;
    btn.innerHTML = btn.dataset.originalHtml || btn.innerHTML;
    delete btn.dataset.loading;
    delete btn.dataset.originalHtml;
  }

  // ── Global helper for AJAX / fetch buttons ────────────────────────────────
  // Usage: btnLoading(this, fetch(...).then(...))
  window.btnLoading = function (btn, promise) {
    if (!setLoading(btn)) return promise;
    return promise.finally(function () { clearLoading(btn); });
  };

  // ── onclick strings that indicate a button must NOT get a loading state ───
  var SKIP_ONCLICK = ['confirm', 'print', 'toggle', 'Toggle', 'close', 'Close', 'switch', 'Switch'];

  function shouldSkip(btn) {
    if (!btn) return true;
    if (btn.dataset.noLoading !== undefined) return true;
    var oc = btn.getAttribute('onclick') || '';
    return SKIP_ONCLICK.some(function (word) { return oc.indexOf(word) !== -1; });
  }

  // ── Auto form submit interception ─────────────────────────────────────────
  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!(form instanceof HTMLFormElement)) return;

    // Prefer the button that was actually clicked (modern browsers)
    var btn = e.submitter || null;

    // Fallback: first visible submit button in the form
    if (!btn) {
      btn = form.querySelector('button[type="submit"]:not([data-no-loading])') ||
            form.querySelector('input[type="submit"]:not([data-no-loading])');
    }

    if (!btn || btn.getAttribute('type') === 'reset') return;
    if (shouldSkip(btn)) return;

    setLoading(btn);
  }, true); // capture phase — runs before any onclick / onsubmit handlers

  // ── Restore buttons if browser restores page from bfcache (Back button) ──
  window.addEventListener('pageshow', function (e) {
    if (e.persisted) {
      document.querySelectorAll('[data-loading]').forEach(clearLoading);
    }
  });

})();

// ── Styled confirm dialog (replaces native confirm()) ─────────────────────────
// Usage: showConfirm('Are you sure?', function() { /* on confirm */ })
window.showConfirm = function (message, onConfirm) {
  var overlay = document.createElement('div');
  overlay.style.cssText =
    'position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:99998;display:flex;align-items:center;justify-content:center;';

  var box = document.createElement('div');
  box.style.cssText =
    'background:#fff;border-radius:16px;padding:28px 32px;max-width:420px;width:90%;box-shadow:0 20px 60px rgba(0,0,0,.25);font-family:inherit;';

  var icon = document.createElement('div');
  icon.style.cssText = 'width:48px;height:48px;border-radius:50%;background:#fef3c7;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;';
  icon.innerHTML = '<i class="fas fa-exclamation-triangle" style="color:#d97706;font-size:20px;"></i>';

  var text = document.createElement('p');
  text.style.cssText = 'text-align:center;font-size:15px;color:#374151;margin:0 0 24px;line-height:1.5;';
  text.textContent = message;

  var actions = document.createElement('div');
  actions.style.cssText = 'display:flex;gap:12px;justify-content:center;';

  var btnCancel = document.createElement('button');
  btnCancel.textContent = 'Cancel';
  btnCancel.style.cssText =
    'flex:1;padding:10px 20px;border:1.5px solid #d1d5db;background:#fff;color:#374151;border-radius:10px;font-size:14px;font-weight:500;cursor:pointer;';

  var btnOk = document.createElement('button');
  btnOk.textContent = 'Confirm';
  btnOk.style.cssText =
    'flex:1;padding:10px 20px;border:none;background:#7c5c45;color:#fff;border-radius:10px;font-size:14px;font-weight:600;cursor:pointer;';

  function close() { document.body.removeChild(overlay); }
  btnCancel.addEventListener('click', close);
  btnOk.addEventListener('click', function () { close(); onConfirm(); });
  overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });

  actions.appendChild(btnCancel);
  actions.appendChild(btnOk);
  box.appendChild(icon);
  box.appendChild(text);
  box.appendChild(actions);
  overlay.appendChild(box);
  document.body.appendChild(overlay);
  btnOk.focus();
};

// ── Styled alert helper (replaces native alert()) ─────────────────────────────
// Usage: showAlert('Something went wrong', 'error')
// Types: 'error' | 'success' | 'warning' | 'info'
window.showAlert = function (message, type) {
  var colors = {
    error:   '#dc2626',
    success: '#16a34a',
    warning: '#d97706',
    info:    '#2563eb',
  };
  if (typeof Toastify === 'function') {
    Toastify({
      text: message,
      duration: 4500,
      gravity: 'top',
      position: 'right',
      stopOnFocus: true,
      style: {
        background: colors[type] || colors.info,
        borderRadius: '10px',
        fontFamily: 'inherit',
        fontSize: '14px',
      },
    }).showToast();
  } else {
    window.alert(message); // fallback if Toastify not loaded
  }
};
