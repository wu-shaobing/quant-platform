import { ref, computed } from 'vue'
import { marketApi } from '@/api'
import { useWebSocket } from '@/composables/useWebSocket'
import type { KLineData, TimePeriod } from '@/types/chart'

export const useKLineData = () => {
  const klineData = ref<KLineData[]>([])
  const selectedPeriod = ref<string>('1m')
  const loading = ref(false)

  // 时间周期配置
  const timePeriods: TimePeriod[] = [
    { value: '1m', label: '1分钟' },
    { value: '5m', label: '5分钟' },
    { value: '15m', label: '15分钟' },
    { value: '30m', label: '30分钟' },
    { value: '1h', label: '1小时' },
    { value: '4h', label: '4小时' },
    { value: '1d', label: '日线' },
    { value: '1w', label: '周线' },
    { value: '1M', label: '月线' }
  ]

  const currentPeriodLabel = computed(() => {
    const period = timePeriods.find(p => p.value === selectedPeriod.value)
    return period?.label || '1分钟'
  })

  // WebSocket连接
  const { connect, disconnect, on, emit } = useWebSocket()

  // 获取K线数据
  const fetchKLineData = async (symbol: string, period: string, limit = 1000) => {
    loading.value = true
    
    try {
      const data = await marketApi.getKLineData({
        symbol,
        period,
        limit
      })
      
      klineData.value = data.map(item => ({
        timestamp: item.timestamp,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume
      }))
      
      selectedPeriod.value = period
      
      return data
    } catch (error) {
      console.error('获取K线数据失败:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 订阅实时K线数据
  const subscribeRealtime = (symbol: string) => {
    connect()
    
    emit('subscribe', {
      type: 'kline',
      symbol,
      period: selectedPeriod.value
    })
    
    on('kline_update', (data: any) => {
      if (data.symbol === symbol) {
        updateKLineData(data)
      }
    })
  }

  // 取消订阅
  const unsubscribeRealtime = (symbol: string) => {
    emit('unsubscribe', {
      type: 'kline',
      symbol,
      period: selectedPeriod.value
    })
  }

  // 更新K线数据
  const updateKLineData = (newData: any) => {
    if (klineData.value.length === 0) return
    
    const lastIndex = klineData.value.length - 1
    const lastKLine = klineData.value[lastIndex]
    
    // 如果是同一时间的数据，更新最后一根K线
    if (lastKLine.timestamp === newData.timestamp) {
      klineData.value[lastIndex] = {
        ...lastKLine,
        high: Math.max(lastKLine.high, newData.price),
        low: Math.min(lastKLine.low, newData.price),
        close: newData.price,
        volume: newData.volume
      }
    } else {
      // 新的时间周期，添加新的K线
      klineData.value.push({
        timestamp: newData.timestamp,
        open: newData.price,
        high: newData.price,
        low: newData.price,
        close: newData.price,
        volume: newData.volume
      })
      
      // 保持数据量不超过限制
      if (klineData.value.length > 1000) {
        klineData.value.shift()
      }
    }
  }

  return {
    klineData,
    selectedPeriod,
    timePeriods,
    currentPeriodLabel,
    loading,
    fetchKLineData,
    subscribeRealtime,
    unsubscribeRealtime,
    updateKLineData
  }
}