// API 模块统一导出
export { default as userApi } from './user'
export { default as marketApi } from './market'
export { default as tradingApi } from './trading'
export { default as strategyApi } from './strategy'
export { default as backtestApi } from './backtest'

// HTTP 客户端
export { http, default as httpClient } from './http'

// 只导出不冲突的类型
export type { ApiResponse } from './http'

// 分别导出不同模块的类型，避免冲突
export type * as UserTypes from '@/types/user'
export type * as MarketTypes from '@/types/market'
export type * as TradingTypes from '@/types/trading'
export type * as StrategyTypes from '@/types/strategy'
export type * as BacktestTypes from '@/types/backtest'
export type * as CommonTypes from '@/types/common' 