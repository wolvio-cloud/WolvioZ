import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Wolvio brand palette
        navy: {
          DEFAULT: "#1A2332",
          50: "#f0f2f5",
          100: "#d9dde6",
          200: "#b3bbcc",
          300: "#8c99b3",
          400: "#667799",
          500: "#1A2332",
          600: "#161e2b",
          700: "#121924",
          800: "#0e141d",
          900: "#0a0f16",
        },
        brand: {
          blue: "#2563EB",
          slate: "#475569",
          light: "#F1F5F9",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px -1px rgba(0,0,0,0.1)",
        "card-lg": "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)",
      },
    },
  },
  plugins: [],
};

export default config;
