(function () {
  // Auto-format phone number with +255 prefix
  var tel = document.getElementById('id_telephone');
  if (tel) {
    tel.addEventListener('input', function () {
      var value = tel.value.replace(/\s+/g, '');
      if (!value.startsWith('+255')) {
        value = value.replace(/^\+?0*/, '');
        value = '+255' + value;
      }
      if (value.startsWith('+2550')) {
        value = '+255' + value.slice(5);
      }
      tel.value = value;
    });
  }

  var phoneVerified = false;

  function getPhone() {
    var el = document.getElementById('id_telephone');
    return el ? el.value.trim() : '';
  }

  function getCsrf() {
    var el = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return el ? el.value : '';
  }

  function setSubmitReady(ready) {
    var btn = document.getElementById('submit-btn');
    if (!btn) return;
    phoneVerified = ready;
    var readyClasses = (btn.dataset.readyClass || '').split(' ');
    var disabledClasses = (btn.dataset.disabledClass || '').split(' ');
    if (ready) {
      btn.disabled = false;
      disabledClasses.forEach(function (c) { if (c) btn.classList.remove(c); });
      readyClasses.forEach(function (c) { if (c) btn.classList.add(c); });
      btn.innerHTML = '<i class="fas fa-user-plus text-sm"></i><span>Create Account</span>';
    } else {
      btn.disabled = true;
      readyClasses.forEach(function (c) { if (c) btn.classList.remove(c); });
      disabledClasses.forEach(function (c) { if (c) btn.classList.add(c); });
      btn.innerHTML = '<i class="fas fa-lock text-sm"></i><span>Verify phone to create account</span>';
    }
  }

  window.registerSendOTP = function (resend) {
    var phone = getPhone();
    if (!phone) { alert('Please enter your phone number first.'); return; }

    var btn = document.getElementById('send-otp-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Sending...'; }

    fetch('/home/otp/send/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ phone: phone }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (btn) { btn.disabled = false; btn.textContent = resend ? 'Resend OTP' : 'Send OTP'; }
        if (data.status === 'sent') {
          var section = document.getElementById('otp-section');
          var display = document.getElementById('otp-phone-display');
          var input = document.getElementById('otp-input');
          var err = document.getElementById('otp-error');
          var suc = document.getElementById('otp-success');
          if (section) section.classList.remove('hidden');
          if (display) display.textContent = phone;
          if (input) input.value = '';
          if (err) err.classList.add('hidden');
          if (suc) {
            if (resend) { suc.textContent = 'New OTP sent!'; suc.classList.remove('hidden'); }
            else suc.classList.add('hidden');
          }
        } else {
          alert(data.error || 'Failed to send OTP. Try again.');
        }
      })
      .catch(function () {
        if (btn) { btn.disabled = false; btn.textContent = resend ? 'Resend OTP' : 'Send OTP'; }
        alert('Network error. Please try again.');
      });
  };

  window.registerVerifyOTP = function () {
    var phone = getPhone();
    var code = (document.getElementById('otp-input') || {}).value || '';
    code = code.trim();

    var err = document.getElementById('otp-error');
    if (code.length !== 6) {
      if (err) { err.textContent = 'Enter the 6-digit code.'; err.classList.remove('hidden'); }
      return;
    }

    var btn = document.getElementById('verify-otp-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Verifying...'; }

    fetch('/home/otp/verify/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ phone: phone, code: code }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (btn) { btn.disabled = false; btn.textContent = 'Verify'; }
        var suc = document.getElementById('otp-success');
        var errEl = document.getElementById('otp-error');
        if (data.verified) {
          if (suc) { suc.textContent = 'Phone verified!'; suc.classList.remove('hidden'); }
          if (errEl) errEl.classList.add('hidden');
          var section = document.getElementById('otp-section');
          if (section) section.classList.add('hidden');
          var indicator = document.getElementById('phone-verified-indicator');
          if (indicator) { indicator.classList.remove('hidden'); indicator.style.display = 'flex'; }
          setSubmitReady(true);
        } else {
          if (errEl) { errEl.textContent = data.error || 'Invalid code.'; errEl.classList.remove('hidden'); }
          if (suc) suc.classList.add('hidden');
        }
      })
      .catch(function () {
        if (btn) { btn.disabled = false; btn.textContent = 'Verify'; }
        var errEl = document.getElementById('otp-error');
        if (errEl) { errEl.textContent = 'Network error. Try again.'; errEl.classList.remove('hidden'); }
      });
  };

  // Prevent submit if not verified
  var form = document.getElementById('register-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      if (!phoneVerified) {
        e.preventDefault();
        alert('Please verify your phone number before submitting.');
      }
    });
  }
})();
