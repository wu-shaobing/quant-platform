/**
 * 技术指标计算库
 * 包含各种常用技术指标的计算函数
 */

export interface KLinePoint {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface IndicatorResult {
  name: string
  data: Array<{ timestamp: number; value: number | null }>
  color?: string
  lineStyle?: 'solid' | 'dashed' | 'dotted'
}

export interface MAResult extends IndicatorResult {
  period: number
}

export interface MACDResult {
  dif: IndicatorResult
  dea: IndicatorResult
  macd: IndicatorResult
}

export interface RSIResult extends IndicatorResult {
  period: number
}

export interface BollingerResult {
  upper: IndicatorResult
  middle: IndicatorResult
  lower: IndicatorResult
}

export interface KDJResult {
  k: IndicatorResult
  d: IndicatorResult
  j: IndicatorResult
}

/**
 * 计算简单移动平均线 (SMA)
 */
export function calculateSMA(data: KLinePoint[], period: number): MAResult {
  const result: Array<{ timestamp: number; value: number | null }> = []

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push({ timestamp: data[i].timestamp, value: null })
    } else {
      let sum = 0
      for (let j = i - period + 1; j <= i; j++) {
        sum += data[j].close
      }
      result.push({
        timestamp: data[i].timestamp,
        value: sum / period
      })
    }
  }

  return {
    name: `MA${period}`,
    data: result,
    period,
    color: period === 5 ? '#FF6B6B' : period === 10 ? '#4ECDC4' : '#45B7D1'
  }
}

/**
 * 计算指数移动平均线 (EMA)
 */
export function calculateEMA(data: KLinePoint[], period: number): MAResult {
  const result: Array<{ timestamp: number; value: number | null }> = []
  const multiplier = 2 / (period + 1)

  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      result.push({ timestamp: data[i].timestamp, value: data[i].close })
    } else {
      const previousEMA = result[i - 1].value || data[i - 1].close
      const currentEMA = (data[i].close - previousEMA) * multiplier + previousEMA
      result.push({ timestamp: data[i].timestamp, value: currentEMA })
    }
  }

  return {
    name: `EMA${period}`,
    data: result,
    period,
    color: period === 12 ? '#FF9F43' : period === 26 ? '#10AC84' : '#5F27CD'
  }
}

/**
 * 计算MACD指标
 */
export function calculateMACD(data: KLinePoint[], fastPeriod = 12, slowPeriod = 26, signalPeriod = 9): MACDResult {
  const fastEMA = calculateEMA(data, fastPeriod)
  const slowEMA = calculateEMA(data, slowPeriod)

  // 计算DIF线
  const difData: Array<{ timestamp: number; value: number | null }> = []
  for (let i = 0; i < data.length; i++) {
    const fastValue = fastEMA.data[i].value
    const slowValue = slowEMA.data[i].value

    if (fastValue !== null && slowValue !== null) {
      difData.push({
        timestamp: data[i].timestamp,
        value: fastValue - slowValue
      })
    } else {
      difData.push({ timestamp: data[i].timestamp, value: null })
    }
  }

  // 计算DEA线（DIF的EMA）
  const deaData: Array<{ timestamp: number; value: number | null }> = []
  const deaMultiplier = 2 / (signalPeriod + 1)

  for (let i = 0; i < difData.length; i++) {
    if (difData[i].value === null) {
      deaData.push({ timestamp: difData[i].timestamp, value: null })
    } else if (i === 0 || deaData[i - 1].value === null) {
      deaData.push({ timestamp: difData[i].timestamp, value: difData[i].value })
    } else {
      const previousDEA = deaData[i - 1].value!
      const currentDEA = (difData[i].value! - previousDEA) * deaMultiplier + previousDEA
      deaData.push({ timestamp: difData[i].timestamp, value: currentDEA })
    }
  }

  // 计算MACD柱状图
  const macdData: Array<{ timestamp: number; value: number | null }> = []
  for (let i = 0; i < data.length; i++) {
    const difValue = difData[i].value
    const deaValue = deaData[i].value

    if (difValue !== null && deaValue !== null) {
      macdData.push({
        timestamp: data[i].timestamp,
        value: 2 * (difValue - deaValue)
      })
    } else {
      macdData.push({ timestamp: data[i].timestamp, value: null })
    }
  }

  return {
    dif: {
      name: 'DIF',
      data: difData,
      color: '#FF6B6B'
    },
    dea: {
      name: 'DEA',
      data: deaData,
      color: '#4ECDC4'
    },
    macd: {
      name: 'MACD',
      data: macdData,
      color: '#45B7D1'
    }
  }
}

/**
 * 计算RSI指标
 */
export function calculateRSI(data: KLinePoint[], period = 14): RSIResult {
  const result: Array<{ timestamp: number; value: number | null }> = []

  for (let i = 0; i < data.length; i++) {
    if (i < period) {
      result.push({ timestamp: data[i].timestamp, value: null })
    } else {
      let gains = 0
      let losses = 0

      for (let j = i - period + 1; j <= i; j++) {
        const change = data[j].close - data[j - 1].close
        if (change > 0) {
          gains += change
        } else {
          losses += Math.abs(change)
        }
      }

      const avgGain = gains / period
      const avgLoss = losses / period

      if (avgLoss === 0) {
        result.push({ timestamp: data[i].timestamp, value: 100 })
      } else {
        const rs = avgGain / avgLoss
        const rsi = 100 - (100 / (1 + rs))
        result.push({ timestamp: data[i].timestamp, value: rsi })
      }
    }
  }

  return {
    name: `RSI${period}`,
    data: result,
    period,
    color: '#9C88FF'
  }
}

/**
 * 计算布林带指标
 */
export function calculateBollingerBands(data: KLinePoint[], period = 20, multiplier = 2): BollingerResult {
  const sma = calculateSMA(data, period)
  const upper: Array<{ timestamp: number; value: number | null }> = []
  const lower: Array<{ timestamp: number; value: number | null }> = []

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      upper.push({ timestamp: data[i].timestamp, value: null })
      lower.push({ timestamp: data[i].timestamp, value: null })
    } else {
      // 计算标准差
      const mean = sma.data[i].value!
      let sumSquaredDiff = 0

      for (let j = i - period + 1; j <= i; j++) {
        const diff = data[j].close - mean
        sumSquaredDiff += diff * diff
      }

      const stdDev = Math.sqrt(sumSquaredDiff / period)

      upper.push({
        timestamp: data[i].timestamp,
        value: mean + (multiplier * stdDev)
      })
      lower.push({
        timestamp: data[i].timestamp,
        value: mean - (multiplier * stdDev)
      })
    }
  }

  return {
    upper: {
      name: 'BOLL上轨',
      data: upper,
      color: '#FF6B6B'
    },
    middle: {
      name: 'BOLL中轨',
      data: sma.data,
      color: '#4ECDC4'
    },
    lower: {
      name: 'BOLL下轨',
      data: lower,
      color: '#45B7D1'
    }
  }
}

/**
 * 计算KDJ指标
 */
export function calculateKDJ(data: KLinePoint[], kPeriod = 9, dPeriod = 3, jPeriod = 3): KDJResult {
  const kData: Array<{ timestamp: number; value: number | null }> = []
  const dData: Array<{ timestamp: number; value: number | null }> = []
  const jData: Array<{ timestamp: number; value: number | null }> = []

  let prevK = 50
  let prevD = 50

  for (let i = 0; i < data.length; i++) {
    if (i < kPeriod - 1) {
      kData.push({ timestamp: data[i].timestamp, value: null })
      dData.push({ timestamp: data[i].timestamp, value: null })
      jData.push({ timestamp: data[i].timestamp, value: null })
    } else {
      // 计算最高价和最低价
      let highest = data[i - kPeriod + 1].high
      let lowest = data[i - kPeriod + 1].low

      for (let j = i - kPeriod + 2; j <= i; j++) {
        highest = Math.max(highest, data[j].high)
        lowest = Math.min(lowest, data[j].low)
      }

      // 计算RSV
      const rsv = highest === lowest ? 0 : ((data[i].close - lowest) / (highest - lowest)) * 100

      // 计算K值
      const k = (2 * prevK + rsv) / 3

      // 计算D值
      const d = (2 * prevD + k) / 3

      // 计算J值
      const j = 3 * k - 2 * d

      kData.push({ timestamp: data[i].timestamp, value: k })
      dData.push({ timestamp: data[i].timestamp, value: d })
      jData.push({ timestamp: data[i].timestamp, value: j })

      prevK = k
      prevD = d
    }
  }

  return {
    k: {
      name: 'K',
      data: kData,
      color: '#FF6B6B'
    },
    d: {
      name: 'D',
      data: dData,
      color: '#4ECDC4'
    },
    j: {
      name: 'J',
      data: jData,
      color: '#45B7D1'
    }
  }
}

/**
 * 计算威廉指标 (WR)
 */
export function calculateWR(data: KLinePoint[], period = 14): IndicatorResult {
  const result: Array<{ timestamp: number; value: number | null }> = []

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push({ timestamp: data[i].timestamp, value: null })
    } else {
      let highest = data[i - period + 1].high
      let lowest = data[i - period + 1].low

      for (let j = i - period + 2; j <= i; j++) {
        highest = Math.max(highest, data[j].high)
        lowest = Math.min(lowest, data[j].low)
      }

      const wr = highest === lowest ? 0 : ((highest - data[i].close) / (highest - lowest)) * 100
      result.push({ timestamp: data[i].timestamp, value: wr })
    }
  }

  return {
    name: `WR${period}`,
    data: result,
    color: '#FFA726'
  }
}

/**
 * 计算CCI指标
 */
export function calculateCCI(data: KLinePoint[], period = 14): IndicatorResult {
  const result: Array<{ timestamp: number; value: number | null }> = []

  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push({ timestamp: data[i].timestamp, value: null })
    } else {
      // 计算典型价格
      const typicalPrices: number[] = []
      for (let j = i - period + 1; j <= i; j++) {
        typicalPrices.push((data[j].high + data[j].low + data[j].close) / 3)
      }

      // 计算平均典型价格
      const avgTypicalPrice = typicalPrices.reduce((sum, price) => sum + price, 0) / period

      // 计算平均绝对偏差
      const avgDeviation = typicalPrices.reduce((sum, price) => sum + Math.abs(price - avgTypicalPrice), 0) / period

      // 计算CCI
      const currentTypicalPrice = (data[i].high + data[i].low + data[i].close) / 3
      const cci = avgDeviation === 0 ? 0 : (currentTypicalPrice - avgTypicalPrice) / (0.015 * avgDeviation)

      result.push({ timestamp: data[i].timestamp, value: cci })
    }
  }

  return {
    name: `CCI${period}`,
    data: result,
    color: '#AB47BC'
  }
}

/**
 * 计算成交量加权平均价格 (VWAP)
 */
export function calculateVWAP(data: KLinePoint[]): IndicatorResult {
  const result: Array<{ timestamp: number; value: number | null }> = []
  let cumulativeVolume = 0
  let cumulativeVolumePrice = 0

  for (let i = 0; i < data.length; i++) {
    const typicalPrice = (data[i].high + data[i].low + data[i].close) / 3
    cumulativeVolumePrice += typicalPrice * data[i].volume
    cumulativeVolume += data[i].volume

    const vwap = cumulativeVolume === 0 ? 0 : cumulativeVolumePrice / cumulativeVolume
    result.push({ timestamp: data[i].timestamp, value: vwap })
  }

  return {
    name: 'VWAP',
    data: result,
    color: '#26A69A'
  }
}

/**
 * 计算平均真实波幅 (ATR)
 */
export function calculateATR(data: KLinePoint[], period = 14): IndicatorResult {
  const result: Array<{ timestamp: number; value: number | null }> = []
  const trueRanges: number[] = []

  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      trueRanges.push(data[i].high - data[i].low)
      result.push({ timestamp: data[i].timestamp, value: null })
    } else {
      const tr1 = data[i].high - data[i].low
      const tr2 = Math.abs(data[i].high - data[i - 1].close)
      const tr3 = Math.abs(data[i].low - data[i - 1].close)
      const trueRange = Math.max(tr1, tr2, tr3)

      trueRanges.push(trueRange)

      if (i < period) {
        result.push({ timestamp: data[i].timestamp, value: null })
      } else {
        const atr = trueRanges.slice(i - period + 1, i + 1).reduce((sum, tr) => sum + tr, 0) / period
        result.push({ timestamp: data[i].timestamp, value: atr })
      }
    }
  }

  return {
    name: `ATR${period}`,
    data: result,
    color: '#FF7043'
  }
}
