const colors = require("tailwindcss/colors");

module.exports = {
  darkMode: "class", // 启用深色模式切换
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#e6f7ff",
          100: "#b3e5fc",
          200: "#81d4fa",
          300: "#4fc3f7",
          400: "#29b6f6",
          500: "#03a9f4",
          600: "#039be5",
          700: "#0288d1",
          800: "#0277bd",
          900: "#01579b",
        },
        deepspace: {
          dark: "#000814",
          base: "#001d3d",
          light: "#003566",
        },
        nightpurple: {
          dark: "#1a0933",
          base: "#3d1765",
          light: "#7d3cff",
        },
        abyssgreen: {
          dark: "#001219",
          base: "#005f73",
          light: "#0a9396",
        },
        darkmatter: {
          dark: "#200122",
          base: "#3c1053",
          light: "#6a3093",
        },
        midnightnavy: {
          dark: "#0d1926",
          base: "#1e3d59",
          light: "#2e5984",
        },
        darkcosmos: {
          dark: "#0f0c29",
          base: "#302b63",
          light: "#24243e",
        },
        cyberneon: {
          dark: "#2c003e",
          base: "#5d0c7b",
          light: "#9d4edd",
        },
      },
      backgroundImage: {
        "gradient-deepspace":
          "linear-gradient(135deg, #000814 0%, #001d3d 50%, #003566 100%)",
        "gradient-nightpurple":
          "linear-gradient(135deg, #1a0933 0%, #3d1765 50%, #7d3cff 100%)",
        "gradient-abyssgreen":
          "linear-gradient(135deg, #001219 0%, #005f73 50%, #0a9396 100%)",
        "gradient-darkmatter":
          "linear-gradient(135deg, #200122 0%, #3c1053 50%, #6a3093 100%)",
        "gradient-midnightnavy":
          "linear-gradient(135deg, #0d1926 0%, #1e3d59 50%, #2e5984 100%)",
        "gradient-darkcosmos":
          "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
        "gradient-cyberneon":
          "linear-gradient(135deg, #2c003e 0%, #5d0c7b 50%, #9d4edd 100%)",
      },
      animation: {
        "gradient-pulse": "pulse 15s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "gradient-shift": "gradientShift 25s ease infinite",
      },
      keyframes: {
        gradientShift: {
          "0%, 100%": { "background-position": "0% 50%" },
          "50%": { "background-position": "100% 50%" },
        },
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    function ({ addUtilities }) {
      const newUtilities = {
        ".bg-gradient-animate": {
          backgroundSize: "200% 200%",
          animation: "gradientShift 25s ease infinite",
        },
        ".text-glow": {
          textShadow: "0 0 8px rgba(255, 255, 255, 0.5)",
        },
        ".card-glass": {
          backgroundColor: "rgba(15, 15, 35, 0.2)",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(255, 255, 255, 0.05)",
        },
      };
      addUtilities(newUtilities, ["responsive", "hover", "dark"]);
    },
  ],
};
