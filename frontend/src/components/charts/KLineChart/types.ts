export interface KLineData {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface TimePeriod {
  value: string
  label: string
}

export interface IndicatorType {
  value: string
  label: string
  params?: Record<string, any>
}

export interface ChartConfig {
  theme: 'light' | 'dark'
  locale: 'zh-CN' | 'en-US'
  precision: number
  showVolume: boolean
  showIndicators: boolean
}

export interface TechnicalIndicator {
  name: string
  type: 'line' | 'bar' | 'area'
  data: number[]
  color?: string
  params?: Record<string, any>
}