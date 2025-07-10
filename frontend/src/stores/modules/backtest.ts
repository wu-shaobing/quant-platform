import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { backtestApi } from '@/api'
import { ElMessage } from 'element-plus'
import type { 
  Backtest,
  BacktestConfig,
  BacktestResult,
  BacktestCreateData,
  BacktestStatus,
  BacktestProgress,
  BacktestPerformance,
  BacktestStatistics
} from '@/types/backtest'

export const useBacktestStore = defineStore('backtest', () => {
  // ============ 状态定义 ============
  
  // 回测列表
  const backtests = ref<Backtest[]>([])
  
  // 回测结果详情
  const backtestResults = ref<Map<string, BacktestResult>>(new Map())
  
  // 当前选中的回测
  const selectedBacktest = ref<Backtest | null>(null)
  
  // 当前回测结果
  const currentResult = ref<BacktestResult | null>(null)
  
  // 回测进度
  const backtestProgress = ref<Map<string, BacktestProgress>>(new Map())
  
  // 加载状态
  const loading = ref({
    list: false,
    create: false,
    result: false,
    delete: false,
    cancel: false
  })
  
  // 错误状态
  const errors = ref({
    list: null as string | null,
    create: null as string | null,
    result: null as string | null,
    delete: null as string | null,
    cancel: null as string | null
  })

  // ============ 计算属性 ============

  // 按状态分组的回测
  const backtestsByStatus = computed(() => {
    const groups: Record<BacktestStatus, Backtest[]> = {
      pending: [],
      running: [],
      completed: [],
      failed: [],
      cancelled: []
    }
    
    backtests.value.forEach(backtest => {
      groups[backtest.status].push(backtest)
    })
    
    return groups
  })

  // 运行中的回测数量
  const runningBacktestsCount = computed(() => {
    return backtests.value.filter(b => b.status === 'running').length
  })

  // 已完成的回测数量
  const completedBacktestsCount = computed(() => {
    return backtests.value.filter(b => b.status === 'completed').length
  })

  // 最近的回测结果
  const recentBacktests = computed(() => {
    return backtests.value
      .filter(b => b.status === 'completed')
      .sort((a, b) => new Date(b.completedAt || 0).getTime() - new Date(a.completedAt || 0).getTime())
      .slice(0, 10)
  })

  // 最佳回测表现
  const bestPerformance = computed(() => {
    const completedResults = Array.from(backtestResults.value.values())
      .filter(result => result.status === 'completed')
    
    if (completedResults.length === 0) return null
    
    return completedResults.reduce((best, current) => {
      const bestReturn = best.performance.totalReturn
      const currentReturn = current.performance.totalReturn
      return currentReturn > bestReturn ? current : best
    })
  })

  // ============ 回测管理方法 ============

  // 获取回测列表
  const fetchBacktests = async (params?: {
    page?: number
    pageSize?: number
    status?: BacktestStatus
    strategyId?: string
    keyword?: string
  }) => {
    loading.value.list = true
    errors.value.list = null
    
    try {
      const data = await backtestApi.getBacktests(params)
      backtests.value = data.items || data
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取回测列表失败'
      errors.value.list = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.list = false
    }
  }

  // 创建回测
  const createBacktest = async (config: BacktestCreateData) => {
    loading.value.create = true
    errors.value.create = null
    
    try {
      const backtest = await backtestApi.createBacktest(config)
      backtests.value.unshift(backtest)
      ElMessage.success('回测创建成功')
      return backtest
    } catch (error) {
      const message = error instanceof Error ? error.message : '创建回测失败'
      errors.value.create = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.create = false
    }
  }

  // 运行回测
  const runBacktest = async (id: string) => {
    try {
      const backtest = await backtestApi.runBacktest(id)
      const index = backtests.value.findIndex(b => b.id === id)
      if (index !== -1) {
        backtests.value[index] = backtest
      }
      ElMessage.success('回测启动成功')
      return backtest
    } catch (error) {
      const message = error instanceof Error ? error.message : '启动回测失败'
      ElMessage.error(message)
      throw error
    }
  }

  // 取消回测
  const cancelBacktest = async (id: string) => {
    loading.value.cancel = true
    errors.value.cancel = null
    
    try {
      await backtestApi.cancelBacktest(id)
      const backtest = backtests.value.find(b => b.id === id)
      if (backtest) {
        backtest.status = 'cancelled'
      }
      ElMessage.success('回测已取消')
    } catch (error) {
      const message = error instanceof Error ? error.message : '取消回测失败'
      errors.value.cancel = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.cancel = false
    }
  }

  // 删除回测
  const deleteBacktest = async (id: string) => {
    loading.value.delete = true
    errors.value.delete = null
    
    try {
      await backtestApi.deleteBacktest(id)
      backtests.value = backtests.value.filter(b => b.id !== id)
      backtestResults.value.delete(id)
      backtestProgress.value.delete(id)
      
      if (selectedBacktest.value?.id === id) {
        selectedBacktest.value = null
      }
      if (currentResult.value?.backtestId === id) {
        currentResult.value = null
      }
      
      ElMessage.success('回测删除成功')
    } catch (error) {
      const message = error instanceof Error ? error.message : '删除回测失败'
      errors.value.delete = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.delete = false
    }
  }

  // ============ 结果管理方法 ============

  // 获取回测结果
  const fetchBacktestResult = async (id: string) => {
    loading.value.result = true
    errors.value.result = null
    
    try {
      const result = await backtestApi.getBacktestResult(id)
      backtestResults.value.set(id, result)
      currentResult.value = result
      return result
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取回测结果失败'
      errors.value.result = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.result = false
    }
  }

  // 获取回测详情
  const fetchBacktestDetail = async (id: string) => {
    try {
      const backtest = await backtestApi.getBacktestById(id)
      selectedBacktest.value = backtest
      
      // 如果有结果，也获取结果详情
      if (backtest.status === 'completed' && backtest.result) {
        await fetchBacktestResult(id)
      }
      
      return backtest
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取回测详情失败'
      ElMessage.error(message)
      throw error
    }
  }

  // 获取回测进度
  const fetchBacktestProgress = async (id: string) => {
    try {
      const progress = await backtestApi.getBacktestProgress(id)
      backtestProgress.value.set(id, progress)
      return progress
    } catch (error) {
      console.error('获取回测进度失败:', error)
      throw error
    }
  }

  // ============ 分析方法 ============

  // 比较回测结果
  const compareBacktests = (backtestIds: string[]) => {
    const results = backtestIds
      .map(id => backtestResults.value.get(id))
      .filter(result => result && result.status === 'completed') as BacktestResult[]
    
    if (results.length < 2) {
      throw new Error('至少需要两个已完成的回测结果进行比较')
    }
    
    return {
      results,
      comparison: {
        totalReturns: results.map(r => r.performance.totalReturn),
        sharpeRatios: results.map(r => r.performance.sharpeRatio),
        maxDrawdowns: results.map(r => r.performance.maxDrawdown),
        winRates: results.map(r => r.statistics.winRate)
      }
    }
  }

  // 计算回测排名
  const rankBacktests = (metric: keyof BacktestPerformance = 'totalReturn') => {
    const completedResults = Array.from(backtestResults.value.values())
      .filter(result => result.status === 'completed')
    
    return completedResults
      .sort((a, b) => (b.performance[metric] as number) - (a.performance[metric] as number))
      .map((result, index) => ({
        rank: index + 1,
        backtestId: result.backtestId,
        value: result.performance[metric],
        backtest: backtests.value.find(b => b.id === result.backtestId)
      }))
  }

  // ============ 工具方法 ============

  // 设置选中的回测
  const setSelectedBacktest = (backtest: Backtest | null) => {
    selectedBacktest.value = backtest
  }

  // 设置当前结果
  const setCurrentResult = (result: BacktestResult | null) => {
    currentResult.value = result
  }

  // 更新回测状态
  const updateBacktestStatus = (id: string, status: BacktestStatus, progress?: number) => {
    const backtest = backtests.value.find(b => b.id === id)
    if (backtest) {
      backtest.status = status
      if (progress !== undefined) {
        backtest.progress = progress
      }
    }
  }

  // 清除错误
  const clearErrors = () => {
    Object.keys(errors.value).forEach(key => {
      errors.value[key as keyof typeof errors.value] = null
    })
  }

  // 重置状态
  const reset = () => {
    backtests.value = []
    backtestResults.value.clear()
    backtestProgress.value.clear()
    selectedBacktest.value = null
    currentResult.value = null
    clearErrors()
  }

  return {
    // 状态
    backtests,
    backtestResults,
    selectedBacktest,
    currentResult,
    backtestProgress,
    loading,
    errors,
    
    // 计算属性
    backtestsByStatus,
    runningBacktestsCount,
    completedBacktestsCount,
    recentBacktests,
    bestPerformance,
    
    // 方法
    fetchBacktests,
    createBacktest,
    runBacktest,
    cancelBacktest,
    deleteBacktest,
    fetchBacktestResult,
    fetchBacktestDetail,
    fetchBacktestProgress,
    compareBacktests,
    rankBacktests,
    setSelectedBacktest,
    setCurrentResult,
    updateBacktestStatus,
    clearErrors,
    reset
  }
}) 