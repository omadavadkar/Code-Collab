/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        vscode: {
          bg: "#1e1e1e",
          panel: "#252526",
          sidebar: "#1f1f1f",
          border: "#3c3c3c",
          text: "#d4d4d4",
          muted: "#9da1a6",
          accent: "#007acc",
        },
      },
    },
  },
  plugins: [],
};
