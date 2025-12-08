

// Back to Top Button
const backToTopButton = document.getElementById("back-to-top");

window.addEventListener("scroll", () => {
  if (window.pageYOffset > 300) {
    backToTopButton.classList.remove("opacity-0", "translate-y-10");
    backToTopButton.classList.add("opacity-100", "translate-y-0");
  } else {
    backToTopButton.classList.remove("opacity-100", "translate-y-0");
    backToTopButton.classList.add("opacity-0", "translate-y-10");
  }
});

backToTopButton.addEventListener("click", () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
});

// Mobile menu toggle
document.getElementById("menu-toggle").addEventListener("click", function () {
  document.getElementById("mobile-menu").classList.toggle("hidden");
});

// Scroll animations
const fadeElements = document.querySelectorAll(".fade-in");
const slideLeftElements = document.querySelectorAll(".slide-in-left");
const slideRightElements = document.querySelectorAll(".slide-in-right");
const scaleElements = document.querySelectorAll(".scale-in");

const observerOptions = {
  threshold: 0.1,
  rootMargin: "0px 0px -50px 0px",
};

const observer = new IntersectionObserver(function (entries) {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add("appear");
    }
  });
}, observerOptions);

fadeElements.forEach((el) => observer.observe(el));
slideLeftElements.forEach((el) => observer.observe(el));
slideRightElements.forEach((el) => observer.observe(el));
scaleElements.forEach((el) => observer.observe(el));

// Form navigation
const formSteps = document.querySelectorAll(".form-step");
const progressFill = document.getElementById("progress-fill");
const progressPercent = document.getElementById("progress-percent");
let currentStep = 1;
const totalSteps = formSteps.length - 1;

// Phone verification modal
const verificationModal = document.createElement("div");
verificationModal.innerHTML = `
        <div id="verification-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50 flex items-center justify-center p-4">
            <div class="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl">
                <div class="text-center mb-6">
                    <div class="w-16 h-16 bg-brown-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-mobile-alt text-brown-900 text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-brown-900 mb-2">Hakiki Nambari Ya Simu</h3>
                    <p class="text-brown-700" id="verification-message">Tumetuma msimbo wa uthibitisho kwenye nambari yako ya simu.</p>
                </div>
                
                <div class="space-y-4">
                    <div id="verification-error" class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg hidden"></div>
                    
                    <div class="text-center mb-4">
                        <div class="text-2xl font-mono font-bold text-brown-900 mb-2" id="verification-code-display">-----</div>
                        <div class="text-sm text-brown-600" id="countdown-timer">Msimbo utaisha muda wake baada ya: <span id="timer">10:00</span></div>
                    </div>
                    
                    <div class="grid grid-cols-6 gap-2 mb-4">
                        <input type="text" maxlength="1" class="verification-digit h-12 w-12 text-center text-2xl font-bold border-2 border-brown-300 rounded-lg focus:border-brown-700 focus:outline-none" data-index="0">
                        <input type="text" maxlength="1" class="verification-digit h-12 w-12 text-center text-2xl font-bold border-2 border-brown-300 rounded-lg focus:border-brown-700 focus:outline-none" data-index="1">
                        <input type="text" maxlength="1" class="verification-digit h-12 w-12 text-center text-2xl font-bold border-2 border-brown-300 rounded-lg focus:border-brown-700 focus:outline-none" data-index="2">
                        <input type="text" maxlength="1" class="verification-digit h-12 w-12 text-center text-2xl font-bold border-2 border-brown-300 rounded-lg focus:border-brown-700 focus:outline-none" data-index="3">
                        <input type="text" maxlength="1" class="verification-digit h-12 w-12 text-center text-2xl font-bold border-2 border-brown-300 rounded-lg focus:border-brown-700 focus:outline-none" data-index="4">
                        <input type="text" maxlength="1" class="verification-digit h-12 w-12 text-center text-2xl font-bold border-2 border-brown-300 rounded-lg focus:border-brown-700 focus:outline-none" data-index="5">
                    </div>
                    
                    <div class="flex space-x-3">
                        <button type="button" id="resend-code-btn" class="flex-1 text-brown-900 font-semibold py-3 px-4 rounded-lg border border-brown-900 hover:bg-brown-50 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed">
                            <i class="fas fa-redo mr-2"></i>Tuma tena
                        </button>
                        <button type="button" id="verify-btn" class="flex-1 bg-brown-900 text-white font-semibold py-3 px-4 rounded-lg hover:bg-brown-800 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed">
                            <i class="fas fa-check mr-2"></i>Hakiki
                        </button>
                    </div>
                    
                    <button type="button" id="close-verification-btn" class="w-full text-brown-700 font-medium py-2 px-4 rounded-lg hover:bg-brown-50 transition-all duration-300">
                        Funga
                    </button>
                </div>
            </div>
        </div>
    `;
document.body.appendChild(verificationModal);
const verificationModalElement = document.getElementById("verification-modal");
const verificationDigits = verificationModalElement.querySelectorAll(
  ".verification-digit"
);
const verifyBtn = document.getElementById("verify-btn");
const resendBtn = document.getElementById("resend-code-btn");
const closeBtn = document.getElementById("close-verification-btn");
const verificationError = document.getElementById("verification-error");
const timerElement = document.getElementById("timer");
const verificationCodeDisplay = document.getElementById(
  "verification-code-display"
);

let currentPhone = "";
let verificationTimer = null;
let timeLeft = 600; // 10 minutes in seconds

// Load form data from localStorage
function loadFormData() {
  const savedData = localStorage.getItem("assessmentFormData");
  if (savedData) {
    const data = JSON.parse(savedData);

    // Fill personal information
    if (data.name) document.getElementById("name").value = data.name;
    if (data.email) document.getElementById("email").value = data.email;
    if (data.location)
      document.getElementById("location").value = data.location;
    if (data.phone) {
      document.getElementById("phone").value = data.phone;
      // Check if phone was previously verified
      checkPhoneVerificationStatus(data.phone);
    }

    // Fill current situation
    if (data.currentSituation) {
      document.getElementById("current-situation").value =
        data.currentSituation;
      const situationCard = document.querySelector(
        `.option-card[data-value="${data.currentSituation}"]`
      );
      if (situationCard) situationCard.classList.add("selected");
    }

    // Fill goals
    if (data.goals) {
      document.getElementById("goals").value = data.goals;
      const goalCard = document.querySelector(
        `.option-card[data-value="${data.goals}"]`
      );
      if (goalCard) goalCard.classList.add("selected");
    }

    // Fill challenges
    if (data.challenges) {
      const challengesArray = data.challenges.split(",");
      document.getElementById("challenges").value = data.challenges;

      challengesArray.forEach((challenge) => {
        const option = document.querySelector(
          `.checkbox-option[data-value="${challenge}"]`
        );
        if (option) {
          option.classList.add("selected");
          const checkIcon = option.querySelector(".fa-check");
          checkIcon.classList.add("text-brown-900");
          option
            .querySelector(".w-6")
            .classList.add("bg-brown-900", "border-brown-900");
        }
      });
    }

    // Fill solution
    if (data.solution) {
      document.getElementById("solution").value = data.solution;
    }
  }
}

// Save form data to localStorage
function saveFormData() {
  const formData = {
    name: document.getElementById("name").value,
    email: document.getElementById("email").value,
    location: document.getElementById("location").value,
    phone: document.getElementById("phone").value,
    currentSituation: document.getElementById("current-situation").value,
    goals: document.getElementById("goals").value,
    challenges: document.getElementById("challenges").value,
    solution: document.getElementById("solution").value,
  };

  localStorage.setItem("assessmentFormData", JSON.stringify(formData));
}

function updateProgress() {
  const progress = ((currentStep - 1) / (totalSteps - 1)) * 100;
  progressFill.style.width = `${progress}%`;
  progressPercent.textContent = `${Math.round(progress)}%`;
}

function showStep(stepNumber) {
  formSteps.forEach((step) => {
    step.classList.remove("active");
  });
  document.getElementById(`step-${stepNumber}`).classList.add("active");
  currentStep = stepNumber;
  updateProgress();
  saveFormData();
}

// Check if phone is verified
async function checkPhoneVerificationStatus(phone) {
  if (!phone) return false;

  try {
    const response = await fetch(
      `/tathmini/api/check-verification/?phone=${encodeURIComponent(phone)}`
    );
    const result = await response.json();

    if (result.success && result.verified) {
      // Phone is verified, mark as verified in localStorage
      const savedData = localStorage.getItem("assessmentFormData");
      if (savedData) {
        const data = JSON.parse(savedData);
        data.phoneVerified = true;
        localStorage.setItem("assessmentFormData", JSON.stringify(data));
      }
      return true;
    }
  } catch (error) {
    console.error("Error checking phone verification:", error);
  }
  return false;
}

// Show verification modal
async function showVerificationModal(phone) {
  currentPhone = phone;
  verificationError.classList.add("hidden");
  verificationCodeDisplay.textContent = "-----";
  timeLeft = 600;
  updateTimer();

  // Clear verification digits
  verificationDigits.forEach((digit) => (digit.value = ""));

  // Send verification code
  try {
    const response = await fetch("/tathmini/api/send-verification/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({ phone: phone }),
    });

    const result = await response.json();

    if (result.success) {
      verificationModalElement.classList.remove("hidden");
      verificationCodeDisplay.textContent = result.code; // Remove this in production!

      // Start timer
      startVerificationTimer();
    } else {
      showVerificationError(result.error || "Hitilafu katika kutuma msimbo.");
    }
  } catch (error) {
    showVerificationError("Hitilafu ya mtandao. Tafadhali jaribu tena.");
  }
}

// Start verification timer
function startVerificationTimer() {
  if (verificationTimer) clearInterval(verificationTimer);

  verificationTimer = setInterval(() => {
    timeLeft--;
    updateTimer();

    if (timeLeft <= 0) {
      clearInterval(verificationTimer);
      verifyBtn.disabled = true;
      resendBtn.disabled = false;
      verificationCodeDisplay.textContent = "-----";
    }
  }, 1000);
}

// Update timer display
function updateTimer() {
  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  timerElement.textContent = `${minutes.toString().padStart(2, "0")}:${seconds
    .toString()
    .padStart(2, "0")}`;
}

// Show verification error
function showVerificationError(message) {
  verificationError.textContent = message;
  verificationError.classList.remove("hidden");
}

// Verify phone with code
async function verifyPhone() {
  const code = Array.from(verificationDigits)
    .map((d) => d.value)
    .join("");

  if (code.length !== 6) {
    showVerificationError("Tafadhali ingiza msimbo wote (tarakimu 6).");
    return;
  }

  try {
    verifyBtn.disabled = true;
    verifyBtn.innerHTML =
      '<i class="fas fa-spinner fa-spin mr-2"></i>Inahakiki...';

    const response = await fetch("/tathmini/api/verify-phone/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({ phone: currentPhone, code: code }),
    });

    const result = await response.json();

    if (result.success) {
      // Phone verified successfully
      clearInterval(verificationTimer);
      verificationModalElement.classList.add("hidden");

      // Mark phone as verified in localStorage
      const savedData = localStorage.getItem("assessmentFormData");
      if (savedData) {
        const data = JSON.parse(savedData);
        data.phoneVerified = true;
        localStorage.setItem("assessmentFormData", JSON.stringify(data));
      }

      // Allow user to continue to next step
      showStep(2);

      // Show success notification
      showNotification("Nambari ya simu imehakikiwa kikamilifu!", "success");
    } else {
      showVerificationError(result.error || "Msimbo si sahihi.");
      verifyBtn.disabled = false;
    }
  } catch (error) {
    showVerificationError("Hitilafu ya mtandao. Tafadhali jaribu tena.");
    verifyBtn.disabled = false;
  } finally {
    verifyBtn.innerHTML = '<i class="fas fa-check mr-2"></i>Hakiki';
  }
}

// Show notification
function showNotification(message, type = "success") {
  const notification = document.createElement("div");
  notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300 ${
    type === "success"
      ? "bg-green-50 border border-green-200 text-green-800"
      : "bg-red-50 border border-red-200 text-red-800"
  }`;
  notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${
                  type === "success"
                    ? "fa-check-circle"
                    : "fa-exclamation-circle"
                } mr-2"></i>
                <span>${message}</span>
            </div>
        `;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.opacity = "0";
    notification.style.transform = "translateX(100%)";
    setTimeout(() => notification.remove(), 300);
  }, 5000);
}

// Verification digit input handling
verificationDigits.forEach((digit, index) => {
  digit.addEventListener("input", (e) => {
    // Only allow numbers
    e.target.value = e.target.value.replace(/[^0-9]/g, "");

    // Move to next digit if current is filled
    if (e.target.value.length === 1 && index < verificationDigits.length - 1) {
      verificationDigits[index + 1].focus();
    }

    // Enable verify button if all digits are filled
    const allFilled = Array.from(verificationDigits).every(
      (d) => d.value.length === 1
    );
    verifyBtn.disabled = !allFilled;
  });

  // Handle backspace
  digit.addEventListener("keydown", (e) => {
    if (e.key === "Backspace" && !digit.value && index > 0) {
      verificationDigits[index - 1].focus();
    }
  });

  // Handle paste
  digit.addEventListener("paste", (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").replace(/[^0-9]/g, "");

    if (pastedData.length === 6) {
      const digits = pastedData.split("");
      digits.forEach((d, i) => {
        if (verificationDigits[i]) {
          verificationDigits[i].value = d;
        }
      });
      verifyBtn.disabled = false;
      verificationDigits[5].focus();
    }
  });
});

// Event listeners for verification modal
verifyBtn.addEventListener("click", verifyPhone);

resendBtn.addEventListener("click", async () => {
  resendBtn.disabled = true;
  resendBtn.innerHTML =
    '<i class="fas fa-spinner fa-spin mr-2"></i>Inatumwa...';

  try {
    const response = await fetch("/tathmini/api/send-verification/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      body: JSON.stringify({ phone: currentPhone }),
    });

    const result = await response.json();

    if (result.success) {
      verificationCodeDisplay.textContent = result.code; // Remove this in production!
      timeLeft = 600;
      startVerificationTimer();
      verifyBtn.disabled = true;
      showNotification("Msimbo mpya umepelekwa!", "success");
    } else {
      showVerificationError(result.error || "Hitilafu katika kutuma msimbo.");
    }
  } catch (error) {
    showVerificationError("Hitilafu ya mtandao. Tafadhali jaribu tena.");
  } finally {
    resendBtn.disabled = false;
    resendBtn.innerHTML = '<i class="fas fa-redo mr-2"></i>Tuma tena';
  }
});

closeBtn.addEventListener("click", () => {
  verificationModalElement.classList.add("hidden");
  clearInterval(verificationTimer);
});

// Next step buttons with phone verification check
document.querySelectorAll(".next-step").forEach((button) => {
  button.addEventListener("click", async function () {
    if (currentStep === 1) {
      // Check if phone is filled and verified before proceeding
      const phone = document.getElementById("phone").value.trim();

      if (!phone) {
        // alert('Tafadhali ingiza nambari ya simu kabla ya kuendelea.');
        Toastify({
          text: "Tafadhali ingiza nambari ya simu kabla ya kuendelea.",
          duration: 5000,
          close: false,
          gravity: "top",
          position: "right",
          backgroundColor: "#FF4C4C",
          stopOnFocus: true,
        }).showToast();

        document.getElementById("phone").focus();
        return;
      }

      // Check if phone is already verified
      const isVerified = await checkPhoneVerificationStatus(phone);

      if (!isVerified) {
        // Show verification modal
        await showVerificationModal(phone);
        return;
      }
    }

    if (currentStep < totalSteps) {
      showStep(currentStep + 1);
    }
  });
});

// Previous step buttons
document.querySelectorAll(".prev-step").forEach((button) => {
  button.addEventListener("click", function () {
    if (currentStep > 1) {
      showStep(currentStep - 1);
    }
  });
});

// Option card selection
document.querySelectorAll(".option-card").forEach((card) => {
  card.addEventListener("click", function () {
    const parentStep = this.closest(".form-step");
    parentStep.querySelectorAll(".option-card").forEach((c) => {
      c.classList.remove("selected");
    });

    this.classList.add("selected");

    const hiddenInput = parentStep.querySelector('input[type="hidden"]');
    if (hiddenInput) {
      hiddenInput.value = this.getAttribute("data-value");
    }
    saveFormData();
  });
});

// Checkbox option selection
document.querySelectorAll(".checkbox-option").forEach((option) => {
  option.addEventListener("click", function () {
    this.classList.toggle("selected");

    const checkIcon = this.querySelector(".fa-check");
    if (this.classList.contains("selected")) {
      checkIcon.classList.add("text-brown-900");
      this.querySelector(".w-6").classList.add(
        "bg-brown-900",
        "border-brown-900"
      );
    } else {
      checkIcon.classList.remove("text-brown-900");
      this.querySelector(".w-6").classList.remove(
        "bg-brown-900",
        "border-brown-900"
      );
    }

    const parentStep = this.closest(".form-step");
    const hiddenInput = parentStep.querySelector('input[type="hidden"]');
    if (hiddenInput) {
      const selectedValues = [];
      parentStep
        .querySelectorAll(".checkbox-option.selected")
        .forEach((opt) => {
          selectedValues.push(opt.getAttribute("data-value"));
        });
      hiddenInput.value = selectedValues.join(",");
    }
    saveFormData();
  });
});

// Form submission
document
  .getElementById("assessment-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const formData = {
      name: document.getElementById("name").value.trim(),
      email: document.getElementById("email").value.trim(),
      location: document.getElementById("location").value.trim(),
      phone: document.getElementById("phone").value.trim(),
      current_situation: document.getElementById("current-situation").value,
      goals: document.getElementById("goals").value,
      challenges: document.getElementById("challenges").value,
      solution: document.getElementById("solution").value.trim(),
    };

    if (!formData.name || !formData.email || !formData.phone) {
      // alert('Tafadhali jaza taarifa zako binafsi (jina, barua pepe, na nambari ya simu).');
      Toastify({
        text: "Tafadhali jaza taarifa zako binafsi (jina, barua pepe, na nambari ya simu).",
        duration: 5000,
        close: false,
        gravity: "top",
        position: "right",
        backgroundColor: "#FF4C4C",
        stopOnFocus: true,
      }).showToast();
      showStep(1);
      return;
    }

    try {
      const submitBtn = this.querySelector('button[type="submit"]');
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML =
        '<i class="fas fa-spinner fa-spin mr-2"></i>Inatumwa...';
      submitBtn.disabled = true;

      const response = await fetch("/tathmini/api/submit-assessment/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify(formData),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        localStorage.removeItem("assessmentFormData");
        showSuccessMessage(result.message);
      } else {
        throw new Error(
          result.error || "Hitilafu imetokea. Tafadhali jaribu tena."
        );
      }
    } catch (error) {
      Toastify({
        text: error.message,
        duration: 10000,
        close: false,
        gravity: "top",
        position: "right",
        backgroundColor: "#FF4C4C",
        stopOnFocus: true,
      }).showToast();

      //            alert('Hitilafu: ' + error.message);

      const submitBtn = document.querySelector('button[type="submit"]');
      submitBtn.innerHTML =
        'Tumiza Tathmini <i class="fas fa-paper-plane ml-2"></i>';
      submitBtn.disabled = false;
    }
  });

// Helper function to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Function to show custom success message
function showSuccessMessage(message) {
  const successDiv = document.getElementById("success-message");
  const messagePara = successDiv.querySelector("p");
  messagePara.innerHTML = message;

  formSteps.forEach((step) => {
    step.classList.remove("active");
  });
  successDiv.classList.add("active");

  progressFill.style.width = "100%";
  progressPercent.textContent = "100%";
}

// Initialize
updateProgress();
loadFormData();

// Auto-save on input change
document
  .querySelectorAll(
    'input[type="text"], input[type="email"], input[type="tel"], textarea'
  )
  .forEach((input) => {
    input.addEventListener("input", saveFormData);
  });

function hideStuff() {
    const allSections = document.querySelectorAll("section");
    
    allSections.forEach(sec => {
        if (sec.id !== "assessment") {
            sec.style.display = "none";
        }
    });

    // Make sure the target section stays visible
    const assessment = document.getElementById("assessment");
    if (assessment) {
        assessment.style.display = "block";
    }
}