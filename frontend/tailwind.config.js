/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#00ff88",
          dark: "#00cc6a",
          light: "#33ffaa",
          glow: "rgba(0, 255, 136, 0.3)",
        },
        surface: {
          DEFAULT: "#0a1a2e",
          light: "#112240",
          lighter: "#1a3355",
          card: "rgba(17, 34, 64, 0.8)",
        },
        accent: {
          cyan: "#00e5ff",
          teal: "#00bfa5",
        },
      },
      fontFamily: {
        urdu: ['"Noto Nastaliq Urdu"', '"Jameel Noori Nastaleeq"', "serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out forwards",
        "slide-up": "slideUp 0.4s ease-out forwards",
        "slide-left": "slideLeft 0.4s ease-out forwards",
        "slide-right": "slideRight 0.4s ease-out forwards",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow-border": "glowBorder 2s ease-in-out infinite alternate",
        typing: "typing 1.2s ease-in-out infinite",
        "scan-line": "scanLine 3s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideLeft: {
          "0%": { opacity: "0", transform: "translateX(20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        slideRight: {
          "0%": { opacity: "0", transform: "translateX(-20px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        glowBorder: {
          "0%": { boxShadow: "0 0 5px rgba(0,255,136,0.3), inset 0 0 5px rgba(0,255,136,0.1)" },
          "100%": { boxShadow: "0 0 15px rgba(0,255,136,0.5), inset 0 0 10px rgba(0,255,136,0.2)" },
        },
        typing: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.3" },
        },
        scanLine: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
      },
      backgroundImage: {
        "circuit-pattern": "url('/circuit-bg.svg')",
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};
