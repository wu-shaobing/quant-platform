import { Decimal } from 'decimal.js'

// 技术指标计算类型定义
export interface KLineData {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface MAResult {
  [period: string]: number[]
}

export interface MACDResult {
  dif: number[]
  dea: number[]
  macd: number[]
}

export interface RSIResult {
  rsi: number[]
}

export interface BollingerBandsResult {
  upper: number[]
  middle: number[]
  lower: number[]
}

export interface KDJResult {
  k: number[]
  d: number[]
  j: number[]
}

/**
 * 移动平均线计算
 * @param data 价格数据
 * @param periods 周期数组
 * @returns MA结果
 */
export const calculateMA = (data: number[], periods: number[]): MAResult => {
  const result: MAResult = {}
  
  periods.forEach(period => {
    const ma: number[] = []
    
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        ma.push(NaN)
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((acc, val) => acc + val, 0)
        ma.push(new Decimal(sum).div(period).toNumber())
      }
    }
    
    result[period.toString()] = ma
  })
  
  return result
}

/**
 * 指数移动平均线计算
 * @param data 价格数据
 * @param period 周期
 * @returns EMA结果
 */
export const calculateEMA = (data: number[], period: number): number[] => {
  const ema: number[] = []
  const multiplier = new Decimal(2).div(period + 1)
  
  // 第一个值使用SMA
  let sum = 0
  for (let i = 0; i < Math.min(period, data.length); i++) {
    sum += data[i]
    if (i < period - 1) {
      ema.push(NaN)
    } else {
      ema.push(sum / period)
    }
  }
  
  // 后续值使用EMA公式
  for (let i = period; i < data.length; i++) {
    const prevEMA = ema[i - 1]
    const currentEMA = new Decimal(data[i])
      .minus(prevEMA)
      .mul(multiplier)
      .plus(prevEMA)
      .toNumber()
    ema.push(currentEMA)
  }
  
  return ema
}

/**
 * MACD指标计算
 * @param data 收盘价数据
 * @param fastPeriod 快线周期，默认12
 * @param slowPeriod 慢线周期，默认26
 * @param signalPeriod 信号线周期，默认9
 * @returns MACD结果
 */
export const calculateMACD = (
  data: number[], 
  fastPeriod = 12, 
  slowPeriod = 26, 
  signalPeriod = 9
): MACDResult => {
  const fastEMA = calculateEMA(data, fastPeriod)
  const slowEMA = calculateEMA(data, slowPeriod)
  
  // 计算DIF线
  const dif: number[] = []
  for (let i = 0; i < data.length; i++) {
    if (isNaN(fastEMA[i]) || isNaN(slowEMA[i])) {
      dif.push(NaN)
    } else {
      dif.push(new Decimal(fastEMA[i]).minus(slowEMA[i]).toNumber())
    }
  }
  
  // 计算DEA线(DIF的EMA)
  const dea = calculateEMA(dif.filter(v => !isNaN(v)), signalPeriod)
  
  // 补齐DEA数组长度
  const deaFull: number[] = []
  let deaIndex = 0
  for (let i = 0; i < data.length; i++) {
    if (isNaN(dif[i])) {
      deaFull.push(NaN)
    } else {
      deaFull.push(dea[deaIndex] || NaN)
      deaIndex++
    }
  }
  
  // 计算MACD柱
  const macd: number[] = []
  for (let i = 0; i < data.length; i++) {
    if (isNaN(dif[i]) || isNaN(deaFull[i])) {
      macd.push(NaN)
    } else {
      macd.push(new Decimal(dif[i]).minus(deaFull[i]).mul(2).toNumber())
    }
  }
  
  return { dif, dea: deaFull, macd }
}

/**
 * RSI指标计算
 * @param data 收盘价数据
 * @param period 周期，默认14
 * @returns RSI结果
 */
export const calculateRSI = (data: number[], period = 14): RSIResult => {
  const rsi: number[] = []
  const gains: number[] = []
  const losses: number[] = []
  
  // 计算涨跌幅
  for (let i = 1; i < data.length; i++) {
    const change = new Decimal(data[i]).minus(data[i - 1]).toNumber()
    gains.push(change > 0 ? change : 0)
    losses.push(change < 0 ? Math.abs(change) : 0)
  }
  
  // 计算RSI
  for (let i = 0; i < data.length; i++) {
    if (i < period) {
      rsi.push(NaN)
    } else {
      const avgGain = gains.slice(i - period, i).reduce((sum, val) => sum + val, 0) / period
      const avgLoss = losses.slice(i - period, i).reduce((sum, val) => sum + val, 0) / period
      
      if (avgLoss === 0) {
        rsi.push(100)
      } else {
        const rs = new Decimal(avgGain).div(avgLoss)
        const rsiValue = new Decimal(100).minus(new Decimal(100).div(rs.plus(1)))
        rsi.push(rsiValue.toNumber())
      }
    }
  }
  
  return { rsi }
}

/**
 * 布林带计算
 * @param data 收盘价数据
 * @param period 周期，默认20
 * @param stdDev 标准差倍数，默认2
 * @returns 布林带结果
 */
export const calculateBollingerBands = (
  data: number[], 
  period = 20, 
  stdDev = 2
): BollingerBandsResult => {
  const middle: number[] = []
  const upper: number[] = []
  const lower: number[] = []
  
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      middle.push(NaN)
      upper.push(NaN)
      lower.push(NaN)
    } else {
      const slice = data.slice(i - period + 1, i + 1)
      const mean = slice.reduce((sum, val) => sum + val, 0) / period
      
      // 计算标准差
      const variance = slice.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / period
      const standardDeviation = Math.sqrt(variance)
      
      middle.push(mean)
      upper.push(new Decimal(mean).plus(standardDeviation * stdDev).toNumber())
      lower.push(new Decimal(mean).minus(standardDeviation * stdDev).toNumber())
    }
  }
  
  return { upper, middle, lower }
}

/**
 * KDJ指标计算
 * @param klineData K线数据
 * @param kPeriod K值周期，默认9
 * @param dPeriod D值周期，默认3
 * @param jPeriod J值周期，默认3
 * @returns KDJ结果
 */
export const calculateKDJ = (
  klineData: KLineData[], 
  kPeriod = 9, 
  dPeriod = 3, 
  jPeriod = 3
): KDJResult => {
  const rsv: number[] = []
  const k: number[] = []
  const d: number[] = []
  const j: number[] = []
  
  // 计算RSV
  for (let i = 0; i < klineData.length; i++) {
    if (i < kPeriod - 1) {
      rsv.push(NaN)
    } else {
      const slice = klineData.slice(i - kPeriod + 1, i + 1)
      const highest = Math.max(...slice.map(item => item.high))
      const lowest = Math.min(...slice.map(item => item.low))
      const close = klineData[i].close
      
      if (highest === lowest) {
        rsv.push(50)
      } else {
        const rsvValue = new Decimal(close - lowest)
          .div(highest - lowest)
          .mul(100)
          .toNumber()
        rsv.push(rsvValue)
      }
    }
  }
  
  // 计算K值
  let prevK = 50
  for (let i = 0; i < rsv.length; i++) {
    if (isNaN(rsv[i])) {
      k.push(NaN)
    } else {
      const kValue = new Decimal(prevK)
        .mul(2)
        .plus(rsv[i])
        .div(3)
        .toNumber()
      k.push(kValue)
      prevK = kValue
    }
  }
  
  // 计算D值
  let prevD = 50
  for (let i = 0; i < k.length; i++) {
    if (isNaN(k[i])) {
      d.push(NaN)
    } else {
      const dValue = new Decimal(prevD)
        .mul(2)
        .plus(k[i])
        .div(3)
        .toNumber()
      d.push(dValue)
      prevD = dValue
    }
  }
  
  // 计算J值
  for (let i = 0; i < k.length; i++) {
    if (isNaN(k[i]) || isNaN(d[i])) {
      j.push(NaN)
    } else {
      const jValue = new Decimal(k[i])
        .mul(3)
        .minus(new Decimal(d[i]).mul(2))
        .toNumber()
      j.push(jValue)
    }
  }
  
  return { k, d, j }
}

/**
 * 计算收益率
 * @param startValue 起始值
 * @param endValue 结束值
 * @returns 收益率(百分比)
 */
export const calculateReturn = (startValue: number, endValue: number): number => {
  if (startValue === 0) return 0
  return new Decimal(endValue).minus(startValue).div(startValue).mul(100).toNumber()
}

/**
 * 计算年化收益率
 * @param totalReturn 总收益率
 * @param days 天数
 * @returns 年化收益率
 */
export const calculateAnnualizedReturn = (totalReturn: number, days: number): number => {
  if (days === 0) return 0
  const dailyReturn = new Decimal(totalReturn).div(100).plus(1)
  return dailyReturn.pow(365 / days).minus(1).mul(100).toNumber()
}

/**
 * 计算波动率
 * @param returns 收益率数组
 * @returns 波动率
 */
export const calculateVolatility = (returns: number[]): number => {
  if (returns.length === 0) return 0
  
  const mean = returns.reduce((sum, val) => sum + val, 0) / returns.length
  const variance = returns.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / returns.length
  
  return Math.sqrt(variance)
}

/**
 * 计算夏普比率
 * @param returns 收益率数组
 * @param riskFreeRate 无风险利率，默认3%
 * @returns 夏普比率
 */
export const calculateSharpeRatio = (returns: number[], riskFreeRate = 3): number => {
  if (returns.length === 0) return 0
  
  const avgReturn = returns.reduce((sum, val) => sum + val, 0) / returns.length
  const volatility = calculateVolatility(returns)
  
  if (volatility === 0) return 0
  
  return new Decimal(avgReturn).minus(riskFreeRate).div(volatility).toNumber()
}

/**
 * 计算最大回撤
 * @param values 净值数组
 * @returns 最大回撤信息
 */
export const calculateMaxDrawdown = (values: number[]): {
  maxDrawdown: number
  maxDrawdownPercent: number
  startIndex: number
  endIndex: number
  peak: number
  trough: number
} => {
  if (values.length === 0) {
    return {
      maxDrawdown: 0,
      maxDrawdownPercent: 0,
      startIndex: -1,
      endIndex: -1,
      peak: 0,
      trough: 0
    }
  }
  
  let maxDrawdown = 0
  let maxDrawdownPercent = 0
  let peak = values[0]
  let peakIndex = 0
  let startIndex = 0
  let endIndex = 0
  
  for (let i = 1; i < values.length; i++) {
    if (values[i] > peak) {
      peak = values[i]
      peakIndex = i
    } else {
      const drawdown = peak - values[i]
      const drawdownPercent = new Decimal(drawdown).div(peak).mul(100).toNumber()
      
      if (drawdown > maxDrawdown) {
        maxDrawdown = drawdown
        maxDrawdownPercent = drawdownPercent
        startIndex = peakIndex
        endIndex = i
      }
    }
  }
  
  return {
    maxDrawdown,
    maxDrawdownPercent,
    startIndex,
    endIndex,
    peak,
    trough: values[endIndex] || 0
  }
}

/**
 * 计算贝塔系数
 * @param assetReturns 资产收益率
 * @param marketReturns 市场收益率
 * @returns 贝塔系数
 */
export const calculateBeta = (assetReturns: number[], marketReturns: number[]): number => {
  if (assetReturns.length !== marketReturns.length || assetReturns.length === 0) {
    return 0
  }
  
  const assetMean = assetReturns.reduce((sum, val) => sum + val, 0) / assetReturns.length
  const marketMean = marketReturns.reduce((sum, val) => sum + val, 0) / marketReturns.length
  
  let covariance = 0
  let marketVariance = 0
  
  for (let i = 0; i < assetReturns.length; i++) {
    const assetDiff = assetReturns[i] - assetMean
    const marketDiff = marketReturns[i] - marketMean
    
    covariance += assetDiff * marketDiff
    marketVariance += marketDiff * marketDiff
  }
  
  if (marketVariance === 0) return 0
  
  return new Decimal(covariance).div(marketVariance).toNumber()
}

/**
 * 计算信息比率
 * @param portfolioReturns 组合收益率
 * @param benchmarkReturns 基准收益率
 * @returns 信息比率
 */
export const calculateInformationRatio = (
  portfolioReturns: number[], 
  benchmarkReturns: number[]
): number => {
  if (portfolioReturns.length !== benchmarkReturns.length || portfolioReturns.length === 0) {
    return 0
  }
  
  const activeReturns = portfolioReturns.map((ret, i) => ret - benchmarkReturns[i])
  const avgActiveReturn = activeReturns.reduce((sum, val) => sum + val, 0) / activeReturns.length
  const trackingError = calculateVolatility(activeReturns)
  
  if (trackingError === 0) return 0
  
  return new Decimal(avgActiveReturn).div(trackingError).toNumber()
}

/**
 * 计算胜率
 * @param returns 收益率数组
 * @returns 胜率(百分比)
 */
export const calculateWinRate = (returns: number[]): number => {
  if (returns.length === 0) return 0
  
  const winCount = returns.filter(ret => ret > 0).length
  return new Decimal(winCount).div(returns.length).mul(100).toNumber()
}

/**
 * 计算盈亏比
 * @param returns 收益率数组
 * @returns 盈亏比
 */
export const calculateProfitLossRatio = (returns: number[]): number => {
  const profits = returns.filter(ret => ret > 0)
  const losses = returns.filter(ret => ret < 0)
  
  if (profits.length === 0 || losses.length === 0) return 0
  
  const avgProfit = profits.reduce((sum, val) => sum + val, 0) / profits.length
  const avgLoss = Math.abs(losses.reduce((sum, val) => sum + val, 0) / losses.length)
  
  if (avgLoss === 0) return 0
  
  return new Decimal(avgProfit).div(avgLoss).toNumber()
} 