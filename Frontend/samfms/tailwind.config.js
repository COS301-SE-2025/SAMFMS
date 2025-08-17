/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./src/**/*.{js,jsx,ts,tsx}', './public/index.html'],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          50: '#daeaf7',
          100: '#c5e0f5',
          200: '#a1cded',
          300: '#7db9e5',
          400: '#4fa4d7', // Updated to your requested color
          500: '#2A91CD',
          600: '#1178b9',
          700: '#0855b1',
          800: '#010e54',
          900: '#00022b',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      keyframes: {
        'accordion-down': {
          from: {height: 0},
          to: {height: 'var(--radix-accordion-content-height)'},
        },
        'accordion-up': {
          from: {height: 'var(--radix-accordion-content-height)'},
          to: {height: 0},
        },
        fadeIn: {
          '0%': {opacity: '0'},
          '100%': {opacity: '1'},
        },
        slideIn: {
          '0%': {transform: 'translateY(30px)', opacity: '0'},
          '100%': {transform: 'translateY(0)', opacity: '1'},
        },
        pulse: {
          '0%, 100%': {transform: 'scale(1)'},
          '50%': {transform: 'scale(1.05)'},
        },
        bounce: {
          '0%, 100%': {transform: 'translateY(0)'},
          '50%': {transform: 'translateY(-10px)'},
        },
        float: {
          '0%, 100%': {transform: 'translateY(0)'},
          '50%': {transform: 'translateY(-20px)'},
        },
        wave: {
          '0%': {backgroundPosition: '0% 50%'},
          '50%': {backgroundPosition: '100% 50%'},
          '100%': {backgroundPosition: '0% 50%'},
        },
        rotate3d: {
          '0%': {transform: 'perspective(1000px) rotateY(0deg)'},
          '100%': {transform: 'perspective(1000px) rotateY(360deg)'},
        },
        shimmer: {
          '0%': {backgroundPosition: '-200% 0'},
          '100%': {backgroundPosition: '200% 0'},
        },
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        fadeIn: 'fadeIn 0.8s ease-in forwards',
        slideIn: 'slideIn 1s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        pulse: 'pulse 2s infinite',
        bounce: 'bounce 2s ease-in-out infinite',
        float: 'float 6s ease-in-out infinite',
        wave: 'wave 10s ease infinite',
        rotate3d: 'rotate3d 20s linear infinite',
        shimmer: 'shimmer 3s linear infinite',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};
