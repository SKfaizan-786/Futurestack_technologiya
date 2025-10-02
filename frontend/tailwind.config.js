/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          blue: '#4A90E2',
          teal: '#3AAFA9'
        },
        secondary: {
          green: '#88D498',
          cyan: '#A9D6E5'
        },
        gray: {
          900: '#1F2937',
          600: '#4B5563',
          400: '#9CA3AF'
        },
        status: {
          error: '#EF4444',
          success: '#10B981'
        }
      },
      fontFamily: {
        'sans': ['Inter', 'Source Sans Pro', 'system-ui', 'sans-serif']
      }
    }
  },
  plugins: [],
}
