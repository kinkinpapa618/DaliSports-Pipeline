/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        dali: {
          dark: '#0b0f19',
          card: '#121827',
          border: '#1e293b',
          accent: '#10b981',
          blue: '#3b82f6',
          orange: '#f97316',
          purple: '#8b5cf6'
        }
      }
    },
  },
  plugins: [],
}
