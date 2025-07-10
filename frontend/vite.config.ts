import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'
// import eslint from 'vite-plugin-eslint'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const isProduction = mode === 'production'
  // const isDevelopment = mode === 'development'

  return {
    plugins: [
      vue({
        script: {
          defineModel: true,
          propsDestructure: true
        }
      }),
      
      // 自动导入
      AutoImport({
        imports: [
          'vue',
          'vue-router',
          'pinia',
          {
            'element-plus': [
              'ElMessage',
              'ElMessageBox', 
              'ElNotification',
              'ElLoading'
            ],
            '@/utils/format/financial': [
              'formatCurrency',
              'formatPrice',
              'formatPercent',
              'formatVolume'
            ]
          }
        ],
        resolvers: [ElementPlusResolver()],
        dts: 'src/types/auto-imports.d.ts',
        eslintrc: {
          enabled: true,
          filepath: './.eslintrc-auto-import.json'
        }
      }),
      
      // 组件自动导入
      Components({
        resolvers: [
          ElementPlusResolver({
            importStyle: 'sass'
          })
        ],
        dts: 'src/types/components.d.ts',
        dirs: ['src/components'],
        extensions: ['vue', 'tsx'],
        include: [/\.vue$/, /\.vue\?vue/, /\.tsx$/]
      }),
      
      // 打包分析
      isProduction && visualizer({
        filename: 'dist/stats.html',
        open: false,
        gzipSize: true,
        brotliSize: true
      })
    ].filter(Boolean),

    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@components': resolve(__dirname, 'src/components'),
        '@views': resolve(__dirname, 'src/views'),
        '@stores': resolve(__dirname, 'src/stores'),
        '@utils': resolve(__dirname, 'src/utils'),
        '@api': resolve(__dirname, 'src/api'),
        '@types': resolve(__dirname, 'src/types'),
        '@assets': resolve(__dirname, 'src/assets'),
        '@composables': resolve(__dirname, 'src/composables'),
        '@layouts': resolve(__dirname, 'src/layouts'),
        '@router': resolve(__dirname, 'src/router'),
        '@plugins': resolve(__dirname, 'src/plugins'),
        '@config': resolve(__dirname, 'src/config'),
        '@directives': resolve(__dirname, 'src/directives')
      }
    },

    css: {
      preprocessorOptions: {
        scss: {
          // Remove additionalData to prevent global variable conflicts
        }
      }
    },

    server: {
      port: 5173,
      host: '0.0.0.0',
      open: false,
      cors: true,
      proxy: {
        '/api': {
          target: env['VITE_API_BASE_URL'] || 'http://localhost:8000',
          changeOrigin: true,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err)
            })
            proxy.on('proxyReq', (_proxyReq, req, _res) => {
              console.log('Sending Request to the Target:', req.method, req.url)
            })
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('Received Response from the Target:', proxyRes.statusCode, req.url)
            })
          }
        },
        '/ws': {
          target: env['VITE_WS_URL'] || 'ws://localhost:8000',
          ws: true,
          changeOrigin: true
        }
      }
    },

    build: {
      target: 'es2015',
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: !isProduction,
      minify: isProduction ? 'terser' : false,
      
      terserOptions: isProduction ? {
        compress: {
          drop_console: true,
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.info']
        }
      } : {},
      
      rollupOptions: {
        output: {
          chunkFileNames: 'assets/js/[name]-[hash].js',
          entryFileNames: 'assets/js/[name]-[hash].js',
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name?.split('.') || []
            const extType = info[info.length - 1]
            
            if (/\.(mp4|webm|ogg|mp3|wav|flac|aac)(\?.*)?$/i.test(assetInfo.name || '')) {
              return 'assets/media/[name]-[hash].[ext]'
            }
            
            if (/\.(png|jpe?g|gif|svg)(\?.*)?$/i.test(assetInfo.name || '')) {
              return 'assets/images/[name]-[hash].[ext]'
            }
            
            if (/\.(woff2?|eot|ttf|otf)(\?.*)?$/i.test(assetInfo.name || '')) {
              return 'assets/fonts/[name]-[hash].[ext]'
            }
            
            return `assets/${extType}/[name]-[hash].[ext]`
          },
          
          manualChunks: (id) => {
            // Vue 框架
            if (id.includes('node_modules/vue') || 
                id.includes('node_modules/vue-router') || 
                id.includes('node_modules/pinia')) {
              return 'vue-vendor'
            }
            
            // UI 组件库
            if (id.includes('node_modules/element-plus')) {
              return 'ui-vendor'
            }
            
            // 图表库
            if (id.includes('node_modules/echarts')) {
              return 'chart-vendor'
            }
            
            // 工具库
            if (id.includes('node_modules/axios') ||
                id.includes('node_modules/lodash-es') ||
                id.includes('node_modules/dayjs') ||
                id.includes('node_modules/decimal.js') ||
                id.includes('node_modules/big.js') ||
                id.includes('node_modules/numeral')) {
              return 'utils-vendor'
            }
            
            // WebSocket
            if (id.includes('node_modules/socket.io-client')) {
              return 'socket-vendor'
            }
            
            // 页面路由按需加载
            if (id.includes('src/views/Dashboard')) {
              return 'page-dashboard'
            }
            if (id.includes('src/views/Market')) {
              return 'page-market'
            }
            if (id.includes('src/views/Trading')) {
              return 'page-trading'
            }
            if (id.includes('src/views/Strategy')) {
              return 'page-strategy'
            }
            if (id.includes('src/views/Backtest')) {
              return 'page-backtest'
            }
            
            // 其他第三方库
            if (id.includes('node_modules')) {
              return 'vendor'
            }
            
            // 默认情况
            return undefined
          }
        }
      },
      
      // 构建性能优化
      chunkSizeWarningLimit: 1000,
      reportCompressedSize: false
    },

    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'pinia',
        'element-plus',
        'echarts/core',
        'echarts/charts',
        'echarts/components',
        'echarts/renderers',
        'axios',
        'lodash-es',
        'dayjs',
        'decimal.js'
      ],
      exclude: ['@vueuse/core']
    },

    define: {
      __VUE_OPTIONS_API__: false,
      __VUE_PROD_DEVTOOLS__: false,
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false
    },

    // 开发时性能优化
    esbuild: {
      drop: isProduction ? ['console', 'debugger'] : []
    }
  }
})