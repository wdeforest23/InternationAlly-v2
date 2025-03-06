/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': {
          DEFAULT: '#14B8A6',
          dark: '#0F766E',
          light: '#99F6E4',
        }
      }
    },
  },
  plugins: [],
} 