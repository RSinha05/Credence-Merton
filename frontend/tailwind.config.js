/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gold: '#D4AF37',
        dark: '#050505',
        surface: '#111111'
      },
      fontFamily: {
        sans: ['Manrope', 'sans-serif'],
        serif: ['Cormorant Garamond', 'serif'],
      }
    },
  },
  plugins: [],
}
