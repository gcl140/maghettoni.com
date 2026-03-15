// Add this to your base.html or dashboard.js
document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.querySelector('input[name="q"]');
  const suggestionsBox = document.getElementById("searchSuggestions");
  const quickSearchButtons = document.querySelectorAll("[data-search]");

  if (searchInput && suggestionsBox) {
    let debounceTimer;

    searchInput.addEventListener("input", function (e) {
      clearTimeout(debounceTimer);
      const query = e.target.value.trim();

      if (query.length < 2) {
        suggestionsBox.classList.add("hidden");
        return;
      }

      debounceTimer = setTimeout(() => {
        fetch(`/dashboard/search/quick/?q=${encodeURIComponent(query)}`, {
          headers: {
            "X-Requested-With": "XMLHttpRequest",
          },
        })
          .then((response) => response.json())
          //   .then((data) => {
          //     if (data.results && data.results.length > 0) {
          //       // Update suggestions box
          //       suggestionsBox.classList.remove("hidden");
          //     } else {
          //       suggestionsBox.classList.add("hidden");
          //     }
          //   })

          .then((data) => {
            suggestionsBox.innerHTML = "";

            if (!data.results || data.results.length === 0) {
              suggestionsBox.classList.add("hidden");
              return;
            }

            data.results.forEach((item) => {
              const div = document.createElement("div");
              div.className =
                "px-4 py-2 cursor-pointer hover:bg-gray-100 flex flex-col";

              div.innerHTML = `
                        <span class="font-medium">${item.name}</span>
                        <span class="text-sm text-gray-500">${item.type} • ${item.detail}</span>
                        `;

              div.addEventListener("click", () => {
                if (item.url && item.url !== "#") {
                  window.location.href = item.url;
                }
              });

              suggestionsBox.appendChild(div);
            });

            suggestionsBox.classList.remove("hidden");
          })

          .catch((error) => {
            console.error("Search error:", error);
            suggestionsBox.classList.add("hidden");
          });
      }, 300);
    });

    // Close suggestions when clicking outside
    document.addEventListener("click", function (e) {
      if (
        !searchInput.contains(e.target) &&
        !suggestionsBox.contains(e.target)
      ) {
        suggestionsBox.classList.add("hidden");
      }
    });

    // Quick search button handlers
    quickSearchButtons.forEach((button) => {
      button.addEventListener("click", function () {
        searchInput.value = this.dataset.search;
        searchInput.closest("form").submit();
      });
    });

    // Keyboard navigation
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        suggestionsBox.classList.add("hidden");
      }
    });
  }
});

