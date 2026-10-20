/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        ink: {
          50: '#f6f8f9',
          100: '#e9eef0',
          700: '#243943',
          800: '#172b34',
          900: '#0d2028',
          950: '#07171e',
        },
        // Chart identity colours, validated as a pair (colour-blind safe on white).
        observed: '#0d9488',
        filled: '#eb6834',
      },
      fontFamily: {
        sans: ['"Manrope"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}
