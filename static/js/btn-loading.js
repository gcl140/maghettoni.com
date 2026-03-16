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
