/**
 * 图表相关类型定义
 */

import type { EChartsOption } from 'echarts'

// 时间框架类型（与TimePeriod保持一致）
export type TimeFrame = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M'

// 时间周期选项
export interface TimeFrameOption {
  value: TimeFrame
  label: string
  seconds: number
}

// 基础数据类型
export interface BaseChartData {
  timestamp: string | number
  value: number
}

// K线数据类型
export interface KLineData {
  timestamp: string | number
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount?: number
}

// 蜡烛图数据类型（K线数据的别名）
export type CandlestickData = KLineData

// 深度图数据类型
export interface DepthData {
  price: number
  amount: number
  total: number
}

export interface OrderBookData {
  bids: DepthData[]
  asks: DepthData[]
  timestamp: number
}

// 技术指标类型
export type IndicatorType = 'MA' | 'EMA' | 'MACD' | 'RSI' | 'KDJ' | 'BOLL' | 'VOL'

export interface IndicatorConfig {
  type: IndicatorType
  params: Record<string, number>
  visible: boolean
  color?: string
}

export interface TechnicalIndicator {
  type: IndicatorType
  name: string
  data: number[]
  config: Record<string, any>
}

// 时间周期类型
export type TimePeriod = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M'

export interface TimePeriodOption {
  value: TimePeriod
  label: string
  seconds: number
}

// 图表配置类型
export interface ChartConfig {
  theme?: 'light' | 'dark'
  grid?: {
    left?: string | number
    right?: string | number
    top?: string | number
    bottom?: string | number
  }
  animation?: boolean
  responsive?: boolean
}

// 图表事件类型
export interface ChartEventData {
  type: string
  event: MouseEvent
  data?: any
}

export type ChartEventHandler = (data: ChartEventData) => void

// 图表组件Props类型
export interface BaseChartProps {
  data: any[]
  height?: number | string
  width?: number | string
  loading?: boolean
  theme?: 'light' | 'dark'
  config?: ChartConfig
  onEvent?: ChartEventHandler
}

// 位置数据类型（用于饼图等）
export interface PositionChartData {
  name: string
  value: number
  percent: number
  color?: string
}

// 位置数据类型（简化版）
export interface PositionData {
  name: string
  value: number
  percent: number
  symbol?: string
}

// 趋势数据类型（用于折线图等）
export interface TrendChartData {
  date: string
  value: number
  label?: string
}

// 趋势数据类型（简化版）
export interface TrendData {
  date: string
  value: number
}

// 风险分布数据类型
export interface RiskDistributionData {
  category: string
  value: number
  level: 'low' | 'medium' | 'high' | 'critical'
}

// 风险趋势数据类型
export interface RiskTrendData {
  date: string
  value: number
  type: 'var' | 'drawdown' | 'volatility'
}

// 图表主题配置
export interface ChartTheme {
  backgroundColor: string
  textColor: string
  lineColor: string
  gridColor: string
  upColor: string
  downColor: string
  neutralColor: string
}

// 导出ECharts相关类型
export type { EChartsOption }
