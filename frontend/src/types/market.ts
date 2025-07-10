// 市场数据相关类型定义

// 行情数据
export interface QuoteData {
  symbol: string
  name: string
  currentPrice: number
  previousClose: number
  change: number
  changePercent: number
  high: number
  low: number
  volume: number
  turnover: number
  openPrice: number
  timestamp: number
  status: 'trading' | 'suspended' | 'closed'
}

// K线数据
export interface KLineData {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  turnover: number
  symbol?: string
}

// 市场深度数据项
export interface OrderBookItem {
  price: number
  quantity: number
  amount: number
}

// 市场深度数据
export interface OrderBookData {
  symbol: string
  timestamp: number
  bids: OrderBookItem[]  // 买盘
  asks: OrderBookItem[]  // 卖盘
}

// 成交明细
export interface TradeData {
  timestamp: number
  price: number
  quantity: number
  amount: number
  direction: 'buy' | 'sell' | 'neutral'
}

// 股票基本信息
export interface StockInfo {
  symbol: string
  name: string
  exchange: string
  market: string
  sector: string
  industry: string
  listDate: string
  totalShares: number
  floatShares: number
  marketCap: number
  pe: number
  pb: number
  eps: number
  roe: number
  status: string
}

// 市场搜索结果
export interface MarketSearchResult {
  symbol: string
  name: string
  exchange: string
  type: string
  currentPrice?: number
  change?: number
  changePercent?: number
}

// 市场概览
export interface MarketOverview {
  indices: Array<{
    name: string
    value: number
    change: number
    changePercent: number
  }>
  stats: {
    totalStocks: number
    advancers: number
    decliners: number
    unchanged: number
    totalVolume: number
    totalTurnover: number
  }
  timestamp: number
}

// 板块数据
export interface SectorData {
  name: string
  code: string
  change: number
  changePercent: number
  volume: number
  turnover: number
  stocks: number
  leadingStock: {
    symbol: string
    name: string
    changePercent: number
  }
}

// 排行榜数据
export interface RankingData {
  symbol: string
  name: string
  currentPrice: number
  change: number
  changePercent: number
  volume: number
  turnover: number
  rank: number
}

// 市场新闻
export interface MarketNews {
  id: string
  title: string
  summary: string
  content: string
  source: string
  publishTime: number
  tags: string[]
  relatedSymbols: string[]
  importance: 'low' | 'medium' | 'high'
  url?: string
}

// 财经日历事件
export interface CalendarEvent {
  id: string
  title: string
  description: string
  date: number
  time?: string
  country: string
  category: string
  importance: 'low' | 'medium' | 'high'
  previous?: number
  forecast?: number
  actual?: number
  unit?: string
}

// 技术指标
export interface TechnicalIndicator {
  name: string
  value: number | number[]
  signal: 'buy' | 'sell' | 'hold'
  timestamp: number
}

// 市场情绪指标
export interface MarketSentiment {
  fearGreedIndex: number
  vixIndex: number
  putCallRatio: number
  marginDebt: number
  timestamp: number
}

// 资金流向
export interface MoneyFlow {
  symbol: string
  mainInflow: number
  mainOutflow: number
  retailInflow: number
  retailOutflow: number
  netInflow: number
  timestamp: number
}

// 龙虎榜数据
export interface DragonTigerData {
  symbol: string
  name: string
  reason: string
  buyAmount: number
  sellAmount: number
  netAmount: number
  seats: Array<{
    name: string
    type: 'institution' | 'individual'
    buyAmount: number
    sellAmount: number
    netAmount: number
  }>
  date: string
}

// 分时数据
export interface MinuteData {
  timestamp: number
  price: number
  volume: number
  avgPrice: number
}

// 市场状态
export type MarketStatus = 'pre_market' | 'trading' | 'lunch_break' | 'after_market' | 'closed' | 'holiday'

// 交易所信息
export interface ExchangeInfo {
  code: string
  name: string
  timezone: string
  tradingHours: {
    morning: { start: string; end: string }
    afternoon: { start: string; end: string }
  }
  holidays: string[]
}

// K线周期
export type KLinePeriod = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M'

// 排行榜类型
export type RankingType = 'gainers' | 'losers' | 'volume' | 'turnover' | 'amplitude' | 'turnover_rate'

// 市场数据订阅配置
export interface MarketSubscription {
  symbols: string[]
  dataTypes: ('quote' | 'kline' | 'depth' | 'trade')[]
  frequency?: number
}

// 历史数据查询参数
export interface HistoryDataQuery {
  symbol: string
  period: KLinePeriod
  startDate?: string
  endDate?: string
  limit?: number
  adjust?: 'none' | 'qfq' | 'hfq'  // 复权类型
}

// 市场筛选条件
export interface MarketFilter {
  exchange?: string[]
  sector?: string[]
  industry?: string[]
  marketCap?: { min?: number; max?: number }
  pe?: { min?: number; max?: number }
  pb?: { min?: number; max?: number }
  changePercent?: { min?: number; max?: number }
  volume?: { min?: number; max?: number }
}

// 自选股分组
export interface WatchlistGroup {
  id: string
  name: string
  symbols: string[]
  createTime: number
  updateTime: number
}

// 预警条件
export interface AlertCondition {
  id: string
  symbol: string
  name: string
  type: 'price' | 'change' | 'volume' | 'technical'
  operator: '>' | '<' | '>=' | '<=' | '='
  value: number
  enabled: boolean
  triggered: boolean
  createTime: number
  triggerTime?: number
}

// 蜡烛图数据（别名）
export interface CandlestickData extends KLineData {}

// 深度数据（别名）
export interface DepthData extends OrderBookItem {
  type: 'bid' | 'ask'
}

// 添加缺失的类型定义
export interface KLineParams {
  symbol: string
  period: KLinePeriod
  startTime?: number
  endTime?: number
  startDate?: string
  endDate?: string
  limit?: number
  adjust?: 'none' | 'qfq' | 'hfq'
}

export interface QuoteParams {
  symbols: string[]
  fields?: string[]
}

export interface SearchParams {
  keyword: string
  market?: string
  exchange?: string
  type?: string
  limit?: number
}

export interface SearchResult {
  symbol: string
  name: string
  exchange: string
  type: string
  currentPrice?: number
  change?: number
  changePercent?: number
}

export interface NewsData {
  id: string
  title: string
  summary: string
  content: string
  source: string
  publishTime: number
  tags: string[]
  relatedSymbols: string[]
  importance: 'low' | 'medium' | 'high'
  url?: string
}

export interface StockScreenerParams {
  exchange?: string[]
  sector?: string[]
  industry?: string[]
  marketCap?: { min?: number; max?: number }
  pe?: { min?: number; max?: number }
  pb?: { min?: number; max?: number }
  changePercent?: { min?: number; max?: number }
  volume?: { min?: number; max?: number }
  limit?: number
  offset?: number
}

// 自选股条目
export interface WatchlistItem {
  symbol: string
  name: string
  addTime: number
  sort: number
}

// 指数数据接口
export interface IndexData {
  symbol: string
  name: string
  currentPrice: number
  change: number
  changePercent: number
  volume?: number
  turnover?: number
} 