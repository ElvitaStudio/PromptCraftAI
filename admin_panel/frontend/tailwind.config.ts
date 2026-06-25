import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: "#08070d",
          900: "#101019",
          850: "#161522",
          800: "#1d1b2b"
        },
        violetGlow: "#8b5cf6"
      },
      boxShadow: {
        premium: "0 24px 80px rgba(139, 92, 246, 0.18)"
      }
    }
  },
  plugins: []
};

export default config;
