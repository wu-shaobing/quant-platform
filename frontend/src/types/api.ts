// API相关类型定义

import { BaseResponse, ListResponse } from './common'

// HTTP方法类型
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'

// 请求配置
export interface RequestConfig {
  url: string
  method?: HttpMethod
  params?: Record<string, any>
  data?: any
  headers?: Record<string, string>
  timeout?: number
  withCredentials?: boolean
}

// API响应基础类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  code?: number
  timestamp?: string
}

// 分页响应类型
export interface PaginatedResponse<T = any> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 列表响应类型
export interface ListResponse<T = any> extends ApiResponse<PaginatedResponse<T>> {}

// 错误响应类型
export interface ApiError {
  code: number
  message: string
  details?: Record<string, any>
  field?: string
}

// WebSocket消息类型
export interface WebSocketMessage<T = any> {
  type: string
  data: T
  timestamp?: string
  id?: string
}

// 订阅请求类型
export interface SubscriptionRequest {
  symbols: string[]
  dataTypes: ('tick' | 'depth' | 'trade')[]
  interval?: string
}

// 市场数据相关类型
export interface TickData {
  symbol: string
  lastPrice: number
  volume: number
  turnover: number
  openInterest?: number
  timestamp: string
  bidPrice1: number
  bidVolume1: number
  askPrice1: number
  askVolume1: number
  change: number
  changePercent: number
}

export interface BarData {
  symbol: string
  datetime: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  turnover: number
  openInterest?: number
  interval: string
}

export interface DepthData {
  symbol: string
  timestamp: string
  bids: [number, number][] // [price, volume]
  asks: [number, number][] // [price, volume]
}

// 交易相关类型
export interface OrderData {
  orderId: string
  symbol: string
  direction: 'BUY' | 'SELL'
  offset: 'OPEN' | 'CLOSE' | 'CLOSETODAY' | 'CLOSEYESTERDAY'
  orderType: 'LIMIT' | 'MARKET' | 'STOP' | 'FAK' | 'FOK'
  volume: number
  price?: number
  tradedVolume: number
  status: 'SUBMITTING' | 'NOTTRADED' | 'PARTTRADED' | 'ALLTRADED' | 'CANCELLED' | 'REJECTED'
  createTime: string
  updateTime: string
}

export interface TradeData {
  tradeId: string
  orderId: string
  symbol: string
  direction: 'BUY' | 'SELL'
  offset: 'OPEN' | 'CLOSE' | 'CLOSETODAY' | 'CLOSEYESTERDAY'
  volume: number
  price: number
  turnover: number
  commission: number
  timestamp: string
}

export interface PositionData {
  symbol: string
  direction: 'LONG' | 'SHORT'
  volume: number
  price: number
  pnl: number
  pnlPercent: number
  margin: number
  marketValue: number
  lastPrice: number
  updateTime: string
}

export interface AccountData {
  accountId: string
  totalAssets: number
  availableCash: number
  frozenCash: number
  totalMargin: number
  totalPnl: number
  dailyPnl: number
  dailyPnlPercent: number
  totalPnlPercent: number
  riskLevel: number
  updateTime: string
}

// 策略相关类型
export interface StrategyData {
  id: string
  name: string
  description: string
  author: string
  category: string
  tags: string[]
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH'
  annualReturn: number
  maxDrawdown: number
  sharpeRatio: number
  rating: number
  viewCount: number
  favoriteCount: number
  downloadCount: number
  isFavorited: boolean
  status: 'DRAFT' | 'PUBLISHED' | 'RUNNING' | 'STOPPED'
  createTime: string
  updateTime: string
}

// 回测相关类型
export interface BacktestData {
  id: string
  name: string
  strategy: string
  strategyId: string
  symbol: string
  startDate: string
  endDate: string
  initialCash: number
  totalReturn: number
  totalReturnPercent: number
  annualReturn: number
  maxDrawdown: number
  maxDrawdownPercent: number
  sharpeRatio: number
  sortinoRatio: number
  calmarRatio: number
  winRate: number
  profitFactor: number
  totalTrades: number
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  progress: number
  isFavorite: boolean
  createTime: string
  updateTime: string
}

// 用户相关类型
export interface UserData {
  id: number
  username: string
  email: string
  fullName?: string
  phone?: string
  avatar?: string
  role: 'USER' | 'ADMIN' | 'VIP'
  isActive: boolean
  lastLoginTime?: string
  createTime: string
}

export interface LoginRequest {
  username: string
  password: string
  rememberMe?: boolean
  verificationToken?: string
}

export interface TokenResponse {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  userId: number
  username: string
}

// 通用查询参数
export interface QueryParams {
  page?: number
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  search?: string
  filters?: Record<string, any>
}

// 时间范围查询
export interface TimeRangeQuery {
  startTime?: string
  endTime?: string
  interval?: string
}

// 导出类型工具
export type ApiResponseData<T> = T extends ApiResponse<infer U> ? U : never
export type ListResponseData<T> = T extends ListResponse<infer U> ? U : never

// 响应类型
export interface ApiSuccessResponse<T = any> extends BaseResponse<T> {
  code: 200
  success: true
}

export interface ApiErrorResponse extends BaseResponse<null> {
  code: number
  success: false
  error: {
    type: string
    message: string
    details?: any
  }
}

export type ApiResponse<T = any> = ApiSuccessResponse<T> | ApiErrorResponse

// 分页请求参数
export interface PaginationRequest {
  page?: number
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

// 列表响应
export interface ListApiResponse<T> extends ApiSuccessResponse<ListResponse<T>> {}

// 认证相关
export interface LoginResponse {
  token: string
  refreshToken: string
  expiresIn: number
  user: {
    id: string
    username: string
    email: string
    avatar?: string
    roles: string[]
    permissions: string[]
  }
}

export interface RefreshTokenRequest {
  refreshToken: string
}

export interface RefreshTokenResponse {
  token: string
  expiresIn: number
}

// 文件上传
export interface UploadRequest {
  file: File
  filename?: string
  category?: string
}

export interface UploadResponse {
  url: string
  filename: string
  size: number
  mimeType: string
  hash: string
}

// WebSocket消息类型
export interface WSSubscribeMessage {
  action: 'subscribe' | 'unsubscribe'
  channel: string
  params?: Record<string, any>
}

export interface WSHeartbeatMessage {
  type: 'ping' | 'pong'
  timestamp: number
}

export interface ValidationError {
  field: string
  message: string
  value?: any
}

// 搜索请求
export interface SearchRequest extends PaginationRequest {
  keyword?: string
  filters?: Record<string, any>
  dateRange?: {
    start: string
    end: string
  }
}

// 批量操作
export interface BatchRequest<T = any> {
  action: string
  items: T[]
  options?: Record<string, any>
}

export interface BatchResponse<T = any> {
  success: T[]
  failed: Array<{
    item: T
    error: ApiError
  }>
  total: number
  successCount: number
  failedCount: number
} 