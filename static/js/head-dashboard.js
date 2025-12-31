tailwind.config = {
  theme: {
    extend: {
      colors: {
        brown: {
          50: "#fdf8f6",
          100: "#f2e8e5",
          200: "#eaddd7",
          300: "#e0cec7",
          400: "#d2bab0",
          500: "#bfa094",
          600: "#a18072",
          700: "#8b6e5e",
          800: "#7d5d4f",
          900: "#603b2b",
        },
        landlord: {
          primary: "#603b2b",
          secondary: "#8b6e5e",
          accent: "#d4a574",
          light: "#f8f3e6",
          dark: "#2c1810",
        },
      },
      fontFamily: {
        serif: ["DM Sans", "serif"],
        sans: ["Inter", "sans-serif"],
      },
      animation: {
        float: "float 3s ease-in-out infinite",
        "pulse-slow": "pulse 3s ease-in-out infinite",
        "slide-in": "slideIn 0.3s ease-out",
        "bounce-slow": "bounce 2s infinite",
        gradient: "gradient 3s ease infinite",
      },
    },
  },
};
