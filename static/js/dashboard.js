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