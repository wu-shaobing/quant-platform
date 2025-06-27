import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
export default defineConfig({
    plugins: [
        vue({
            script: {
                defineModel: true,
                propsDestructure: true
            }
        })
    ],
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
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: ['./vitest.setup.ts'],
        // 覆盖率配置
        coverage: {
            provider: 'v8',
            reporter: ['text', 'json', 'html', 'lcov'],
            reportsDirectory: './coverage',
            exclude: [
                'node_modules/',
                'dist/',
                'coverage/',
                '**/*.d.ts',
                '**/*.config.*',
                '**/auto-imports.d.ts',
                '**/components.d.ts'
            ],
            thresholds: {
                global: {
                    branches: 70,
                    functions: 70,
                    lines: 70,
                    statements: 70
                }
            }
        },
        // 测试包含和排除
        include: [
            'src/**/*.{test,spec}.{js,ts,vue}',
            'tests/**/*.{test,spec}.{js,ts,vue}'
        ],
        exclude: [
            'node_modules/',
            'dist/',
            '.idea/',
            '.git/',
            '.cache/'
        ],
        // 测试超时
        testTimeout: 10000,
        hookTimeout: 10000,
        // 并发配置
        pool: 'threads',
        poolOptions: {
            threads: {
                singleThread: false,
                minThreads: 1,
                maxThreads: 4
            }
        },
        // 报告器
        reporters: ['verbose', 'json', 'html'],
        outputFile: {
            json: './test-results.json',
            html: './test-results.html'
        },
        // 监听模式配置
        watch: false,
        // 模拟配置
        clearMocks: true,
        restoreMocks: true,
        // 环境变量
        env: {
            NODE_ENV: 'test',
            VITE_API_BASE_URL: 'http://localhost:8000',
            VITE_WS_URL: 'ws://localhost:8000'
        }
    },
    // Vite 配置
    define: {
        __VUE_OPTIONS_API__: false,
        __VUE_PROD_DEVTOOLS__: false,
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false
    },
    // 依赖优化
    optimizeDeps: {
        include: [
            'vue',
            '@vue/test-utils',
            'element-plus',
            'echarts',
            'lodash-es',
            'dayjs',
            'decimal.js'
        ]
    }
});
