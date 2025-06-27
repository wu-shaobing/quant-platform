/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}'
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 品牌色
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554'
        },
        
        // 金融专用色
        financial: {
          // 涨跌色 (中国市场)
          up: '#ff4d4f',
          down: '#52c41a',
          neutral: '#8c8c8c',
          
          // 美股涨跌色
          'us-up': '#00d632',
          'us-down': '#ff3232',
          
          // 背景色
          'bg-primary': 'var(--el-bg-color)',
          'bg-secondary': 'var(--el-bg-color-page)',
          'bg-tertiary': 'var(--el-fill-color-light)',
          
          // 边框色
          'border-light': 'var(--el-border-color-light)',
          'border-medium': 'var(--el-border-color)',
          'border-dark': 'var(--el-border-color-darker)'
        },
        
        // 图表色系
        chart: {
          'line-1': '#5470c6',
          'line-2': '#91cc75',
          'line-3': '#fac858',
          'line-4': '#ee6666',
          'line-5': '#73c0de',
          'line-6': '#3ba272',
          'line-7': '#fc8452',
          'line-8': '#9a60b4',
          'line-9': '#ea7ccc'
        }
      },
      
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif'
        ],
        mono: [
          'JetBrains Mono',
          'Fira Code',
          'Monaco',
          'Consolas',
          'Liberation Mono',
          'Courier New',
          'monospace'
        ],
        financial: [
          'DIN',
          'Arial',
          'sans-serif'
        ]
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
        
        // 金融数据字体
        'financial-xs': ['0.75rem', { lineHeight: '1rem', letterSpacing: '0.025em' }],
        'financial-sm': ['0.875rem', { lineHeight: '1.25rem', letterSpacing: '0.025em' }],
        'financial-base': ['1rem', { lineHeight: '1.5rem', letterSpacing: '0.025em' }],
        'financial-lg': ['1.125rem', { lineHeight: '1.75rem', letterSpacing: '0.025em' }]
      },
      
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem'
      },
      
      borderRadius: {
        'financial': 'var(--el-border-radius-base)'
      },
      
      boxShadow: {
        'financial': 'var(--el-box-shadow-light)',
        'financial-hover': 'var(--el-box-shadow)',
        'financial-active': '0 0 0 3px rgba(59, 130, 246, 0.1)'
      },
      
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'fade-out': 'fadeOut 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'price-flash': 'priceFlash 0.8s ease-out',
        'number-count': 'numberCount 1s ease-out',
        'pulse-soft': 'pulseSoft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' }
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' }
        },
        priceFlash: {
          '0%': { backgroundColor: 'rgba(59, 130, 246, 0.3)' },
          '100%': { backgroundColor: 'transparent' }
        },
        numberCount: {
          '0%': { transform: 'scale(1.1)' },
          '100%': { transform: 'scale(1)' }
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
      backdropBlur: {
        'xs': '2px',
      },
      gridTemplateColumns: {
        'fill-60': 'repeat(auto-fill, minmax(60px, 1fr))',
        'fill-80': 'repeat(auto-fill, minmax(80px, 1fr))',
        'fill-100': 'repeat(auto-fill, minmax(100px, 1fr))',
      },
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
    
    // 自定义金融组件
    function({ addComponents, theme }) {
      addComponents({
        '.price-up': {
          color: theme('colors.financial.up')
        },
        '.price-down': {
          color: theme('colors.financial.down')
        },
        '.price-neutral': {
          color: theme('colors.financial.neutral')
        },
        '.financial-card': {
          backgroundColor: theme('colors.financial.bg-primary'),
          borderRadius: theme('borderRadius.financial'),
          boxShadow: theme('boxShadow.financial'),
          border: `1px solid ${theme('colors.financial.border-light')}`
        },
        '.financial-table': {
          '& th': {
            backgroundColor: theme('colors.financial.bg-secondary'),
            fontWeight: theme('fontWeight.semibold'),
            fontSize: theme('fontSize.sm')[0],
            padding: theme('spacing.3')
          },
          '& td': {
            fontSize: theme('fontSize.sm')[0],
            padding: theme('spacing.3'),
            borderBottom: `1px solid ${theme('colors.financial.border-light')}`
          }
        }
      })
    }
  ],
  corePlugins: {
    preflight: false,
  },
} 