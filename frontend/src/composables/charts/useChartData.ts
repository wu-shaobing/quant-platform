// src/composables/charts/useChartData.ts
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { EChartsOption } from 'echarts'
import type { 
  ChartDataPoint, 
  KLineDataPoint, 
  PerformanceData,
  RiskMetrics,
  EquityPoint,
  DrawdownPoint 
} from '@/types/chart'

/**
 * 图表数据管理组合函数
 * 负责生成和管理各种图表的数据和配置
 */
export const useChartData = () => {
  // ============ 状态管理 ============
  
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 图表主题配置
  const chartTheme = {
    colors: [
      '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
      '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#5470c6'
    ],
    backgroundColor: 'transparent',
    textStyle: {
      color: '#333',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e0e0e0',
      borderWidth: 1,
      textStyle: {
        color: '#333'
      }
    }
  }

  // ============ 数据生成方法 ============

  /**
   * 生成K线图数据
   */
  const generateKLineData = (
    symbol: string, 
    period: string = '1d', 
    count: number = 200
  ): KLineDataPoint[] => {
    const data: KLineDataPoint[] = []
    const basePrice = 100 + Math.random() * 50
    let currentPrice = basePrice
    
    const now = Date.now()
    const interval = period === '1d' ? 24 * 60 * 60 * 1000 : 60 * 60 * 1000
    
    for (let i = count; i >= 0; i--) {
      const timestamp = now - i * interval
      const date = new Date(timestamp)
      
      // 模拟价格波动
      const change = (Math.random() - 0.5) * 0.1
      const open = currentPrice
      const close = open * (1 + change)
      const high = Math.max(open, close) * (1 + Math.random() * 0.02)
      const low = Math.min(open, close) * (1 - Math.random() * 0.02)
      const volume = Math.floor((500000 + Math.random() * 1000000))
      
      data.push({
        timestamp,
        date: date.toISOString().split('T')[0],
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
        volume,
        amount: volume * close
      })
      
      currentPrice = close
    }
    
    return data
  }

  /**
   * 生成折线图数据
   */
  const generateLineData = (
    days: number = 30, 
    baseValue: number = 100,
    volatility: number = 0.02
  ): ChartDataPoint[] => {
    const data: ChartDataPoint[] = []
    let currentValue = baseValue
    
    for (let i = 0; i < days; i++) {
      const date = new Date()
      date.setDate(date.getDate() - (days - i))
      
      // 添加随机波动
      const change = (Math.random() - 0.5) * volatility * 2
      currentValue *= (1 + change)
      
      data.push({
        date: date.toISOString().split('T')[0],
        value: Number(currentValue.toFixed(2)),
        timestamp: date.getTime()
      })
    }
    
    return data
  }

  /**
   * 生成饼图数据
   */
  const generatePieData = (categories: string[]): Array<{name: string, value: number}> => {
    return categories.map(category => ({
      name: category,
      value: Math.floor(Math.random() * 100) + 10
    }))
  }

  /**
   * 生成柱状图数据
   */
  const generateBarData = (
    categories: string[], 
    series: number = 1
  ): Array<{name: string, data: number[]}> => {
    const result = []
    
    for (let i = 0; i < series; i++) {
      result.push({
        name: `系列${i + 1}`,
        data: categories.map(() => Math.floor(Math.random() * 100) + 10)
      })
    }
    
    return result
  }

  /**
   * 生成净值曲线数据
   */
  const generateEquityData = (
    days: number = 252,
    initialValue: number = 1000000,
    annualReturn: number = 0.15,
    volatility: number = 0.2
  ): EquityPoint[] => {
    const data: EquityPoint[] = []
    let equity = initialValue
    let cash = initialValue * 0.1
    let positions = initialValue * 0.9
    
    const dailyReturn = annualReturn / 252
    const dailyVol = volatility / Math.sqrt(252)
    
    for (let i = 0; i < days; i++) {
      const date = new Date()
      date.setDate(date.getDate() - (days - i))
      
      // 模拟每日收益
      const randomReturn = (Math.random() - 0.5) * dailyVol * 2 + dailyReturn
      positions *= (1 + randomReturn)
      equity = cash + positions
      
      data.push({
        date: date.toISOString().split('T')[0],
        timestamp: date.getTime(),
        equity: Number(equity.toFixed(2)),
        cash: Number(cash.toFixed(2)),
        positions: Number(positions.toFixed(2)),
        totalValue: Number(equity.toFixed(2))
      })
    }
    
    return data
  }

  /**
   * 生成回撤数据
   */
  const generateDrawdownData = (equityData: EquityPoint[]): DrawdownPoint[] => {
    const data: DrawdownPoint[] = []
    let peak = equityData[0]?.equity || 0
    
    equityData.forEach((point, index) => {
      if (point.equity > peak) {
        peak = point.equity
      }
      
      const drawdown = (point.equity - peak) / peak
      
      data.push({
        date: point.date,
        timestamp: point.timestamp,
        drawdown: Number(drawdown.toFixed(4)),
        underwater: drawdown < 0 ? 1 : 0,
        peak: Number(peak.toFixed(2)),
        valley: Number(point.equity.toFixed(2))
      })
    })
    
    return data
  }

  // ============ 图表配置方法 ============

  /**
   * 获取净值曲线图配置
   */
  const getEquityChartOption = (data: EquityPoint[]): EChartsOption => {
    return {
      ...chartTheme,
      title: {
        text: '净值曲线',
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'normal'
        }
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const point = params[0]
          const date = point.axisValue
          const value = point.value
          return `${date}<br/>净值: ${value.toLocaleString()}`
        }
      },
      xAxis: {
        type: 'category',
        data: data.map(d => d.date),
        boundaryGap: false,
        axisLine: {
          lineStyle: { color: '#e0e0e0' }
        },
        axisTick: { show: false },
        axisLabel: {
          color: '#666',
          fontSize: 12
        }
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#666',
          fontSize: 12,
          formatter: (value: number) => (value / 10000).toFixed(1) + '万'
        },
        splitLine: {
          lineStyle: { color: '#f0f0f0' }
        }
      },
      series: [
        {
          name: '净值',
          type: 'line',
          data: data.map(d => d.equity),
          smooth: true,
          symbol: 'none',
          lineStyle: {
            width: 2,
            color: chartTheme.colors[0]
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: chartTheme.colors[0] + '40' },
                { offset: 1, color: chartTheme.colors[0] + '10' }
              ]
            }
          }
        }
      ]
    }
  }

  /**
   * 获取K线图配置
   */
  const getKLineChartOption = (data: KLineDataPoint[]): EChartsOption => {
    return {
      ...chartTheme,
      title: {
        text: 'K线图',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        formatter: (params: any) => {
          const point = params[0]
          const data = point.data
          return `
            ${point.axisValue}<br/>
            开盘: ${data[1]}<br/>
            收盘: ${data[2]}<br/>
            最高: ${data[4]}<br/>
            最低: ${data[3]}
          `
        }
      },
      xAxis: {
        type: 'category',
        data: data.map(d => d.date),
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      },
      yAxis: {
        scale: true,
        splitArea: { show: true }
      },
      dataZoom: [
        {
          type: 'inside',
          start: 70,
          end: 100
        },
        {
          show: true,
          type: 'slider',
          top: '90%',
          start: 70,
          end: 100
        }
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: data.map(d => [d.open, d.close, d.low, d.high]),
          itemStyle: {
            color: '#00da3c',
            color0: '#ec0000',
            borderColor: '#008F28',
            borderColor0: '#8A0000'
          }
        }
      ]
    }
  }

  /**
   * 获取持仓饼图配置
   */
  const getPositionPieChartOption = (data: Array<{name: string, value: number}>): EChartsOption => {
    return {
      ...chartTheme,
      title: {
        text: '持仓分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '持仓',
          type: 'pie',
          radius: '50%',
          data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
  }

  /**
   * 获取收益趋势图配置
   */
  const getReturnTrendChartOption = (data: ChartDataPoint[]): EChartsOption => {
    return {
      ...chartTheme,
      title: {
        text: '收益趋势',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const point = params[0]
          return `${point.axisValue}<br/>收益率: ${(point.value * 100).toFixed(2)}%`
        }
      },
      xAxis: {
        type: 'category',
        data: data.map(d => d.date),
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [
        {
          name: '收益率',
          type: 'line',
          data: data.map(d => (d.value * 100).toFixed(2)),
          smooth: true,
          lineStyle: {
            color: chartTheme.colors[1]
          }
        }
      ]
    }
  }

  /**
   * 获取风险分布图配置
   */
  const getRiskDistributionChartOption = (riskMetrics: RiskMetrics): EChartsOption => {
    const metrics = [
      { name: '波动率', value: riskMetrics.volatility * 100 },
      { name: '最大回撤', value: Math.abs(riskMetrics.maxDrawdown) * 100 },
      { name: 'VaR(95%)', value: Math.abs(riskMetrics.var95) * 100 },
      { name: '下行标准差', value: riskMetrics.downSideDeviation * 100 }
    ]

    return {
      ...chartTheme,
      title: {
        text: '风险指标',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      xAxis: {
        type: 'category',
        data: metrics.map(m => m.name),
        axisLabel: {
          interval: 0,
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [
        {
          name: '风险值',
          type: 'bar',
          data: metrics.map(m => m.value.toFixed(2)),
          itemStyle: {
            color: (params: any) => {
              const colors = ['#91cc75', '#fac858', '#ee6666', '#fc8452']
              return colors[params.dataIndex % colors.length]
            }
          }
        }
      ]
    }
  }

  /**
   * 获取策略对比图配置
   */
  const getStrategyComparisonChartOption = (strategies: Array<{
    name: string
    data: Array<[string, number]>
  }>): EChartsOption => {
    return {
      ...chartTheme,
      title: {
        text: '策略对比',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: strategies.map(s => s.name),
        bottom: 0
      },
      xAxis: {
        type: 'time',
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: strategies.map((strategy, index) => ({
        name: strategy.name,
        type: 'line',
        data: strategy.data.map(item => [item[0], item[1] * 100]),
        smooth: true,
        lineStyle: {
          width: 2,
          color: chartTheme.colors[index % chartTheme.colors.length]
        }
      }))
    }
  }

  /**
   * 获取回撤图配置
   */
  const getDrawdownChartOption = (data: DrawdownPoint[]): EChartsOption => {
    return {
      ...chartTheme,
      title: {
        text: '回撤分析',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const point = params[0]
          const value = Math.abs(point.value)
          return `${point.axisValue}<br/>回撤: ${(value * 100).toFixed(2)}%`
        }
      },
      xAxis: {
        type: 'category',
        data: data.map(d => d.date),
        boundaryGap: false
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value: number) => `${(Math.abs(value) * 100).toFixed(1)}%`
        }
      },
      series: [
        {
          name: '回撤',
          type: 'line',
          data: data.map(d => d.drawdown),
          areaStyle: {
            color: '#ff4d4f20'
          },
          lineStyle: {
            color: '#ff4d4f'
          },
          smooth: true
        }
      ]
    }
  }

  // ============ 工具方法 ============

  /**
   * 计算技术指标 - 移动平均线
   */
  const calculateMA = (data: number[], period: number): number[] => {
    const result: number[] = []
    
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(NaN)
      } else {
        const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0)
        result.push(sum / period)
      }
    }
    
    return result
  }

  /**
   * 计算RSI指标
   */
  const calculateRSI = (data: number[], period: number = 14): number[] => {
    const result: number[] = []
    const gains: number[] = []
    const losses: number[] = []
    
    for (let i = 1; i < data.length; i++) {
      const change = data[i] - data[i - 1]
      gains.push(change > 0 ? change : 0)
      losses.push(change < 0 ? Math.abs(change) : 0)
    }
    
    for (let i = 0; i < gains.length; i++) {
      if (i < period - 1) {
        result.push(NaN)
      } else {
        const avgGain = gains.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period
        const avgLoss = losses.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0) / period
        
        if (avgLoss === 0) {
          result.push(100)
        } else {
          const rs = avgGain / avgLoss
          const rsi = 100 - (100 / (1 + rs))
          result.push(rsi)
        }
      }
    }
    
    return [NaN, ...result] // 添加第一个数据点的占位符
  }

  /**
   * 计算MACD指标
   */
  const calculateMACD = (data: number[], fastPeriod: number = 12, slowPeriod: number = 26, signalPeriod: number = 9) => {
    const ema12 = calculateEMA(data, fastPeriod)
    const ema26 = calculateEMA(data, slowPeriod)
    
    const dif = ema12.map((val, i) => val - ema26[i])
    const dea = calculateEMA(dif, signalPeriod)
    const macd = dif.map((val, i) => (val - dea[i]) * 2)
    
    return { dif, dea, macd }
  }

  /**
   * 计算EMA指数移动平均
   */
  const calculateEMA = (data: number[], period: number): number[] => {
    const result: number[] = []
    const multiplier = 2 / (period + 1)
    
    result[0] = data[0]
    
    for (let i = 1; i < data.length; i++) {
      result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]
    }
    
    return result
  }

  /**
   * 处理图表数据错误
   */
  const handleError = (errorMessage: string) => {
    error.value = errorMessage
    ElMessage.error(errorMessage)
    console.error('Chart data error:', errorMessage)
  }

  /**
   * 清除错误状态
   */
  const clearError = () => {
    error.value = null
  }

  return {
    // 状态
    loading,
    error,
    
    // 数据生成方法
    generateKLineData,
    generateLineData,
    generatePieData,
    generateBarData,
    generateEquityData,
    generateDrawdownData,
    
    // 图表配置方法
    getEquityChartOption,
    getKLineChartOption,
    getPositionPieChartOption,
    getReturnTrendChartOption,
    getRiskDistributionChartOption,
    getStrategyComparisonChartOption,
    getDrawdownChartOption,
    
    // 技术指标计算
    calculateMA,
    calculateRSI,
    calculateMACD,
    calculateEMA,
    
    // 工具方法
    handleError,
    clearError,
    
    // 主题配置
    chartTheme
  }
}