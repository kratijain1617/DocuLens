import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#F3F5F8",
        ink: "#122033",
        navy: {
          DEFAULT: "#0E1C36",
          mid: "#1A3A68",
        },
        iris: "#5146C8",
        line: "#E3E8EF",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Segoe UI", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
      },
      boxShadow: {
        card: "0 16px 40px rgba(14, 28, 54, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
