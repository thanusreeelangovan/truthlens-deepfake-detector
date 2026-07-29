/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        forensic: {
          bg: '#0a0e14',
          panel: '#111722',
          border: '#1e2733',
          accent: '#3ddc97',
          warn: '#ff5c5c',
          muted: '#5b6675',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['"Inter"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}