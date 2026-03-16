/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./dashboardd/templates/**/*.html",
    "./tenant_portal/templates/**/*.html",
    "./yuzzaz/templates/**/*.html",
    "./tathmini/templates/**/*.html",
  ],
  theme: {
    extend: {
      colors: {
        brown: {
          50: "#fdf8f3",
          100: "#f5e8d8",
          200: "#e8cba8",
          300: "#d9a87a",
          400: "#c67c3b",
          500: "#a0602e",
          600: "#7a4520",
          700: "#5c3317",
          800: "#3e2210",
          900: "#2c1a0e",
        },
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        serif: ["Playfair Display", "serif"],
      },
    },
  },
  plugins: [],
};
