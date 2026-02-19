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
          DEFAULT: "#C8A96E",
          dark: "#A07840",
          light: "#E0C88A",
          glow: "rgba(200, 169, 110, 0.4)",
        },
        mughal: {
          red: "#8B1A1A",
          "red-dark": "#5C0F0F",
          "red-light": "#B03030",
          gold: "#C8A96E",
          "gold-dark": "#A07840",
          "gold-light": "#E8D4A0",
          ivory: "#F5F0E8",
          "ivory-dark": "#E0D8C8",
          lapis: "#1A2744",
          "lapis-dark": "#0F1830",
          "lapis-light": "#253660",
          emerald: "#2D6A4F",
          marble: "rgba(245, 240, 232, 0.08)",
          "marble-light": "rgba(245, 240, 232, 0.15)",
        },
        surface: {
          DEFAULT: "#1A0A05",
          light: "#2A1510",
          lighter: "#3D2018",
          card: "rgba(42, 21, 16, 0.92)",
        },
        accent: {
          cyan: "#C8A96E",
          teal: "#2D6A4F",
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
        "glow-border": "glowBorder 3s ease-in-out infinite alternate",
        typing: "typing 1.2s ease-in-out infinite",
        "sun-rotate": "sunRotate 20s linear infinite",
        "ray-pulse": "rayPulse 3s ease-in-out infinite",
        "blind-open": "blindOpen 0.4s ease-out forwards",
        "star-twinkle": "starTwinkle 2s ease-in-out infinite",
        "float": "floatAnim 4s ease-in-out infinite",
        "arch-glow": "archGlow 3s ease-in-out infinite alternate",
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
          "0%": { boxShadow: "0 0 8px rgba(200,169,110,0.3), inset 0 0 8px rgba(200,169,110,0.1)" },
          "100%": { boxShadow: "0 0 20px rgba(200,169,110,0.6), inset 0 0 15px rgba(200,169,110,0.2)" },
        },
        typing: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.3" },
        },
        sunRotate: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        rayPulse: {
          "0%, 100%": { opacity: "0.6", transform: "scaleY(1)" },
          "50%": { opacity: "1", transform: "scaleY(1.1)" },
        },
        blindOpen: {
          "0%": { transform: "scaleY(1)", transformOrigin: "top" },
          "100%": { transform: "scaleY(0)", transformOrigin: "top" },
        },
        starTwinkle: {
          "0%, 100%": { opacity: "0.3", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.3)" },
        },
        floatAnim: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        },
        archGlow: {
          "0%": { boxShadow: "0 0 10px rgba(200,169,110,0.2), inset 0 0 10px rgba(200,169,110,0.05)" },
          "100%": { boxShadow: "0 0 30px rgba(200,169,110,0.5), inset 0 0 20px rgba(200,169,110,0.15)" },
        },
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "mughal-arch": "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 50'%3E%3Cpath d='M0,50 Q50,0 100,50' fill='none' stroke='%23C8A96E' stroke-width='0.5'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
};
