/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        primary: "#4f46e5",
        "background-light": "#ffffff",
        "background-dark": "#171717",
        "surface-light": "#f8fafc",
        "surface-dark": "#262626",
        "bubble-user-light": "#e0e7ff",
        "bubble-user-dark": "#374151",
        "text-light": "#1f2937",
        "text-dark": "#f3f4f6",
        "text-secondary-light": "#6b7280",
        "text-secondary-dark": "#9ca3af",
      },
      fontFamily: {
        display: ["Roboto", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
      },
    },
  },
  plugins: [],
}