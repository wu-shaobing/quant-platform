// 策略和回测相关类型定义

import type { CandlestickData } from './chart'
import type { Order, Position, Trade as TradingTrade } from './trading'

/**
 * 策略状态
 */
export type StrategyStatus = 'draft' | 'running' | 'paused' | 'stopped' | 'error'

/**
 * 策略类型
 */
export type StrategyType = 
  | 'trend_following'
  | 'mean_reversion' 
  | 'momentum'
  | 'arbitrage'
  | 'factor_model'
  | 'machine_learning'
  | 'custom'

/**
 * 风险等级
 */
export type RiskLevel = 'low' | 'medium' | 'high'

/**
 * 策略参数
 */
export interface StrategyParameter {
  name: string
  type: 'number' | 'string' | 'boolean'
  defaultValue: any
  description: string
  min?: number
  max?: number
  options?: string[]
}

/**
 * 策略基本信息
 */
export interface Strategy {
  id: string
  name: string
  description: string
  type: StrategyType
  status: StrategyStatus
  riskLevel: RiskLevel
  minCapital: number
  maxPositions: number
  code: string
  tags: string[]
  parameters: StrategyParameter[]
  createdAt: string
  updatedAt: string
  createdBy: string
  runningTime?: number
  version: string
}

/**
 * 策略性能指标
 */
export interface StrategyPerformance {
  currentNav: number
  totalReturn: number
  annualizedReturn: number
  maxDrawdown: number
  sharpeRatio: number
  sortinoRatio?: number
  todayPnl: number
  winRate: number
  volatility: number
  concentration: number
  profitFactor?: number
  totalTrades?: number
  avgTradeDuration?: number
  lastUpdate: Date
}

/**
 * 回测结果
 */
export interface BacktestResult {
  strategyId: string
  startDate: string
  endDate: string
  initialCapital: number
  finalCapital: number
  totalReturn: number
  annualizedReturn: number
  maxDrawdown: number
  sharpeRatio: number
  sortinoRatio: number
  winRate: number
  volatility: number
  profitFactor: number
  totalTrades: number
  avgTradeDuration: number
  trades: TradingTrade[]
  navCurve: NavPoint[]
  drawdownCurve: DrawdownPoint[]
  createdAt: string
}

/**
 * 交易记录
 */
export interface Trade {
  id: string
  strategyId: string
  symbol: string
  side: 'buy' | 'sell'
  quantity: number
  price: number
  amount: number
  fee: number
  pnl: number
  timestamp: string
  reason: string
}

/**
 * 净值点
 */
export interface NavPoint {
  date: string
  nav: number
  benchmark?: number
}

/**
 * 回撤点
 */
export interface DrawdownPoint {
  date: string
  drawdown: number
}

/**
 * 策略日志
 */
export interface StrategyLog {
  id: string
  strategyId: string
  level: 'info' | 'warning' | 'error' | 'debug'
  message: string
  timestamp: string
  data?: any
}

/**
 * 策略模板
 */
export interface StrategyTemplate {
  id: string
  name: string
  description: string
  type: StrategyType
  difficulty: 'easy' | 'medium' | 'hard'
  tags: string[]
  code: string
  parameters: StrategyParameter[]
  documentation?: string
  author: string
  version: string
  downloads: number
  rating: number
}

/**
 * 策略创建请求
 */
export interface CreateStrategyRequest {
  name: string
  description: string
  type: StrategyType
  riskLevel: RiskLevel
  minCapital: number
  maxPositions: number
  code: string
  tags: string[]
  parameters: StrategyParameter[]
}

/**
 * 策略更新请求
 */
export interface UpdateStrategyRequest extends Partial<CreateStrategyRequest> {
  id: string
}

/**
 * 策略查询参数
 */
export interface StrategyQueryParams {
  page?: number
  pageSize?: number
  status?: StrategyStatus
  type?: StrategyType
  riskLevel?: RiskLevel
  keyword?: string
  sortBy?: 'name' | 'createdAt' | 'updatedAt' | 'performance'
  sortOrder?: 'asc' | 'desc'
}

/**
 * 策略列表响应
 */
export interface StrategyListResponse {
  items: Strategy[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 策略实例 (运行中的策略)
export interface StrategyInstance {
  id: string
  strategyId: string
  name: string
  status: StrategyStatus
  startTime: string
  stopTime?: string
  capital: number
  currentValue: number
  pnl: number
  pnlPercent: number
  symbols: string[]
  live: boolean // 是否实盘
}

// 策略信号
export interface StrategySignal {
  id: string
  strategyInstanceId: string
  symbol: string
  signal: 'buy' | 'sell' | 'hold' | 'close_long' | 'close_short'
  strength?: number // 信号强度 (0-1)
  price?: number // 信号触发价格
  quantity?: number // 建议数量
  reason?: string // 信号原因
  timestamp: string
  meta?: Record<string, any> // 额外信息
}

// 回测配置
export interface BacktestConfig {
  strategyId: string
  name: string
  description?: string
  symbol: string
  timeFrame: string
  startDate: string
  endDate: string
  initialCapital: number
  commissionRate: number
  slippage: number // 滑点
  parameters?: Record<string, any>
}

// 绩效报告
export interface PerformanceReport {
  initialCapital: number
  finalCapital: number
  
  totalReturn: number
  annualizedReturn: number
  
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  
  averageTradeReturn: number
  averageWinningTrade: number
  averageLosingTrade: number
  profitLossRatio: number
  
  maxDrawdown: number
  sharpeRatio: number
  sortinoRatio: number
  calmarRatio: number
  
  avgHoldingPeriod: number // in hours or days
  expectancy: number
  
  beta?: number
  alpha?: number
}

// 策略优化配置
export interface OptimizationConfig {
  strategyId: string
  symbol: string
  timeFrame: string
  startDate: string
  endDate: string
  parameterRanges: Array<{
    key: string
    start: number
    end: number
    step: number
  }>
  objective: keyof PerformanceReport // 优化目标, e.g., 'totalReturn', 'sharpeRatio'
}

// 优化结果
export interface OptimizationResult {
  id: string
  config: OptimizationConfig
  status: 'running' | 'completed' | 'failed'
  bestParameters: Record<string, any>
  bestPerformance: PerformanceReport
  results: Array<{
    parameters: Record<string, any>
    performance: PerformanceReport
  }>
}

// 蒙特卡洛模拟
export interface MonteCarloResult {
  simulations: number
  confidenceLevel: number
  meanReturn: number
  medianReturn: number
  returnDistribution: number[]
}

// 敏感性分析
export interface SensitivityAnalysisResult {
  parameter: string
  values: number[]
  performanceMetric: string
  metricValues: number[]
}
