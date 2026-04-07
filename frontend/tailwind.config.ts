import type { Config } from 'tailwindcss';
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: { colors: { primary: { DEFAULT: '#0f172a' }, accent: { DEFAULT: '#22c55e' } }, fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] } } },
  plugins: [],
} satisfies Config;
