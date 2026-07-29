/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // "Evidence Locker" palette — warm darkroom, not cold hacker-terminal
        forensic: {
          bg: '#14110d',
          panel: '#1c1812',
          panelRaised: '#241f16',
          border: '#332c22',
          safelight: '#e8a33d',   // active/scanning state only
          real: '#4fd1c5',        // verdict: authentic
          fake: '#d64545',        // verdict: manipulated
          muted: '#8c8375',
          text: '#e7e2d8',
        },
      },
      fontFamily: {
        stamp: ['"Special Elite"', 'monospace'],  // case-file / typewriter headers
        sans: ['"IBM Plex Sans"', 'sans-serif'],   // body copy
        data: ['"IBM Plex Mono"', 'monospace'],    // timestamps, scores, hashes
      },
      backgroundImage: {
        'sprocket-strip': "repeating-linear-gradient(90deg, transparent 0 10px, #332c22 10px 12px)",
      },
    },
  },
  plugins: [],
}