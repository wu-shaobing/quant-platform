import { ref, computed } from 'vue'
import type { IndicatorType, TechnicalIndicator } from '@/types/chart'

export const useIndicators = () => {
  const activeIndicators = ref<string[]>([])
  const indicatorConfigs = ref<Record<string, any>>({})
  const calculatedIndicators = ref<Record<string, any>>({})

  // 可用指标配置
  const availableIndicators: IndicatorType[] = [
    { value: 'MA', label: '移动平均线' },
    { value: 'MACD', label: 'MACD' },
    { value: 'RSI', label: 'RSI' },
    { value: 'KDJ', label: 'KDJ' },
    { value: 'BOLL', label: '布林带' },
    { value: 'VOL', label: '成交量' },
    { value: 'OBV', label: 'OBV' },
    { value: 'CCI', label: 'CCI' },
    { value: 'WR', label: 'WR' },
    { value: 'BIAS', label: 'BIAS' }
  ]

  // 添加指标
  const addIndicator = (indicatorType: string) => {
    if (!activeIndicators.value.includes(indicatorType)) {
      activeIndicators.value.push(indicatorType)
      
      // 设置默认配置
      setDefaultConfig(indicatorType)
      
      // 计算指标数据
      calculateIndicator(indicatorType)
    }
  }

  // 移除指标
  const removeIndicator = (indicatorType: string) => {
    const index = activeIndicators.value.indexOf(indicatorType)
    if (index > -1) {
      activeIndicators.value.splice(index, 1)
      delete indicatorConfigs.value[indicatorType]
      delete calculatedIndicators.value[indicatorType]
    }
  }

  // 更新指标配置
  const updateIndicatorConfig = (indicatorType: string, config: any) => {
    indicatorConfigs.value[indicatorType] = { ...config }
    calculateIndicator(indicatorType)
  }

  // 设置默认配置
  const setDefaultConfig = (indicatorType: string) => {
    const defaultConfigs: Record<string, any> = {
      MA: { periods: [5, 10, 20, 60] },
      MACD: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 },
      RSI: { period: 14 },
      KDJ: { kPeriod: 9, dPeriod: 3, jPeriod: 3 },
      BOLL: { period: 20, multiplier: 2 },
      VOL: { periods: [5, 10] },
      OBV: {},
      CCI: { period: 14 },
      WR: { period: 14 },
      BIAS: { periods: [6, 12, 24] }
    }

    indicatorConfigs.value[indicatorType] = defaultConfigs[indicatorType] || {}
  }

  // 计算指标
  const calculateIndicator = (indicatorType: string) => {
    // 这里应该调用实际的技术指标计算函数
    // 为了演示，这里返回模拟数据
    
    switch (indicatorType) {
      case 'MA':
        calculatedIndicators.value[indicatorType] = calculateMA()
        break
      case 'MACD':
        calculatedIndicators.value[indicatorType] = calculateMACD()
        break
      case 'RSI':
        calculatedIndicators.value[indicatorType] = calculateRSI()
        break
      default:
        calculatedIndicators.value[indicatorType] = []
    }
  }

  // 移动平均线计算
  const calculateMA = () => {
    const config = indicatorConfigs.value.MA
    const result: Record<string, number[]> = {}
    
    config.periods.forEach((period: number) => {
      // 模拟MA计算
      result[period.toString()] = Array.from({ length: 100 }, (_, i) => 
        Math.random() * 100 + 50
      )
    })
    
    return result
  }

  // MACD计算
  const calculateMACD = () => {
    // 模拟MACD计算
    return {
      dif: Array.from({ length: 100 }, () => Math.random() * 2 - 1),
      dea: Array.from({ length: 100 }, () => Math.random() * 2 - 1),
      macd: Array.from({ length: 100 }, () => Math.random() * 4 - 2)
    }
  }

  // RSI计算
  const calculateRSI = () => {
    // 模拟RSI计算
    return Array.from({ length: 100 }, () => Math.random() * 100)
  }

  // 获取指标标签
  const getIndicatorLabel = (indicatorType: string) => {
    const indicator = availableIndicators.find(item => item.value === indicatorType)
    return indicator?.label || indicatorType
  }

  // 获取指标配置组件
  const getIndicatorConfigComponent = (indicatorType: string) => {
    // 返回对应的配置组件名称
    return `${indicatorType}Config`
  }

  return {
    availableIndicators,
    activeIndicators,
    indicatorConfigs,
    calculatedIndicators,
    addIndicator,
    removeIndicator,
    updateIndicatorConfig,
    getIndicatorLabel,
    getIndicatorConfigComponent,
    calculateIndicator
  }
}