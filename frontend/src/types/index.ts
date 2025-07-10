/**
 * 统一类型定义导出
 */

// 基础类型导出
export * from './api'
export * from './chart'
export * from './common'
export * from './user'
export * from './portfolio'

// 市场相关类型
export type {
  StockInfo as MarketStockInfo,
  QuoteData,
  MarketDepth,
  KLineData,
  MarketStats,
  IndexData,
  SectorData,
  HotStock as MarketHotStock,
  NewsItem as MarketNews
} from './market'

// 交易相关类型 - 明确导出避免冲突
export type {
  OrderSide,
  OrderType,
  OrderStatus,
  PositionSide,
  AccountType,
  Order,
  OrderFormData,
  Position,
  Trade,
  TradeRecord,
  Account,
  CashFlow,
  RiskWarning,
  TradingStats,
  Quote,
  Tick,
  TradingRules,
  QuickTradeConfig,
  OrderSubmitData,
  OrderCancelData,
  OrderModifyData,
  StockInfo as TradingStockInfo
} from './trading'

// 策略相关类型 - 明确导出避免冲突
export type {
  Strategy,
  StrategyType,
  StrategyStatus,
  RiskLevel,
  StrategyParameter,
  StrategyLog,
  StrategyPerformance,
  StrategyConfig,
  StrategyBacktest,
  StrategyOptimization
} from './strategy'

// 回测相关类型 - 明确导出避免冲突
export type {
  Backtest,
  BacktestStatus,
  BacktestConfig,
  BacktestResult,
  BacktestMetrics,
  BacktestTrade,
  BacktestPosition,
  BacktestFormData,
  BacktestCreateData,
  DrawdownPoint,
  OptimizationResult
} from './backtest'

// 风险相关类型
export * from './risk'

// 为了避免冲突，重新导出StockInfo为TradingStockInfo
export type { TradingStockInfo } from './trading'
export type { StockInfo } from './market'

// 组件类型
export type { ComponentSize, ComponentType } from './common'

// API响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp?: number
  requestId?: string
}

// 分页请求类型
export interface PaginationRequest {
  page: number
  pageSize: number
  keyword?: string
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

// 分页响应类型
export interface PaginationResponse<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 全局类型定义
export interface PaginationParams {
  page?: number
  pageSize?: number
  total?: number
}

export interface BaseEntity {
  id: string
  createTime: number
  updateTime: number
}

export interface Dictionary<T = any> {
  [key: string]: T
}

export type Nullable<T> = T | null
export type Optional<T> = T | undefined
export type Maybe<T> = T | null | undefined

// 新闻相关类型
export interface NewsItem {
  id: string
  title: string
  content?: string
  summary?: string
  source: string
  author?: string
  publishTime: number
  url?: string
  thumbnail?: string
  tags?: string[]
  readCount?: number
  isImportant?: boolean
}

// 热门股票类型
export interface HotStock {
  symbol: string
  name: string
  currentPrice: number
  change: number
  changePercent: number
  volume?: number
  turnover?: number
  marketCap?: number
  category?: 'gainers' | 'losers' | 'volume' | 'active'
}

// 通用类型定义
export interface PaginationData<T = any> {
  list: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 错误类型
export interface ApiError {
  code?: number
  message?: string
  timestamp?: number
  details?: Record<string, any>
}

// HTTP请求相关
export interface RequestConfig {
  baseURL?: string
  timeout?: number
  headers?: Record<string, string>
  withCredentials?: boolean
}

// 通用状态
export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

// 排序
export interface SortConfig {
  field: string
  order: 'asc' | 'desc'
}

// 筛选
export interface FilterConfig {
  field: string
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'like'
  value: any
}

// 时间范围
export interface TimeRange {
  startTime: string
  endTime: string
}

// 颜色主题
export interface ColorTheme {
  primary: string
  secondary: string
  success: string
  warning: string
  error: string
  info: string
}

// 图表配置
export interface ChartConfig {
  type: 'line' | 'bar' | 'candlestick' | 'scatter'
  theme: 'light' | 'dark'
  colors: ColorTheme
  animation: boolean
  responsive: boolean
}

// 通知
export interface Notification {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  title: string
  message: string
  duration?: number
  actions?: Array<{
    text: string
    action: () => void
  }>
  timestamp: string
}

// 文件上传
export interface FileUpload {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  url?: string
  error?: string
}

// 键值对
export interface KeyValue<T = any> {
  key: string
  value: T
  label?: string
}

// 选项
export interface Option<T = any> {
  label: string
  value: T
  disabled?: boolean
  children?: Option<T>[]
}

// 菜单项
export interface MenuItem {
  id: string
  title: string
  icon?: string
  path?: string
  children?: MenuItem[]
  meta?: {
    requireAuth?: boolean
    roles?: string[]
    permissions?: string[]
  }
}

// 面包屑
export interface Breadcrumb {
  title: string
  path?: string
  icon?: string
}

// 表格列
export interface TableColumn<T = any> {
  key: string
  title: string
  dataIndex?: string
  width?: number | string
  align?: 'left' | 'center' | 'right'
  fixed?: 'left' | 'right'
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, record: T, index: number) => any
}

// 表单字段
export interface FormField {
  name: string
  label: string
  type: 'input' | 'select' | 'textarea' | 'number' | 'date' | 'switch' | 'radio' | 'checkbox'
  required?: boolean
  placeholder?: string
  options?: Option[]
  rules?: any[]
  props?: Record<string, any>
}

// 布局配置
export interface LayoutConfig {
  sidebar: {
    collapsed: boolean
    width: number
  }
  header: {
    height: number
    fixed: boolean
  }
  footer: {
    height: number
    show: boolean
  }
}

// WebSocket消息
export interface WebSocketMessage<T = any> {
  type: string
  data: T
  timestamp: number
  id?: string
}

// 环境配置
export interface EnvConfig {
  NODE_ENV: 'development' | 'production' | 'test'
  VITE_API_BASE_URL: string
  VITE_WS_URL: string
  VITE_APP_TITLE: string
  VITE_ENABLE_MOCK: string
}
