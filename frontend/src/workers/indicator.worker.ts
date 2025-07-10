// 技术指标计算 Web Worker
// import { Big } from 'big.js'  // 暂时注释掉，未使用

interface WorkerMessage {
  id: string
  type: string
  data: any
}

interface KLineData {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

// 移动平均线计算
function calculateMA(data: number[], period: number): number[] {
  const result: number[] = []
  
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(NaN)
    } else {
      let sum = 0
      for (let j = i - period + 1; j <= i; j++) {
        sum += data[j] || 0
      }
      result.push(sum / period)
    }
  }
  
  return result
}

// 指数移动平均线计算
function calculateEMA(data: number[], period: number): number[] {
  const result: number[] = []
  const multiplier = 2 / (period + 1)
  
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      result.push(data[i] || 0)
    } else {
      const ema = ((data[i] || 0) - (result[i - 1] || 0)) * multiplier + (result[i - 1] || 0)
      result.push(ema)
    }
  }
  
  return result
}

// MACD计算
function calculateMACD(data: number[], fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) {
  const fastEMA = calculateEMA(data, fastPeriod)
  const slowEMA = calculateEMA(data, slowPeriod)
  
  // DIF线
  const dif = fastEMA.map((fast, index) => fast - (slowEMA[index] || 0))
  
  // DEA线 (信号线)
  const dea = calculateEMA(dif.filter(v => !isNaN(v)), signalPeriod)
  
  // MACD柱状图
  const macd = dif.map((d, index) => {
    if (index < slowPeriod - 1 + signalPeriod - 1) {
      return NaN
    }
    return (d - (dea[index - (slowPeriod - 1)] || 0)) * 2
  })
  
  return { dif, dea, macd }
}

// RSI计算
function calculateRSI(data: number[], period = 14): number[] {
  const result: number[] = []
  const gains: number[] = []
  const losses: number[] = []
  
  // 计算涨跌幅
  for (let i = 1; i < data.length; i++) {
    const change = (data[i] || 0) - (data[i - 1] || 0)
    gains.push(change > 0 ? change : 0)
    losses.push(change < 0 ? Math.abs(change) : 0)
  }
  
  // 计算RSI
  for (let i = 0; i < gains.length; i++) {
    if (i < period - 1) {
      result.push(NaN)
    } else {
      const avgGain = gains.slice(i - period + 1, i + 1).reduce((sum, gain) => sum + gain, 0) / period
      const avgLoss = losses.slice(i - period + 1, i + 1).reduce((sum, loss) => sum + loss, 0) / period
      
      if (avgLoss === 0) {
        result.push(100)
      } else {
        const rs = avgGain / avgLoss
        const rsi = 100 - (100 / (1 + rs))
        result.push(rsi)
      }
    }
  }
  
  return [NaN, ...result] // 添加第一个NaN，因为第一个数据点没有变化
}

// KDJ计算
function calculateKDJ(data: KLineData[], kPeriod = 9, _dPeriod = 3, _jPeriod = 3) {
  const result = {
    k: [] as number[],
    d: [] as number[],
    j: [] as number[]
  }
  
  let prevK = 50
  let prevD = 50
  
  for (let i = 0; i < data.length; i++) {
    if (i < kPeriod - 1) {
      result.k.push(NaN)
      result.d.push(NaN)
      result.j.push(NaN)
    } else {
      // 计算最高价和最低价
      const periodData = data.slice(i - kPeriod + 1, i + 1)
      const highestHigh = Math.max(...periodData.map(d => d.high))
      const lowestLow = Math.min(...periodData.map(d => d.low))
      
      // 计算RSV
      const rsv = (((data[i]?.close || 0) - lowestLow) / (highestHigh - lowestLow)) * 100
      
      // 计算K值
      const k = (2 * prevK + rsv) / 3
      result.k.push(k)
      
      // 计算D值
      const d = (2 * prevD + k) / 3
      result.d.push(d)
      
      // 计算J值
      const j = 3 * k - 2 * d
      result.j.push(j)
      
      prevK = k
      prevD = d
    }
  }
  
  return result
}

// 布林带计算
function calculateBOLL(data: number[], period = 20, multiplier = 2) {
  const ma = calculateMA(data, period)
  const upper: number[] = []
  const lower: number[] = []
  
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      upper.push(NaN)
      lower.push(NaN)
    } else {
      // 计算标准差
      const periodData = data.slice(i - period + 1, i + 1)
      const mean = ma[i]
      const variance = periodData.reduce((sum, value) => sum + Math.pow(value - (mean || 0), 2), 0) / period
      const stdDev = Math.sqrt(variance)
      
      upper.push((mean || 0) + multiplier * stdDev)
      lower.push((mean || 0) - multiplier * stdDev)
    }
  }
  
  return {
    upper,
    middle: ma,
    lower
  }
}

// CCI计算
function calculateCCI(data: KLineData[], period = 14): number[] {
  const result: number[] = []
  const typicalPrices = data.map(d => (d.high + d.low + d.close) / 3)
  
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(NaN)
    } else {
      const periodData = typicalPrices.slice(i - period + 1, i + 1)
      const sma = periodData.reduce((sum, price) => sum + price, 0) / period
      const meanDeviation = periodData.reduce((sum, price) => sum + Math.abs(price - sma), 0) / period
      
      const cci = ((typicalPrices[i] || 0) - sma) / (0.015 * meanDeviation)
      result.push(cci)
    }
  }
  
  return result
}

// 威廉指标计算
function calculateWR(data: KLineData[], period = 14): number[] {
  const result: number[] = []
  
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(NaN)
    } else {
      const periodData = data.slice(i - period + 1, i + 1)
      const highestHigh = Math.max(...periodData.map(d => d.high))
      const lowestLow = Math.min(...periodData.map(d => d.low))
      
      const wr = ((highestHigh - (data[i]?.close || 0)) / (highestHigh - lowestLow)) * -100
      result.push(wr)
    }
  }
  
  return result
}

// OBV计算
function calculateOBV(data: KLineData[]): number[] {
  const result: number[] = []
  let obv = 0
  
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      result.push(0)
    } else {
      if ((data[i]?.close || 0) > (data[i - 1]?.close || 0)) {
        obv += (data[i]?.volume || 0)
      } else if ((data[i]?.close || 0) < (data[i - 1]?.close || 0)) {
        obv -= (data[i]?.volume || 0)
      }
      result.push(obv)
    }
  }
  
  return result
}

// BIAS计算
function calculateBIAS(data: number[], periods: number[] = [6, 12, 24]) {
  const result: { [key: string]: number[] } = {}
  
  periods.forEach(period => {
    const ma = calculateMA(data, period)
    const bias = data.map((price, index) => {
      if (isNaN(ma[index] || 0)) return NaN
      return ((price - (ma[index] || 0)) / (ma[index] || 1)) * 100
    })
    result[`bias${period}`] = bias
  })
  
  return result
}

// 消息处理
self.onmessage = function(e: MessageEvent<WorkerMessage>) {
  const { id, type, data } = e.data
  
  try {
    let result: any
    
    switch (type) {
      case 'MA':
        result = calculateMA(data.prices, data.period)
        break
        
      case 'EMA':
        result = calculateEMA(data.prices, data.period)
        break
        
      case 'MACD':
        result = calculateMACD(data.prices, data.fastPeriod, data.slowPeriod, data.signalPeriod)
        break
        
      case 'RSI':
        result = calculateRSI(data.prices, data.period)
        break
        
      case 'KDJ':
        result = calculateKDJ(data.klineData, data.kPeriod, data.dPeriod, data.jPeriod)
        break
        
      case 'BOLL':
        result = calculateBOLL(data.prices, data.period, data.multiplier)
        break
        
      case 'CCI':
        result = calculateCCI(data.klineData, data.period)
        break
        
      case 'WR':
        result = calculateWR(data.klineData, data.period)
        break
        
      case 'OBV':
        result = calculateOBV(data.klineData)
        break
        
      case 'BIAS':
        result = calculateBIAS(data.prices, data.periods)
        break
        
      default:
        throw new Error(`Unknown indicator type: ${type}`)
    }
    
    // 发送计算结果
    self.postMessage({
      id,
      type: 'success',
      data: result
    })
    
  } catch (error) {
    // 发送错误信息
    self.postMessage({
      id,
      type: 'error',
      error: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}

// 导出类型定义
export type { WorkerMessage, KLineData }