(function () {
  const hour = new Date().getHours();
  let timeGreeting = "Habari";

  if (hour >= 4 && hour < 6) {
    timeGreeting = "Habari za alfajiri";
  } else if (hour >= 6 && hour < 11) {
    timeGreeting = "Habari za asubuhi";
  } else if (hour >= 11 && hour < 15) {
    timeGreeting = "Habari za mchana";
  } else if (hour >= 15 && hour < 19) {
    timeGreeting = "Habari za jioni";
  } else {
    timeGreeting = "Habari za usiku";
  }

  document.getElementById("greetingText").textContent = timeGreeting + ",";
})();

const canvas = document.getElementById("revenueChart");

if (canvas) {
  const labels = JSON.parse(canvas.dataset.labels);
  const data = JSON.parse(canvas.dataset.values);

  new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Mapato kwa huu Mwezi",
          data: data,
          tension: 0.35,
          borderColor: "#603b2b", // emerald-600
          backgroundColor: "#7d5d4f8f",
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: { beginAtZero: true },
      },
    },
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const mobileMenuToggle = document.getElementById("mobileMenuToggle");
  const closeSidebar = document.getElementById("closeSidebar");
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebarOverlay");

  mobileMenuToggle.addEventListener("click", function () {
    sidebar.classList.remove("-translate-x-full");
    sidebarOverlay.classList.remove("hidden");
  });

  closeSidebar.addEventListener("click", function () {
    sidebar.classList.add("-translate-x-full");
    sidebarOverlay.classList.add("hidden");
  });

  sidebarOverlay.addEventListener("click", function () {
    sidebar.classList.add("-translate-x-full");
    sidebarOverlay.classList.add("hidden");
  });

  // Close sidebar when clicking on a link (mobile)
  const sidebarLinks = sidebar.querySelectorAll("a");
  sidebarLinks.forEach((link) => {
    link.addEventListener("click", function () {
      if (window.innerWidth < 1024) {
        sidebar.classList.add("-translate-x-full");
        sidebarOverlay.classList.add("hidden");
      }
    });
  });

  // Handle window resize
  window.addEventListener("resize", function () {
    if (window.innerWidth >= 1024) {
      sidebar.classList.remove("-translate-x-full");
      sidebarOverlay.classList.add("hidden");
    }
  });
});

// Mobile sidebar toggle
const mobileMenuToggle = document.getElementById("mobileMenuToggle");
const closeSidebar = document.getElementById("closeSidebar");
const sidebar = document.getElementById("sidebar");
const sidebarOverlay = document.getElementById("sidebarOverlay");

mobileMenuToggle?.addEventListener("click", () => {
  sidebar.classList.remove("-translate-x-full");
  sidebarOverlay.classList.remove("hidden");
  document.body.style.overflow = "hidden";
});

closeSidebar?.addEventListener("click", () => {
  sidebar.classList.add("-translate-x-full");
  sidebarOverlay.classList.add("hidden");
  document.body.style.overflow = "auto";
});

sidebarOverlay?.addEventListener("click", () => {
  sidebar.classList.add("-translate-x-full");
  sidebarOverlay.classList.add("hidden");
  document.body.style.overflow = "auto";
});

// Update current date and time
function updateDateTime() {
  const now = new Date();
  const options = {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  };
  document.getElementById("currentDateTime").textContent =
    now.toLocaleDateString("en-US", options);
}
updateDateTime();
setInterval(updateDateTime, 60000); // Update every minute

// Add fun hover effects to all cards
document.addEventListener("DOMContentLoaded", function () {
  const cards = document.querySelectorAll(".bg-white");
  cards.forEach((card) => {
    if (!card.classList.contains("no-hover")) {
      card.classList.add("hover-lift", "transition-all", "duration-300");
    }
  });

  // Add confetti on special interactions
  const funButtons = document.querySelectorAll("button, a");
  funButtons.forEach((btn) => {
    btn.addEventListener("click", function (e) {
      if (this.classList.contains("fun")) {
        e.preventDefault();
        createConfetti();
        setTimeout(() => {
          window.location.href = this.href;
        }, 800);
      }
    });
  });
});

// Fun confetti effect
function createConfetti() {
  const colors = ["#603b2b", "#8b6e5e", "#d4a574", "#f8f3e6"];
  for (let i = 0; i < 50; i++) {
    const confetti = document.createElement("div");
    confetti.style.cssText = `
                    position: fixed;
                    width: 10px;
                    height: 10px;
                    background: ${
                      colors[Math.floor(Math.random() * colors.length)]
                    };
                    border-radius: ${Math.random() > 0.5 ? "50%" : "0"};
                    z-index: 9999;
                    pointer-events: none;
                    left: ${Math.random() * 100}vw;
                    top: -20px;
                    animation: fall ${Math.random() * 2 + 1}s linear forwards;
                `;
    document.body.appendChild(confetti);
    setTimeout(() => confetti.remove(), 2000);
  }

  // Add CSS for falling animation
  const style = document.createElement("style");
  style.textContent = `
                @keyframes fall {
                    to {
                        transform: translateY(100vh) rotate(${
                          Math.random() * 360
                        }deg);
                        opacity: 0;
                    }
                }
            `;
  document.head.appendChild(style);
}

// Random motivational quotes
const quotes = [
  "Your properties are thriving! 🌟",
  "Great landlords make happy tenants! 🏡",
  "Revenue is looking good this month! 💰",
  "All systems are go! 🚀",
  "Another day, another successful property! 🎯",
];

// Randomly update header message sometimes
if (Math.random() > 0.7) {
  setTimeout(() => {
    const header = document.querySelector("h1.text-3xl");
    if (header) {
      const original = header.innerHTML;
      header.innerHTML = `<span class="gradient-text">${
        quotes[Math.floor(Math.random() * quotes.length)]
      }</span>`;
      setTimeout(() => {
        header.innerHTML = original;
      }, 3000);
    }
  }, 5000);
}
