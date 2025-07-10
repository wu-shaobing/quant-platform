/**
 * 交易相关类型定义
 */

// 订单方向
export type OrderSide = 'buy' | 'sell'

// 订单类型
export type OrderType = 'market' | 'limit' | 'stop' | 'stop-limit' | 'trailing-stop'

// 订单状态
export type OrderStatus = 
  | 'pending'      // 待提交
  | 'submitted'    // 已提交
  | 'accepted'     // 已接受
  | 'partially-filled' // 部分成交
  | 'filled'       // 已成交
  | 'cancelled'    // 已取消
  | 'rejected'     // 已拒绝
  | 'expired'      // 已过期

// 持仓方向
export type PositionSide = 'long' | 'short'

// 账户类型
export type AccountType = 'cash' | 'margin' | 'futures'

// 股票信息
export interface StockInfo {
  symbol: string
  name: string
  market: string
  sector?: string
  industry?: string
  currentPrice: number
  change: number
  changePercent: number
  volume: number
  turnover: number
  marketCap?: number
  pe?: number
  pb?: number
  high52w?: number
  low52w?: number
  isTrading: boolean
}

// 订单信息
export interface Order {
  id: string           // 订单ID（别名）
  orderId: string
  clientOrderId?: string
  symbol: string
  side: OrderSide
  type: OrderType
  quantity: number
  price?: number
  stopPrice?: number
  trailingAmount?: number
  trailingPercent?: number
  filledQuantity: number
  avgFillPrice: number
  status: OrderStatus
  timeInForce: 'DAY' | 'GTC' | 'IOC' | 'FOK'
  createTime: number
  updateTime: number
  commission: number
  commissionAsset: string
  remark?: string
}

// 订单表单数据
export interface OrderFormData {
  symbol: string
  side: OrderSide
  type: OrderType
  quantity: number
  price?: number
  stopPrice?: number
  timeInForce?: 'DAY' | 'GTC' | 'IOC' | 'FOK'
  remark?: string
}

// 持仓信息
export interface Position {
  symbol: string
  side: PositionSide
  totalQuantity: number
  availableQuantity: number
  lockedQuantity: number
  avgPrice: number
  marketPrice: number
  markPrice: number  // 标记价格
  size: number       // 持仓大小（等同于totalQuantity）
  marketValue: number
  unrealizedPnl: number
  unrealizedPnlPercent: number
  todayPnl: number
  todayPnlPercent: number
  totalPnl: number
  totalPnlPercent: number
  createTime: number
  updateTime: number
}

// 成交记录
export interface Trade {
  id: string           // 成交ID（别名）
  tradeId: string
  orderId: string
  symbol: string
  side: OrderSide
  quantity: number
  price: number
  amount: number
  commission: number
  commissionAsset: string
  time: number
  timestamp: number    // 时间戳（别名）
  isMaker: boolean
}

// 成交记录别名（向后兼容）
export type TradeRecord = Trade

// 账户信息
export interface Account {
  accountId: string
  accountType: AccountType
  totalEquity: number      // 总资产
  totalAssets: number      // 总资产（别名）
  totalCash: number        // 总现金
  availableCash: number    // 可用现金
  lockedCash: number       // 冻结现金
  totalPositionValue: number // 总持仓市值
  totalPnl: number         // 总盈亏
  totalPnlPercent: number  // 总盈亏百分比
  todayPnl: number         // 今日盈亏
  todayPnlPercent: number  // 今日盈亏百分比
  dailyProfit: number      // 今日盈亏（别名）
  dailyProfitPercent: number // 今日盈亏百分比（别名）
  margin?: number          // 保证金
  marginLevel?: number     // 保证金水平
  buyingPower?: number     // 购买力
  updateTime: number
}

// 资金流水
export interface CashFlow {
  id: string
  type: 'deposit' | 'withdraw' | 'trade' | 'dividend' | 'interest' | 'fee'
  amount: number
  balance: number
  description: string
  time: number
  relatedOrderId?: string
  relatedTradeId?: string
}

// 风险警告
export interface RiskWarning {
  type: 'capital' | 'concentration' | 'price' | 'volatility' | 'liquidity'
  level: 'info' | 'warning' | 'error'
  message: string
  details?: string
}

// 交易统计
export interface TradingStats {
  totalTrades: number
  winTrades: number
  lossTrades: number
  winRate: number
  avgWin: number
  avgLoss: number
  profitFactor: number
  maxWin: number
  maxLoss: number
  totalCommission: number
  totalPnl: number
  sharpeRatio?: number
  maxDrawdown?: number
  volatility?: number
}

// 行情数据
export interface Quote {
  symbol: string
  price: number
  change: number
  changePercent: number
  open: number
  high: number
  low: number
  volume: number
  turnover: number
  bid: number
  bidSize: number
  ask: number
  askSize: number
  timestamp: number
}

// 逐笔成交
export interface Tick {
  symbol: string
  price: number
  quantity: number
  amount: number
  side: 'buy' | 'sell' | 'neutral'
  timestamp: number
}

// 交易规则
export interface TradingRules {
  symbol: string
  minQuantity: number
  maxQuantity: number
  stepQuantity: number
  minPrice: number
  maxPrice: number
  stepPrice: number
  minAmount: number
  maxAmount: number
  commissionRate: number
  minCommission: number
  isTrading: boolean
  tradingHours: Array<{
    start: string
    end: string
  }>
}

// 快速交易配置
export interface QuickTradeConfig {
  enabled: boolean
  presetAmounts: number[]
  defaultSide: OrderSide
  defaultType: OrderType
  confirmRequired: boolean
}

// 订单提交数据
export interface OrderSubmitData {
  symbol: string
  side: OrderSide
  type: OrderType
  quantity: number
  price?: number
  stopPrice?: number
  timeInForce?: 'DAY' | 'GTC' | 'IOC' | 'FOK'
  clientOrderId?: string
  remark?: string
}

// 订单取消数据
export interface OrderCancelData {
  orderId: string
  symbol: string
  reason?: string
}

// 订单修改数据
export interface OrderModifyData {
  orderId: string
  quantity?: number
  price?: number
  stopPrice?: number
  timeInForce?: 'DAY' | 'GTC' | 'IOC' | 'FOK'
}



// 导出所有交易相关类型
export type {
  OrderSide,
  OrderType,
  OrderStatus,
  PositionSide,
  AccountType
}