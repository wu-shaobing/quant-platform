/**
 * 应用配置文件
 * 集中管理所有配置项，包括API、UI、业务等配置
 */

// 环境变量
const env = import.meta.env

/**
 * 应用基础配置
 */
export const appConfig = {
  // 应用信息
  name: env.VITE_APP_TITLE || '量化投资平台',
  description: env.VITE_APP_DESCRIPTION || '专业的量化投资可视化平台',
  version: env.VITE_APP_VERSION || '1.0.0',
  
  // 开发环境
  isDev: env.DEV,
  isProd: env.PROD,
  
  // 功能开关
  enableMock: env.VITE_ENABLE_MOCK === 'true',
  enablePWA: env.VITE_ENABLE_PWA === 'true',
  enableDevtools: env.VITE_ENABLE_DEVTOOLS === 'true',
  
  // 默认设置
  defaultTheme: 'light',
  defaultLanguage: 'zh-CN',
  defaultTimezone: 'Asia/Shanghai'
} as const

/**
 * API 配置
 */
export const apiConfig = {
  // 基础URL
  baseURL: env.VITE_API_BASE_URL || '/api',
  
  // 请求超时
  timeout: Number(env.VITE_API_TIMEOUT) || 10000,
  
  // 重试配置
  retry: {
    times: 3,
    delay: 1000
  },
  
  // WebSocket配置
  websocket: {
    url: env.VITE_WS_URL || 'ws://localhost:8000/ws',
    reconnectInterval: 5000,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000
  }
} as const

/**
 * 认证配置
 */
export const authConfig = {
  // Token存储键名
  tokenKey: env.VITE_AUTH_TOKEN_KEY || 'access_token',
  refreshTokenKey: env.VITE_AUTH_REFRESH_TOKEN_KEY || 'refresh_token',
  
  // Token过期时间 (毫秒)
  tokenExpires: Number(env.VITE_AUTH_TOKEN_EXPIRES) || 7200000, // 2小时
  
  // 刷新Token时机 (距离过期多长时间开始刷新)
  refreshThreshold: 300000, // 5分钟
  
  // 登录页路径
  loginPath: '/login',
  
  // 默认重定向页面
  defaultRedirect: '/dashboard'
} as const

/**
 * 路由配置
 */
export const routeConfig = {
  // 路由模式
  mode: 'history',
  
  // 基础路径
  base: '/',
  
  // 页面标题模板
  titleTemplate: '%s - 量化投资平台',
  
  // 默认页面标题
  defaultTitle: '量化投资平台',
  
  // 路由切换动画
  transition: 'fade',
  
  // 缓存的路由组件
  keepAliveRoutes: [
    'Dashboard',
    'Market',
    'Strategy',
    'Trading'
  ]
} as const

/**
 * UI 配置
 */
export const uiConfig = {
  // 主题配置
  theme: {
    primary: '#3b82f6',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6'
  },
  
  // 布局配置
  layout: {
    headerHeight: 64,
    sidebarWidth: 256,
    sidebarCollapsedWidth: 64,
    footerHeight: 48
  },
  
  // 表格配置
  table: {
    pageSize: 20,
    pageSizes: [10, 20, 50, 100],
    maxHeight: 600
  },
  
  // 图表配置
  chart: {
    theme: 'light',
    renderer: 'canvas',
    animation: true,
    animationDuration: 300
  },
  
  // 消息配置
  message: {
    duration: 3000,
    showClose: true,
    center: false
  },
  
  // 加载配置
  loading: {
    text: '加载中...',
    spinner: 'el-icon-loading',
    background: 'rgba(0, 0, 0, 0.7)'
  }
} as const

/**
 * 业务配置
 */
export const businessConfig = {
  // 交易配置
  trading: {
    // 默认交易市场
    defaultMarket: 'A股',
    
    // 支持的市场
    markets: ['A股', '港股', '美股', '期货', '期权'],
    
    // 价格精度
    priceDecimalPlaces: 2,
    
    // 数量精度
    quantityDecimalPlaces: 0,
    
    // 最小交易单位
    minTradingUnit: 100,
    
    // 涨跌停限制
    priceLimit: 0.1, // 10%
    
    // 风险控制
    riskControl: {
      maxPositionRatio: 0.2, // 单只股票最大持仓比例 20%
      maxDailyLoss: 0.05,    // 单日最大亏损 5%
      maxDrawdown: 0.1       // 最大回撤 10%
    }
  },
  
  // 策略配置
  strategy: {
    // 支持的策略类型
    types: [
      'momentum',
      'mean_reversion', 
      'trend_following',
      'arbitrage',
      'machine_learning',
      'quantitative',
      'fundamental',
      'technical',
      'event_driven',
      'multi_factor'
    ],
    
    // 默认回测参数
    backtestDefaults: {
      startDate: '2023-01-01',
      endDate: '2024-01-01',
      initialCash: 1000000,
      commission: 0.0003,
      slippage: 0.001
    },
    
    // 性能指标计算
    metrics: {
      benchmarkSymbol: '000300.SH', // 沪深300作为基准
      riskFreeRate: 0.03,          // 无风险利率 3%
      tradingDaysPerYear: 252      // 年化交易日
    }
  },
  
  // 行情配置
  market: {
    // 默认显示的股票数量
    defaultStockCount: 50,
    
    // 刷新频率 (毫秒)
    refreshInterval: 3000,
    
    // K线周期
    klinePeriods: [
      { label: '1分钟', value: '1m' },
      { label: '5分钟', value: '5m' },
      { label: '15分钟', value: '15m' },
      { label: '30分钟', value: '30m' },
      { label: '1小时', value: '1h' },
      { label: '日线', value: '1d' },
      { label: '周线', value: '1w' },
      { label: '月线', value: '1M' }
    ],
    
    // 技术指标
    indicators: [
      'MA', 'EMA', 'MACD', 'RSI', 'KDJ', 
      'BOLL', 'CCI', 'WR', 'BIAS', 'ROC'
    ]
  }
} as const

/**
 * 监控配置
 */
export const monitorConfig = {
  // Sentry配置
  sentry: {
    dsn: env.VITE_SENTRY_DSN,
    environment: env.VITE_SENTRY_ENVIRONMENT || 'development',
    sampleRate: 0.1,
    beforeSend: (event: Record<string, unknown>) => {
      // 过滤敏感信息
      if (event.request?.url?.includes('password')) {
        return null
      }
      return event
    }
  },
  
  // 性能监控
  performance: {
    // 页面加载时间阈值 (毫秒)
    pageLoadThreshold: 3000,
    
    // API响应时间阈值 (毫秒)
    apiResponseThreshold: 2000,
    
    // 组件渲染时间阈值 (毫秒)
    componentRenderThreshold: 100,
    
    // 内存使用阈值 (MB)
    memoryUsageThreshold: 100
  },
  
  // 用户行为分析
  analytics: {
    trackingId: env.VITE_GA_TRACKING_ID,
    baiduId: env.VITE_BAIDU_ANALYTICS_ID,
    
    // 自动追踪事件
    autoTrack: {
      pageView: true,
      click: true,
      scroll: false,
      resize: false
    }
  }
} as const

/**
 * CDN 配置
 */
export const cdnConfig = {
  // CDN基础URL
  baseURL: env.VITE_CDN_URL || '',
  
  // 上传URL
  uploadURL: env.VITE_UPLOAD_URL || '/api/upload',
  
  // 支持的文件类型
  allowedTypes: [
    'image/jpeg',
    'image/png', 
    'image/gif',
    'image/webp',
    'application/pdf',
    'text/csv',
    'application/vnd.ms-excel'
  ],
  
  // 文件大小限制 (字节)
  maxFileSize: 10 * 1024 * 1024, // 10MB
  
  // 图片压缩质量
  imageQuality: 0.8
} as const

/**
 * 缓存配置
 */
export const cacheConfig = {
  // 本地存储键前缀
  storagePrefix: 'quant_',
  
  // 缓存过期时间 (毫秒)
  expiration: {
    userSession: 24 * 60 * 60 * 1000,    // 24小时
    marketData: 5 * 60 * 1000,           // 5分钟
    strategyData: 30 * 60 * 1000,        // 30分钟
    configData: 60 * 60 * 1000           // 1小时
  },
  
  // 缓存大小限制
  maxSize: {
    localStorage: 5 * 1024 * 1024,       // 5MB
    sessionStorage: 10 * 1024 * 1024,    // 10MB
    indexedDB: 50 * 1024 * 1024          // 50MB
  }
} as const

/**
 * 开发配置
 */
export const devConfig = {
  // 开发工具
  enableVueDevtools: appConfig.isDev && appConfig.enableDevtools,
  
  // Mock数据
  mockDelay: 500,
  
  // 调试选项
  debug: {
    api: appConfig.isDev,
    router: appConfig.isDev,
    store: appConfig.isDev,
    websocket: appConfig.isDev
  },
  
  // 热重载
  hotReload: {
    enabled: appConfig.isDev,
    port: 5173
  }
} as const

/**
 * 第三方服务配置
 */
export const serviceConfig = {
  // 地图服务
  map: {
    apiKey: env.VITE_MAP_API_KEY,
    defaultCenter: [116.397428, 39.90923], // 北京
    defaultZoom: 10
  },
  
  // TradingView
  tradingView: {
    symbolUrl: env.VITE_TRADING_VIEW_SYMBOL_URL,
    widgetOptions: {
      width: '100%',
      height: 600,
      symbol: '000001.SZ',
      interval: 'D',
      timezone: 'Asia/Shanghai',
      theme: 'light',
      style: '1',
      locale: 'zh',
      toolbar_bg: '#f1f3f6',
      enable_publishing: false,
      hide_top_toolbar: false,
      hide_legend: false,
      save_image: false
    }
  },
  
  // 新闻服务
  news: {
    apiUrl: env.VITE_NEWS_API_URL,
    refreshInterval: 5 * 60 * 1000, // 5分钟
    maxItems: 20
  },
  
  // 行情数据源
  marketData: {
    primarySource: env.VITE_MARKET_DATA_URL || 'ws://localhost:8000/ws',
    backupSources: [],
    timeout: 5000
  }
} as const

/**
 * 全局导出的配置对象
 */
export const config = {
  app: appConfig,
  api: apiConfig,
  auth: authConfig,
  route: routeConfig,
  ui: uiConfig,
  business: businessConfig,
  monitor: monitorConfig,
  cdn: cdnConfig,
  cache: cacheConfig,
  dev: devConfig,
  service: serviceConfig
}

export default config 