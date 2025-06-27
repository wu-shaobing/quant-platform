import { ref, onUnmounted } from 'vue'

interface WorkerMessage {
  id: string
  type: string
  data?: any
  error?: string
}

interface WorkerTask {
  id: string
  resolve: (value: any) => void
  reject: (error: Error) => void
  timeout?: NodeJS.Timeout
}

export const useWorker = (workerUrl: string, options: { timeout?: number } = {}) => {
  const worker = ref<Worker | null>(null)
  const isReady = ref(false)
  const error = ref<string | null>(null)
  const tasks = new Map<string, WorkerTask>()
  
  const { timeout = 30000 } = options

  // 初始化Worker
  const initWorker = () => {
    try {
      worker.value = new Worker(new URL(workerUrl, import.meta.url), {
        type: 'module'
      })
      
      worker.value.onmessage = handleMessage
      worker.value.onerror = handleError
      worker.value.onmessageerror = handleMessageError
      
      isReady.value = true
      error.value = null
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to initialize worker'
      console.error('Worker initialization failed:', err)
    }
  }

  // 处理Worker消息
  const handleMessage = (event: MessageEvent<WorkerMessage>) => {
    const { id, type, data, error: workerError } = event.data
    const task = tasks.get(id)
    
    if (!task) {
      console.warn('Received message for unknown task:', id)
      return
    }
    
    // 清除超时定时器
    if (task.timeout) {
      clearTimeout(task.timeout)
    }
    
    // 移除任务
    tasks.delete(id)
    
    if (type === 'error' || workerError) {
      task.reject(new Error(workerError || 'Worker task failed'))
    } else {
      task.resolve(data)
    }
  }

  // 处理Worker错误
  const handleError = (event: ErrorEvent) => {
    error.value = event.message
    console.error('Worker error:', event)
    
    // 拒绝所有待处理的任务
    tasks.forEach(task => {
      if (task.timeout) {
        clearTimeout(task.timeout)
      }
      task.reject(new Error('Worker error: ' + event.message))
    })
    tasks.clear()
  }

  // 处理消息错误
  const handleMessageError = (event: MessageEvent) => {
    error.value = 'Message error'
    console.error('Worker message error:', event)
  }

  // 发送任务到Worker
  const postTask = <T = any>(type: string, data?: any): Promise<T> => {
    return new Promise((resolve, reject) => {
      if (!worker.value || !isReady.value) {
        reject(new Error('Worker is not ready'))
        return
      }

      const id = generateTaskId()
      const task: WorkerTask = { id, resolve, reject }
      
      // 设置超时
      if (timeout > 0) {
        task.timeout = setTimeout(() => {
          tasks.delete(id)
          reject(new Error('Worker task timeout'))
        }, timeout)
      }
      
      tasks.set(id, task)
      
      // 发送消息
      worker.value.postMessage({ id, type, data })
    })
  }

  // 生成任务ID
  const generateTaskId = () => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  // 终止Worker
  const terminate = () => {
    if (worker.value) {
      worker.value.terminate()
      worker.value = null
      isReady.value = false
    }
    
    // 拒绝所有待处理的任务
    tasks.forEach(task => {
      if (task.timeout) {
        clearTimeout(task.timeout)
      }
      task.reject(new Error('Worker terminated'))
    })
    tasks.clear()
  }

  // 重启Worker
  const restart = () => {
    terminate()
    setTimeout(initWorker, 100)
  }

  // 获取Worker状态
  const getStatus = () => {
    return {
      isReady: isReady.value,
      error: error.value,
      pendingTasks: tasks.size,
      workerExists: !!worker.value
    }
  }

  // 初始化
  initWorker()

  // 清理
  onUnmounted(() => {
    terminate()
  })

  return {
    isReady,
    error,
    postTask,
    terminate,
    restart,
    getStatus
  }
}

// 技术指标计算专用Worker Hook
export const useIndicatorWorker = () => {
  const { postTask, ...workerMethods } = useWorker('/src/workers/indicator.worker.ts')

  // 计算移动平均线
  const calculateMA = (prices: number[], period: number) => {
    return postTask<number[]>('MA', { prices, period })
  }

  // 计算指数移动平均线
  const calculateEMA = (prices: number[], period: number) => {
    return postTask<number[]>('EMA', { prices, period })
  }

  // 计算MACD
  const calculateMACD = (prices: number[], fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) => {
    return postTask<{ dif: number[]; dea: number[]; macd: number[] }>('MACD', {
      prices,
      fastPeriod,
      slowPeriod,
      signalPeriod
    })
  }

  // 计算RSI
  const calculateRSI = (prices: number[], period = 14) => {
    return postTask<number[]>('RSI', { prices, period })
  }

  // 计算KDJ
  const calculateKDJ = (klineData: any[], kPeriod = 9, dPeriod = 3, jPeriod = 3) => {
    return postTask<{ k: number[]; d: number[]; j: number[] }>('KDJ', {
      klineData,
      kPeriod,
      dPeriod,
      jPeriod
    })
  }

  // 计算布林带
  const calculateBOLL = (prices: number[], period = 20, multiplier = 2) => {
    return postTask<{ upper: number[]; middle: number[]; lower: number[] }>('BOLL', {
      prices,
      period,
      multiplier
    })
  }

  // 计算CCI
  const calculateCCI = (klineData: any[], period = 14) => {
    return postTask<number[]>('CCI', { klineData, period })
  }

  // 计算威廉指标
  const calculateWR = (klineData: any[], period = 14) => {
    return postTask<number[]>('WR', { klineData, period })
  }

  // 计算OBV
  const calculateOBV = (klineData: any[]) => {
    return postTask<number[]>('OBV', { klineData })
  }

  // 计算BIAS
  const calculateBIAS = (prices: number[], periods = [6, 12, 24]) => {
    return postTask<{ [key: string]: number[] }>('BIAS', { prices, periods })
  }

  // 批量计算多个指标
  const calculateMultipleIndicators = async (
    klineData: any[],
    indicators: Array<{
      type: string
      params: any
    }>
  ) => {
    const results = await Promise.all(
      indicators.map(({ type, params }) => {
        switch (type) {
          case 'MA':
            return calculateMA(params.prices, params.period)
          case 'EMA':
            return calculateEMA(params.prices, params.period)
          case 'MACD':
            return calculateMACD(params.prices, params.fastPeriod, params.slowPeriod, params.signalPeriod)
          case 'RSI':
            return calculateRSI(params.prices, params.period)
          case 'KDJ':
            return calculateKDJ(klineData, params.kPeriod, params.dPeriod, params.jPeriod)
          case 'BOLL':
            return calculateBOLL(params.prices, params.period, params.multiplier)
          case 'CCI':
            return calculateCCI(klineData, params.period)
          case 'WR':
            return calculateWR(klineData, params.period)
          case 'OBV':
            return calculateOBV(klineData)
          case 'BIAS':
            return calculateBIAS(params.prices, params.periods)
          default:
            throw new Error(`Unknown indicator type: ${type}`)
        }
      })
    )

    return indicators.reduce((acc, { type }, index) => {
      acc[type] = results[index]
      return acc
    }, {} as Record<string, any>)
  }

  return {
    ...workerMethods,
    calculateMA,
    calculateEMA,
    calculateMACD,
    calculateRSI,
    calculateKDJ,
    calculateBOLL,
    calculateCCI,
    calculateWR,
    calculateOBV,
    calculateBIAS,
    calculateMultipleIndicators
  }
}