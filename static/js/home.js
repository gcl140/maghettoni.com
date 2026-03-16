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
const stepOrder = [
  "step-1",
  "step-otp",
  "step-2",
  "step-3",
  "step-4",
  "step-5",
];
let currentStepId = "step-1";

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
    }

    // Fill current situation
    if (data.currentSituation) {
      document.getElementById("current-situation").value =
        data.currentSituation;
      const situationCard = document.querySelector(
        `.option-card[data-value="${data.currentSituation}"]`,
      );
      if (situationCard) situationCard.classList.add("selected");
    }

    // Fill goals
    if (data.goals) {
      document.getElementById("goals").value = data.goals;
      const goalCard = document.querySelector(
        `.option-card[data-value="${data.goals}"]`,
      );
      if (goalCard) goalCard.classList.add("selected");
    }

    // Fill challenges
    if (data.challenges) {
      const challengesArray = data.challenges.split(",");
      document.getElementById("challenges").value = data.challenges;

      challengesArray.forEach((challenge) => {
        const option = document.querySelector(
          `.checkbox-option[data-value="${challenge}"]`,
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
  const stepIndex = stepOrder.indexOf(currentStepId);
  const safeIndex = stepIndex >= 0 ? stepIndex : 0;
  const denominator = Math.max(stepOrder.length - 1, 1);
  const progress = (safeIndex / denominator) * 100;

  if (progressFill) {
    progressFill.style.width = `${progress}%`;
  }
  if (progressPercent) {
    progressPercent.textContent = `${Math.round(progress)}%`;
  }
}

function showAssessmentStep(stepId) {
  if (stepId === "success-message") {
    showSuccessMessage("Asante! Taarifa zako zimetumwa kwa mafanikio.");
    return;
  }

  if (!stepOrder.includes(stepId)) {
    return;
  }

  formSteps.forEach((step) => {
    step.classList.remove("active");
  });

  const targetStep = document.getElementById(stepId);
  if (!targetStep) {
    return;
  }

  targetStep.classList.add("active");
  currentStepId = stepId;
  updateProgress();
  saveFormData();
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

// Next step buttons with phone verification check
document.querySelectorAll(".next-step").forEach((button) => {
  button.addEventListener("click", function () {
    const currentIndex = stepOrder.indexOf(currentStepId);
    if (currentIndex >= 0 && currentIndex < stepOrder.length - 1) {
      showAssessmentStep(stepOrder[currentIndex + 1]);
    }
  });
});

// Previous step buttons
document.querySelectorAll(".prev-step").forEach((button) => {
  button.addEventListener("click", function () {
    const currentIndex = stepOrder.indexOf(currentStepId);
    if (currentIndex > 0) {
      showAssessmentStep(stepOrder[currentIndex - 1]);
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
        "border-brown-900",
      );
    } else {
      checkIcon.classList.remove("text-brown-900");
      this.querySelector(".w-6").classList.remove(
        "bg-brown-900",
        "border-brown-900",
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
      showAssessmentStep("step-1");
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
          result.error || "Hitilafu imetokea. Tafadhali jaribu tena.",
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
  if (!successDiv) {
    return;
  }

  const messagePara = successDiv.querySelector("p");
  if (messagePara) {
    messagePara.innerHTML = message;
  }

  formSteps.forEach((step) => {
    step.classList.remove("active");
  });
  successDiv.classList.add("active");
  currentStepId = "success-message";

  if (progressFill) {
    progressFill.style.width = "100%";
  }
  if (progressPercent) {
    progressPercent.textContent = "100%";
  }
}

// Initialize
const activeStep = document.querySelector(".form-step.active");
if (activeStep && stepOrder.includes(activeStep.id)) {
  currentStepId = activeStep.id;
}

window.showAssessmentStep = showAssessmentStep;
updateProgress();
loadFormData();

// Auto-save on input change
document
  .querySelectorAll(
    'input[type="text"], input[type="email"], input[type="tel"], textarea',
  )
  .forEach((input) => {
    input.addEventListener("input", saveFormData);
  });

function hideStuff() {
  const allSections = document.querySelectorAll("section");

  allSections.forEach((sec) => {
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
