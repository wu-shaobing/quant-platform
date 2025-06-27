/**
 * 数据流组合函数
 * 处理实时数据流订阅和管理
 */
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { getWebSocketService } from '@/services/websocket.service'
import type { Ref } from 'vue'

export interface DataStreamOptions {
  autoConnect?: boolean
  reconnectOnError?: boolean
  bufferSize?: number
  throttleMs?: number
}

export interface StreamData<T = any> {
  data: T
  timestamp: number
  sequence: number
}

export function useDataStream<T = any>(
  streamType: string,
  options: DataStreamOptions = {}
) {
  const {
    autoConnect = true,
    reconnectOnError = true,
    bufferSize = 1000,
    throttleMs = 0
  } = options

  // 状态
  const connected = ref(false)
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const lastUpdate = ref<number>(0)
  
  // 数据
  const currentData = ref<T | null>(null)
  const dataBuffer = ref<StreamData<T>[]>([])
  const sequence = ref(0)

  // WebSocket 服务
  const wsService = getWebSocketService()
  
  // 节流控制
  let lastEmitTime = 0
  let throttleTimer: NodeJS.Timeout | null = null

  // 计算属性
  const isConnected = computed(() => connected.value && wsService.isConnected())
  const hasData = computed(() => currentData.value !== null)
  const bufferLength = computed(() => dataBuffer.value.length)

  /**
   * 连接数据流
   */
  const connect = async (): Promise<void> => {
    if (loading.value) return

    loading.value = true
    error.value = null

    try {
      if (!wsService.isConnected()) {
        await wsService.connect()
      }

      // 监听连接状态
      wsService.on('connect', handleConnect)
      wsService.on('disconnect', handleDisconnect)
      wsService.on('error', handleError)

      // 监听数据流
      wsService.on(streamType as any, handleDataReceived)

      // 订阅数据流
      wsService.emit('subscribe', { type: streamType })

      connected.value = true
    } catch (err) {
      error.value = err as Error
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 断开数据流
   */
  const disconnect = (): void => {
    if (!connected.value) return

    // 取消订阅
    wsService.emit('unsubscribe', { type: streamType })

    // 移除事件监听
    wsService.off('connect', handleConnect)
    wsService.off('disconnect', handleDisconnect)
    wsService.off('error', handleError)
    wsService.off(streamType as any, handleDataReceived)

    connected.value = false
    clearThrottleTimer()
  }

  /**
   * 发送消息到数据流
   */
  const send = (message: any): void => {
    if (!isConnected.value) {
      throw new Error('Data stream not connected')
    }

    wsService.emit(streamType, message)
  }

  /**
   * 清空数据缓冲区
   */
  const clearBuffer = (): void => {
    dataBuffer.value = []
  }

  /**
   * 获取历史数据
   */
  const getHistoryData = (count?: number): StreamData<T>[] => {
    if (count) {
      return dataBuffer.value.slice(-count)
    }
    return [...dataBuffer.value]
  }

  /**
   * 重置状态
   */
  const reset = (): void => {
    currentData.value = null
    dataBuffer.value = []
    sequence.value = 0
    lastUpdate.value = 0
    error.value = null
  }

  // 事件处理器

  const handleConnect = (): void => {
    connected.value = true
    error.value = null
  }

  const handleDisconnect = (): void => {
    connected.value = false
    if (reconnectOnError && !error.value) {
      // 自动重连
      setTimeout(() => {
        if (!connected.value) {
          connect().catch(console.error)
        }
      }, 3000)
    }
  }

  const handleError = (err: Error): void => {
    error.value = err
    if (reconnectOnError) {
      setTimeout(() => {
        connect().catch(console.error)
      }, 5000)
    }
  }

  const handleDataReceived = (data: T): void => {
    const now = Date.now()

    // 节流处理
    if (throttleMs > 0) {
      const timeSinceLastEmit = now - lastEmitTime
      if (timeSinceLastEmit < throttleMs) {
        // 设置延迟处理
        clearThrottleTimer()
        throttleTimer = setTimeout(() => {
          processData(data, now)
        }, throttleMs - timeSinceLastEmit)
        return
      }
    }

    processData(data, now)
  }

  const processData = (data: T, timestamp: number): void => {
    sequence.value++
    lastUpdate.value = timestamp
    lastEmitTime = timestamp

    // 更新当前数据
    currentData.value = data

    // 添加到缓冲区
    const streamData: StreamData<T> = {
      data,
      timestamp,
      sequence: sequence.value
    }

    dataBuffer.value.push(streamData)

    // 限制缓冲区大小
    if (dataBuffer.value.length > bufferSize) {
      dataBuffer.value.shift()
    }
  }

  const clearThrottleTimer = (): void => {
    if (throttleTimer) {
      clearTimeout(throttleTimer)
      throttleTimer = null
    }
  }

  // 生命周期
  onMounted(() => {
    if (autoConnect) {
      connect().catch(console.error)
    }
  })

  onUnmounted(() => {
    disconnect()
    clearThrottleTimer()
  })

  return {
    // 状态
    connected: isConnected,
    loading,
    error,
    lastUpdate,
    hasData,
    bufferLength,

    // 数据
    currentData: currentData as Ref<T | null>,
    dataBuffer: dataBuffer as Ref<StreamData<T>[]>,

    // 方法
    connect,
    disconnect,
    send,
    clearBuffer,
    getHistoryData,
    reset
  }
}

/**
 * 行情数据流
 */
export function useMarketDataStream(symbols: string[] = []) {
  const stream = useDataStream('market-data', {
    autoConnect: true,
    throttleMs: 100 // 100ms 节流
  })

  const subscribeSymbols = (newSymbols: string[]): void => {
    if (stream.connected.value) {
      stream.send({ action: 'subscribe', symbols: newSymbols })
    }
  }

  const unsubscribeSymbols = (symbolsToRemove: string[]): void => {
    if (stream.connected.value) {
      stream.send({ action: 'unsubscribe', symbols: symbolsToRemove })
    }
  }

  // 自动订阅初始股票
  onMounted(() => {
    if (symbols.length > 0) {
      const unwatch = watch(stream.connected, (connected) => {
        if (connected) {
          subscribeSymbols(symbols)
          unwatch()
        }
      }, { immediate: true })
    }
  })

  return {
    ...stream,
    subscribeSymbols,
    unsubscribeSymbols
  }
}

/**
 * 交易数据流
 */
export function useTradingDataStream() {
  return useDataStream('trading-update', {
    autoConnect: true,
    bufferSize: 500
  })
}

/**
 * 通知数据流
 */
export function useNotificationStream() {
  const stream = useDataStream('notification', {
    autoConnect: true,
    bufferSize: 100
  })

  const markAsRead = (notificationId: string): void => {
    if (stream.connected.value) {
      stream.send({ action: 'mark-read', id: notificationId })
    }
  }

  const markAllAsRead = (): void => {
    if (stream.connected.value) {
      stream.send({ action: 'mark-all-read' })
    }
  }

  return {
    ...stream,
    markAsRead,
    markAllAsRead
  }
}