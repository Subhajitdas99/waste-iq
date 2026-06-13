/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#13231B",
        leaf: "#29543A",
        moss: "#4E7C57",
        sand: "#F4E6C8",
        ember: "#E9894C",
        coral: "#F2B07B"
      },
      boxShadow: {
        glow: "0 24px 60px rgba(19, 35, 27, 0.14)"
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'DM Sans'", "sans-serif"]
      }
    }
  },
  plugins: []
};
