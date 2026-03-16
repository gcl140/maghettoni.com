/* OTP helpers for the assessment form */
(function () {
  function showAssessmentStep(id) {
    if (typeof window.showAssessmentStep === "function") {
      window.showAssessmentStep(id);
      return;
    }

    document.querySelectorAll(".form-step").forEach(function (step) {
      step.classList.remove("active");
    });

    var el = document.getElementById(id);
    if (el) {
      el.classList.add("active");
    }
  }

  function getCsrfToken() {
    var tokenInput = document.querySelector(
      'input[name="csrfmiddlewaretoken"]',
    );
    return tokenInput ? tokenInput.value : "";
  }

  function parseResponseOrThrow(response) {
    var contentType = response.headers.get("content-type") || "";
    var isJson = contentType.indexOf("application/json") !== -1;

    if (isJson) {
      return response.json().then(function (data) {
        if (!response.ok) {
          var message = data.error || data.message || "HTTP " + response.status;
          throw new Error(message);
        }
        return data;
      });
    }

    return response.text().then(function (text) {
      if (!response.ok) {
        throw new Error(text || "HTTP " + response.status);
      }
      throw new Error("Response was not JSON as expected.");
    });
  }

  function requestOTP(resend) {
    var phone = (document.getElementById("phone") || {}).value;
    var name = (document.getElementById("name") || {}).value;
    var email = (document.getElementById("email") || {}).value;

    phone = (phone || "").trim();
    name = (name || "").trim();
    email = (email || "").trim();

    if (!name || !email || !phone) {
      showAlert("Tafadhali jaza jina, barua pepe, na nambari ya simu kwanza.", "warning");
      return;
    }

    var btn = document.getElementById("step1-next-btn");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Inatuma OTP...";
    }

    var csrfToken = getCsrfToken();

    fetch("/home/otp/send/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({ phone: phone }),
    })
      .then(parseResponseOrThrow)
      .then(function (data) {
        console.log("OTP send response:", data);
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = 'Endelea <i class="fas fa-arrow-right ml-2"></i>';
        }

        if (data.status === "sent") {
          var phoneDisplay = document.getElementById("otp-phone-display");
          var otpError = document.getElementById("otp-error");
          var otpSuccess = document.getElementById("otp-success");
          var otpInput = document.getElementById("otp-input");

          if (phoneDisplay) phoneDisplay.textContent = phone;
          if (otpError) otpError.classList.add("hidden");
          if (otpSuccess) otpSuccess.classList.add("hidden");
          if (otpInput) otpInput.value = "";

          if (resend && otpSuccess) {
            otpSuccess.textContent = "OTP mpya imetumwa!";
            otpSuccess.classList.remove("hidden");
          }

          if (typeof window.hideStuff === "function") {
            window.hideStuff();
          }

          showAssessmentStep("step-otp");
        } else {
          showAlert(data.error || "Imeshindwa kutuma OTP. Jaribu tena.", "error");
        }
      })
      .catch(function (error) {
        console.error("OTP send error:", error);

        if (btn) {
          btn.disabled = false;
          btn.innerHTML = 'Endelea <i class="fas fa-arrow-right ml-2"></i>';
        }

        var serverMessage = error && error.message ? error.message : "";
        showAlert(serverMessage || "Hitilafu ya mtandao. Jaribu tena.", "error");
      });
  }

  function verifyOTP() {
    var phone = (document.getElementById("phone") || {}).value;
    var code = (document.getElementById("otp-input") || {}).value;

    phone = (phone || "").trim();
    code = (code || "").trim();

    if (code.length !== 6) {
      var invalidCodeError = document.getElementById("otp-error");
      if (invalidCodeError) {
        invalidCodeError.textContent = "Ingiza tarakimu 6 sahihi.";
        invalidCodeError.classList.remove("hidden");
      }
      return;
    }

    var btn = document.getElementById("verify-otp-btn");
    if (btn) {
      btn.disabled = true;
      btn.textContent = "Inathibitisha...";
    }

    var csrfToken = getCsrfToken();

    fetch("/home/otp/verify/", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({ phone: phone, code: code }),
    })
      .then(parseResponseOrThrow)
      .then(function (data) {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = 'Thibitisha <i class="fas fa-check ml-2"></i>';
        }

        if (data.verified) {
          var verifiedFlag = document.getElementById("otp-verified-flag");
          var otpSuccess = document.getElementById("otp-success");
          var otpError = document.getElementById("otp-error");

          if (verifiedFlag) verifiedFlag.value = "1";
          if (otpSuccess) {
            otpSuccess.textContent = "Nambari imethibitishwa!";
            otpSuccess.classList.remove("hidden");
          }
          if (otpError) otpError.classList.add("hidden");

          setTimeout(function () {
            showAssessmentStep("step-2");
          }, 700);
        } else {
          var notVerifiedError = document.getElementById("otp-error");
          var otpSuccess2 = document.getElementById("otp-success");

          if (notVerifiedError) {
            notVerifiedError.textContent = data.error || "Msimbo si sahihi.";
            notVerifiedError.classList.remove("hidden");
          }
          if (otpSuccess2) otpSuccess2.classList.add("hidden");
        }
      })
      .catch(function (error) {
        console.error("OTP verify error:", error);

        if (btn) {
          btn.disabled = false;
          btn.innerHTML = 'Thibitisha <i class="fas fa-check ml-2"></i>';
        }

        var verifyError = document.getElementById("otp-error");
        if (verifyError) {
          verifyError.textContent =
            error && error.message
              ? error.message
              : "Hitilafu ya mtandao. Jaribu tena.";
          verifyError.classList.remove("hidden");
        }
      });
  }

  // Expose handlers for inline onclick attributes used by the template.
  window.requestOTP = requestOTP;
  window.verifyOTP = verifyOTP;
})();
