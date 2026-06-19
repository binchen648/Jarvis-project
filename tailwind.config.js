/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        jarvis: {
          blue: '#4F8CFF',
          purple: '#8B5CF6',
          cyan: '#06B6D4',
          teal: '#14B8A6',
        },
        surface: {
          DEFAULT: '#0A0A0F',
          sidebar: '#0F0F16',
          card: '#14141E',
          dialog: '#1A1A28',
          hover: '#1E1E30',
        },
        text: {
          primary: '#F1F1F6',
          secondary: '#9191A8',
          tertiary: '#5C5C72',
          placeholder: '#3A3A4E',
        },
        border: {
          DEFAULT: '#1E1E30',
          hover: '#2E2E44',
        },
        success: '#22C55E',
        warning: '#F59E0B',
        error: '#EF4444',
        info: '#4F8CFF',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'SF Mono', 'Fira Code', 'monospace'],
        display: ['SF Pro Display', 'Inter Display', 'sans-serif'],
      },
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },
      spacing: {
        '18': '4.5rem',
        'sidebar': '240px',
        'sidebar-collapsed': '64px',
        'topbar': '48px',
      },
      borderRadius: {
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
      },
      boxShadow: {
        'glow-purple': '0 0 20px rgba(139, 92, 246, 0.15)',
        'glow-blue': '0 0 20px rgba(79, 140, 255, 0.15)',
      },
      animation: {
        'pulse-idle': 'pulse-idle 4s ease-in-out infinite',
        'pulse-thinking': 'pulse-thinking 1.2s ease-in-out infinite',
        'pulse-alert': 'pulse-alert 0.8s ease-in-out infinite',
        'pulse-memory': 'pulse-memory 2s ease-in-out infinite',
      },
      keyframes: {
        'pulse-idle': {
          '0%, 100%': { opacity: '0.15', transform: 'scale(1)' },
          '50%': { opacity: '0.25', transform: 'scale(1.05)' },
        },
        'pulse-thinking': {
          '0%, 100%': { opacity: '0.3', transform: 'scale(1)', boxShadow: '0 0 12px rgba(139, 92, 246, 0.15)' },
          '50%': { opacity: '0.6', transform: 'scale(1.08)', boxShadow: '0 0 24px rgba(139, 92, 246, 0.3)' },
        },
        'pulse-alert': {
          '0%, 100%': { opacity: '0.5', transform: 'scale(1)', boxShadow: '0 0 16px rgba(139, 92, 246, 0.2)' },
          '50%': { opacity: '1', transform: 'scale(1.12)', boxShadow: '0 0 36px rgba(139, 92, 246, 0.5)' },
        },
        'pulse-memory': {
          '0%, 100%': { opacity: '0.2', transform: 'scale(1)', boxShadow: '0 0 8px rgba(6, 182, 212, 0.1)' },
          '50%': { opacity: '0.5', transform: 'scale(1.06)', boxShadow: '0 0 20px rgba(6, 182, 212, 0.3)' },
        },
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [
      {
        "jarvis-dark": {
          "primary": "#4F8CFF",
          "primary-content": "#0A0A0F",
          "secondary": "#8B5CF6",
          "secondary-content": "#F1F1F6",
          "accent": "#06B6D4",
          "accent-content": "#0A0A0F",
          "neutral": "#14141E",
          "neutral-content": "#F1F1F6",
          "base-100": "#0A0A0F",
          "base-200": "#0F0F16",
          "base-300": "#1E1E30",
          "base-content": "#F1F1F6",
          "info": "#4F8CFF",
          "success": "#22C55E",
          "warning": "#F59E0B",
          "error": "#EF4444",
        },
      },
      "light",
      "dark",
    ],
  },
};
