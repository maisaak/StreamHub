/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: { 500: "#7B2FF7", 600: "#6a1fd6" },
      },
    },
  },
  plugins: [],
};
