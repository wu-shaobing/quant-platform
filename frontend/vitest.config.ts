/// <reference types="vitest" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  test: {
    // 测试环境配置
    environment: 'jsdom',
    
    // 全局测试设置
    globals: true,
    
    // 设置文件
    setupFiles: ['./tests/setup.ts'],
    
    // 包含的测试文件
    include: [
      'src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      'tests/unit/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'
    ],
    
    // 排除的文件
    exclude: [
      'node_modules',
      'dist',
      '.git',
      '.cache',
      'tests/e2e'
    ],
    
    // 覆盖率配置
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'tests/',
        'dist/',
        '**/*.d.ts',
        '**/*.config.{js,ts}',
        '**/index.ts', // 通常只是导出文件
        'src/main.ts', // 应用入口文件
        'src/types/', // 类型定义文件
        'src/assets/', // 静态资源
        '**/*.stories.{js,ts,jsx,tsx}', // Storybook 文件
        '**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}' // 测试文件本身
      ],
      // 覆盖率阈值
      thresholds: {
        global: {
          branches: 70,
          functions: 70,
          lines: 70,
          statements: 70
        }
      }
    },
    
    // 测试超时设置
    testTimeout: 10000,
    hookTimeout: 10000,
    
    // 并发设置
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        maxThreads: 4,
        minThreads: 1
      }
    },
    
    // 监听模式配置
    watch: {
      ignore: ['node_modules', 'dist', '.git']
    },
    
    // 报告器配置
    reporter: ['default', 'json', 'html'],
    outputFile: {
      json: './test-results/results.json',
      html: './test-results/index.html'
    },
    
    // 模拟配置
    clearMocks: true,
    restoreMocks: true,
    
    // 依赖处理
    deps: {
      inline: [
        '@vue/test-utils',
        'element-plus'
      ]
    }
  }
})