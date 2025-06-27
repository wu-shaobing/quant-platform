/**
 * Vitest 测试设置文件
 */

import { beforeEach, vi } from 'vitest'
import { config } from '@vue/test-utils'
import ElementPlus from 'element-plus'

// 全局 mock 设置
beforeEach(() => {
  // Mock console methods
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
  
  // Mock window methods
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(), // deprecated
      removeListener: vi.fn(), // deprecated
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })

  // Mock ResizeObserver
  global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }))

  // Mock IntersectionObserver
  global.IntersectionObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }))

  // Mock requestAnimationFrame
  global.requestAnimationFrame = vi.fn().mockImplementation(cb => setTimeout(cb, 16))
  global.cancelAnimationFrame = vi.fn().mockImplementation(id => clearTimeout(id))

  // Mock performance
  Object.defineProperty(window, 'performance', {
    writable: true,
    value: {
      now: vi.fn(() => Date.now()),
      mark: vi.fn(),
      measure: vi.fn(),
      getEntriesByName: vi.fn(() => []),
      clearMarks: vi.fn(),
      clearMeasures: vi.fn(),
    },
  })

  // Mock localStorage
  const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn(),
  }
  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock
  })

  // Mock sessionStorage
  const sessionStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn(),
  }
  Object.defineProperty(window, 'sessionStorage', {
    value: sessionStorageMock
  })

  // Mock WebSocket
  global.WebSocket = vi.fn().mockImplementation(() => ({
    send: vi.fn(),
    close: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    readyState: 1, // OPEN
    CONNECTING: 0,
    OPEN: 1,
    CLOSING: 2,
    CLOSED: 3,
  }))

  // Mock fetch
  global.fetch = vi.fn()

  // Mock Image
  global.Image = vi.fn().mockImplementation(() => ({
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    src: '',
    onload: null,
    onerror: null,
  }))
})

// 配置 Vue Test Utils
config.global.plugins = [ElementPlus]

// 全局 stubs
config.global.stubs = {
  transition: false,
  'transition-group': false,
  'el-config-provider': false
}

// 全局 mocks
config.global.mocks = {
  $t: (key: string) => key,
  $route: {
    path: '/',
    query: {},
    params: {},
    hash: '',
    fullPath: '/',
    matched: [],
    meta: {},
    name: null
  },
  $router: {
    push: vi.fn(),
    replace: vi.fn(),
    go: vi.fn(),
    back: vi.fn(),
    forward: vi.fn(),
    resolve: vi.fn(),
    addRoute: vi.fn(),
    removeRoute: vi.fn(),
    hasRoute: vi.fn(),
    getRoutes: vi.fn(() => [])
  }
}

// 全局属性
config.global.provide = {
  // 可以在这里提供全局依赖
}

// Mock ECharts
vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    showLoading: vi.fn(),
    hideLoading: vi.fn(),
  })),
  registerTheme: vi.fn(),
  registerMap: vi.fn(),
  getInstanceByDom: vi.fn(),
  use: vi.fn(),
}))

// Mock Pinia
vi.mock('pinia', async () => {
  const actual = await vi.importActual('pinia')
  return {
    ...actual,
    createPinia: vi.fn(() => ({
      install: vi.fn(),
      use: vi.fn(),
      state: {},
    })),
  }
})

// Mock Vue Router
vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router')
  return {
    ...actual,
    useRouter: vi.fn(() => ({
      push: vi.fn(),
      replace: vi.fn(),
      go: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
    })),
    useRoute: vi.fn(() => ({
      path: '/',
      query: {},
      params: {},
      hash: '',
      fullPath: '/',
      matched: [],
      meta: {},
      name: null,
    })),
  }
})

// 测试工具函数
export const createMockUser = () => ({
  id: '1',
  username: 'testuser',
  email: 'test@example.com',
  token: 'mock-token'
})

export const createMockStock = () => ({
  symbol: '000001',
  name: '平安银行',
  market: 'SZ',
  currentPrice: 12.50,
  change: 0.25,
  changePercent: 0.02,
  volume: 1000000,
  turnover: 12500000,
  isTrading: true
})

export const createMockOrder = () => ({
  id: '1',
  symbol: '000001',
  side: 'buy' as const,
  type: 'limit' as const,
  quantity: 1000,
  price: 12.50,
  status: 'pending' as const,
  createdAt: new Date().toISOString()
})

export const createMockStrategy = () => ({
  id: '1',
  name: '测试策略',
  description: '这是一个测试策略',
  status: 'draft' as const,
  maxPosition: 0.5,
  stopLoss: 0.05,
  takeProfit: 0.1,
  createdAt: new Date().toISOString()
})

// 等待函数
export const waitFor = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// 模拟网络延迟
export const mockNetworkDelay = (ms = 100) => waitFor(ms)

// 清理函数
export const cleanup = () => {
  vi.clearAllMocks()
  vi.clearAllTimers()
  vi.restoreAllMocks()
}