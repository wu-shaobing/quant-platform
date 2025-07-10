/**
 * 应用常量定义
 */

// API相关常量
export const API_CONFIG = {
  TIMEOUT: 10000,
  RETRY_COUNT: 3,
  RETRY_DELAY: 1000
} as const

// API路径常量
export const API_PATHS = {
  // 用户相关
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    PROFILE: '/auth/profile',
    REGISTER: '/auth/register'
  },
  
  // 市场数据
  MARKET: {
    QUOTE: '/market/quote',
    KLINE: '/market/kline',
    SEARCH: '/market/search',
    OVERVIEW: '/market/overview',
    SECTORS: '/market/sectors',
    STOCKS: '/market/stocks',
    INDICES: '/market/indices',
    NEWS: '/market/news',
    RANKING: '/market/ranking',
    ORDERBOOK: '/market/orderbook',
    TICK: '/market/tick',
    FINANCIAL: '/market/financial',
    INDICATOR: '/market/indicator',
    STATUS: '/market/status',
    CALENDAR: '/market/calendar',
    ANNOUNCEMENT: '/market/announcement',
    RESEARCH: '/market/research',
    SHAREHOLDERS: '/market/shareholders'
  },
  
  // 交易相关
  TRADING: {
    ACCOUNT: '/trading/account',
    POSITIONS: '/trading/positions',
    ORDERS: '/trading/orders',
    TRADES: '/trading/trades',
    SUBMIT: '/trading/submit',
    CANCEL: '/trading/cancel',
    MODIFY: '/trading/modify'
  },
  
  // 策略相关
  STRATEGY: {
    LIST: '/strategy/list',
    DETAIL: '/strategy/detail',
    CREATE: '/strategy/create',
    UPDATE: '/strategy/update',
    DELETE: '/strategy/delete',
    START: '/strategy/start',
    STOP: '/strategy/stop',
    BACKTEST: '/strategy/backtest',
    PERFORMANCE: '/strategy/performance'
  },
  
  // 回测相关
  BACKTEST: {
    RUN: '/backtest/run',
    RESULT: '/backtest/result',
    HISTORY: '/backtest/history',
    COMPARE: '/backtest/compare'
  },
  
  // 风险管理
  RISK: {
    METRICS: '/risk/metrics',
    ALERTS: '/risk/alerts',
    LIMITS: '/risk/limits',
    MONITOR: '/risk/monitor'
  }
} as const

// WebSocket相关常量
export const WS_CONFIG = {
  RECONNECT_INTERVAL: 5000,
  MAX_RECONNECT_ATTEMPTS: 10,
  HEARTBEAT_INTERVAL: 30000,
  PING_TIMEOUT: 5000
} as const

// 本地存储键名
export const STORAGE_KEYS = {
  AUTH_TOKEN: 'quant_auth_token',
  REFRESH_TOKEN: 'quant_refresh_token',
  USER_INFO: 'quant_user_info',
  THEME: 'quant_theme',
  LANGUAGE: 'quant_language',
  WATCHLIST: 'quant_watchlist',
  CHART_SETTINGS: 'quant_chart_settings',
  TRADING_SETTINGS: 'quant_trading_settings'
} as const

// 时间相关常量
export const TIME_CONFIG = {
  TOKEN_EXPIRES: 7200000, // 2小时
  REFRESH_TOKEN_EXPIRES: 2592000000, // 30天
  CACHE_EXPIRES: 300000, // 5分钟
  QUOTE_UPDATE_INTERVAL: 1000, // 1秒
  KLINE_UPDATE_INTERVAL: 60000 // 1分钟
} as const

// 交易相关常量
export const TRADING_CONFIG = {
  // 订单类型
  ORDER_TYPES: {
    LIMIT: 'limit',
    MARKET: 'market',
    STOP: 'stop',
    STOP_LIMIT: 'stop_limit',
    TRAILING_STOP: 'trailing_stop'
  },
  
  // 订单方向
  ORDER_SIDES: {
    BUY: 'buy',
    SELL: 'sell'
  },
  
  // 订单状态
  ORDER_STATUS: {
    PENDING: 'pending',
    PARTIAL_FILLED: 'partial_filled',
    FILLED: 'filled',
    CANCELLED: 'cancelled',
    REJECTED: 'rejected',
    EXPIRED: 'expired'
  },
  
  // 持仓方向
  POSITION_SIDES: {
    LONG: 'long',
    SHORT: 'short'
  },
  
  // 最小交易单位
  MIN_ORDER_SIZE: 100,
  
  // 价格精度
  PRICE_PRECISION: 2,
  
  // 数量精度
  QUANTITY_PRECISION: 0
} as const

// 市场相关常量
export const MARKET_CONFIG = {
  // 市场类型
  MARKET_TYPES: {
    STOCK: 'stock',
    FUND: 'fund',
    BOND: 'bond',
    FUTURES: 'futures',
    OPTIONS: 'options'
  },
  
  // 交易所
  EXCHANGES: {
    SSE: 'SSE',  // 上海证券交易所
    SZSE: 'SZSE', // 深圳证券交易所
    BSE: 'BSE',   // 北京证券交易所
    NYSE: 'NYSE', // 纽约证券交易所
    NASDAQ: 'NASDAQ' // 纳斯达克
  },
  
  // K线周期
  KLINE_PERIODS: {
    '1m': '1分钟',
    '5m': '5分钟',
    '15m': '15分钟',
    '30m': '30分钟',
    '1h': '1小时',
    '4h': '4小时',
    '1d': '日线',
    '1w': '周线',
    '1M': '月线'
  },
  
  // 涨跌停限制
  PRICE_LIMIT: {
    STOCK: 0.1,     // 股票10%
    ST_STOCK: 0.05, // ST股票5%
    NEW_STOCK: 0.44 // 新股44%
  }
} as const

// 图表相关常量
export const CHART_CONFIG = {
  // 默认颜色
  COLORS: {
    UP: '#ff4d4f',      // 上涨红色
    DOWN: '#52c41a',    // 下跌绿色
    NEUTRAL: '#8c8c8c', // 平盘灰色
    VOLUME_UP: 'rgba(255, 77, 79, 0.6)',
    VOLUME_DOWN: 'rgba(82, 196, 26, 0.6)'
  },
  
  // 技术指标
  INDICATORS: {
    MA: 'MA',
    EMA: 'EMA',
    BOLL: 'BOLL',
    MACD: 'MACD',
    RSI: 'RSI',
    KDJ: 'KDJ',
    CCI: 'CCI',
    WR: 'WR',
    BIAS: 'BIAS',
    DMI: 'DMI',
    CR: 'CR',
    PSY: 'PSY',
    VR: 'VR',
    WAD: 'WAD',
    OBV: 'OBV',
    SAR: 'SAR'
  },
  
  // 默认指标参数
  INDICATOR_PARAMS: {
    MA: [5, 10, 20, 30, 60],
    EMA: [12, 26],
    BOLL: { period: 20, multiplier: 2 },
    MACD: { fast: 12, slow: 26, signal: 9 },
    RSI: { period: 14 },
    KDJ: { k: 9, d: 3, j: 3 },
    CCI: { period: 14 },
    WR: { period: 14 }
  }
} as const

// 风险管理常量
export const RISK_CONFIG = {
  // 风险等级
  RISK_LEVELS: {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    EXTREME: 'extreme'
  },
  
  // 风险指标阈值
  RISK_THRESHOLDS: {
    MAX_POSITION_RATIO: 0.8,    // 最大持仓比例
    MAX_SINGLE_STOCK_RATIO: 0.3, // 单股最大比例
    MAX_SECTOR_RATIO: 0.5,      // 单行业最大比例
    MAX_DRAWDOWN: 0.2,          // 最大回撤
    MIN_CASH_RATIO: 0.1         // 最小现金比例
  }
} as const

// 策略相关常量
export const STRATEGY_CONFIG = {
  // 策略类型
  STRATEGY_TYPES: {
    TREND_FOLLOWING: 'trend_following',
    MEAN_REVERSION: 'mean_reversion',
    ARBITRAGE: 'arbitrage',
    MARKET_MAKING: 'market_making',
    STATISTICAL: 'statistical',
    FUNDAMENTAL: 'fundamental'
  },
  
  // 策略状态
  STRATEGY_STATUS: {
    DRAFT: 'draft',
    TESTING: 'testing',
    RUNNING: 'running',
    PAUSED: 'paused',
    STOPPED: 'stopped',
    ERROR: 'error'
  },
  
  // 回测状态
  BACKTEST_STATUS: {
    PENDING: 'pending',
    RUNNING: 'running',
    COMPLETED: 'completed',
    FAILED: 'failed',
    CANCELLED: 'cancelled'
  }
} as const

// 通知相关常量
export const NOTIFICATION_CONFIG = {
  // 通知类型
  TYPES: {
    ORDER: 'order',
    TRADE: 'trade',
    PRICE_ALERT: 'price_alert',
    STRATEGY: 'strategy',
    RISK: 'risk',
    SYSTEM: 'system'
  },
  
  // 通知级别
  LEVELS: {
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'error',
    SUCCESS: 'success'
  },
  
  // 默认显示时间
  DURATION: {
    INFO: 3000,
    WARNING: 5000,
    ERROR: 0,
    SUCCESS: 3000
  }
} as const

// 分页相关常量
export const PAGINATION_CONFIG = {
  DEFAULT_PAGE_SIZE: 20,
  PAGE_SIZES: [10, 20, 50, 100],
  MAX_PAGE_SIZE: 1000
} as const

// 文件相关常量
export const FILE_CONFIG = {
  // 支持的图片格式
  IMAGE_TYPES: ['jpg', 'jpeg', 'png', 'gif', 'webp'],
  
  // 支持的文档格式
  DOCUMENT_TYPES: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv'],
  
  // 文件大小限制 (字节)
  MAX_FILE_SIZE: {
    IMAGE: 5 * 1024 * 1024,    // 5MB
    DOCUMENT: 10 * 1024 * 1024  // 10MB
  }
} as const

// 正则表达式
export const REGEX_PATTERNS = {
  // 股票代码 (6位数字)
  STOCK_CODE: /^[0-9]{6}$/,
  
  // 手机号
  MOBILE: /^1[3-9]\d{9}$/,
  
  // 邮箱
  EMAIL: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
  
  // 密码 (8-20位，包含字母和数字)
  PASSWORD: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,20}$/,
  
  // 金额 (最多2位小数)
  AMOUNT: /^\d+(\.\d{1,2})?$/,
  
  // 正整数
  POSITIVE_INTEGER: /^[1-9]\d*$/,
  
  // 非负整数
  NON_NEGATIVE_INTEGER: /^\d+$/
} as const

// 错误码
export const ERROR_CODES = {
  // 通用错误
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  
  // 认证错误
  UNAUTHORIZED: 'UNAUTHORIZED',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  INVALID_TOKEN: 'INVALID_TOKEN',
  
  // 业务错误
  INSUFFICIENT_BALANCE: 'INSUFFICIENT_BALANCE',
  INVALID_ORDER: 'INVALID_ORDER',
  MARKET_CLOSED: 'MARKET_CLOSED',
  PRICE_LIMIT: 'PRICE_LIMIT',
  
  // 数据错误
  DATA_NOT_FOUND: 'DATA_NOT_FOUND',
  DATA_FORMAT_ERROR: 'DATA_FORMAT_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR'
} as const

// 成功码
export const SUCCESS_CODES = {
  SUCCESS: 'SUCCESS',
  ORDER_SUBMITTED: 'ORDER_SUBMITTED',
  ORDER_FILLED: 'ORDER_FILLED',
  STRATEGY_STARTED: 'STRATEGY_STARTED',
  BACKTEST_COMPLETED: 'BACKTEST_COMPLETED'
} as const

// 环境变量
export const ENV_CONFIG = {
  isDevelopment: import.meta.env.MODE === 'development',
  isProduction: import.meta.env.MODE === 'production',
  isTesting: import.meta.env.MODE === 'test',
  
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  
  enableMock: import.meta.env.VITE_ENABLE_MOCK === 'true',
  enableDevtools: import.meta.env.VITE_ENABLE_DEVTOOLS === 'true'
} as const

// 指数代码到名称的映射
export const INDEX_MAP: Record<string, string> = {
  '000001.SH': '上证指数',
  'SH000001': '上证指数',
  '399001.SZ': '深证成指', 
  'SZ399001': '深证成指',
  '399006.SZ': '创业板指',
  'SZ399006': '创业板指',
  '000688.SH': '科创50',
  'SH000688': '科创50'
} as const