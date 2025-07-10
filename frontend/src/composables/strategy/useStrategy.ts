// src/composables/strategy/useStrategy.ts
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { strategyApi } from '@/api'
import type { Strategy, StrategyStatus, StrategyPerformance } from '@/types/strategy'

/**
 * useStrategy 组合式函数
 * 提供策略管理、开发、监控等功能
 */
export const useStrategy = () => {
  const loading = ref(false)
  const strategies = ref<Strategy[]>([])
  const currentStrategy = ref<Strategy | null>(null)
  const selectedStatus = ref<'all' | StrategyStatus>('all')

  /**
   * 获取策略列表
   */
  const fetchStrategies = async () => {
    try {
      loading.value = true
      const data = await strategyApi.getStrategies()
      strategies.value = Array.isArray(data) ? data : []
    } catch (error) {
      console.error('获取策略列表失败:', error)
      ElMessage.error('获取策略列表失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 创建新策略
   */
  const createStrategy = async (strategyData: Partial<Strategy>) => {
    try {
      const newStrategy = await strategyApi.createStrategy(strategyData)
      strategies.value.unshift(newStrategy)
      ElMessage.success('策略创建成功')
      return newStrategy
    } catch (error) {
      console.error('创建策略失败:', error)
      ElMessage.error('创建策略失败')
      throw error
    }
  }

  /**
   * 更新策略
   */
  const updateStrategy = async (id: string, strategyData: Partial<Strategy>) => {
    try {
      const updatedStrategy = await strategyApi.updateStrategy(id, strategyData)
      const index = strategies.value.findIndex(s => s.id === id)
      if (index > -1) {
        strategies.value[index] = updatedStrategy
      }
      ElMessage.success('策略更新成功')
      return updatedStrategy
    } catch (error) {
      console.error('更新策略失败:', error)
      ElMessage.error('更新策略失败')
      throw error
    }
  }

  /**
   * 删除策略
   */
  const deleteStrategy = async (id: string) => {
    try {
      await ElMessageBox.confirm(
        '确定要删除这个策略吗？此操作不可恢复。',
        '删除策略',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )

      await strategyApi.deleteStrategy(id)
      strategies.value = strategies.value.filter(s => s.id !== id)
      ElMessage.success('策略删除成功')
    } catch (error) {
      if (error !== 'cancel') {
        console.error('删除策略失败:', error)
        ElMessage.error('删除策略失败')
      }
    }
  }

  /**
   * 启动策略
   */
  const startStrategy = async (id: string) => {
    try {
      await strategyApi.startStrategy(id)
      const strategy = strategies.value.find(s => s.id === id)
      if (strategy) {
        strategy.status = 'running'
        strategy.startedAt = new Date().toISOString()
      }
      ElMessage.success('策略启动成功')
    } catch (error) {
      console.error('启动策略失败:', error)
      ElMessage.error('启动策略失败')
    }
  }

  /**
   * 停止策略
   */
  const stopStrategy = async (id: string) => {
    try {
      await ElMessageBox.confirm(
        '确定要停止这个策略吗？',
        '停止策略',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )

      await strategyApi.stopStrategy(id)
      const strategy = strategies.value.find(s => s.id === id)
      if (strategy) {
        strategy.status = 'stopped'
        strategy.stoppedAt = new Date().toISOString()
      }
      ElMessage.success('策略停止成功')
    } catch (error) {
      if (error !== 'cancel') {
        console.error('停止策略失败:', error)
        ElMessage.error('停止策略失败')
      }
    }
  }

  /**
   * 暂停策略
   */
  const pauseStrategy = async (id: string) => {
    try {
      await strategyApi.pauseStrategy(id)
      const strategy = strategies.value.find(s => s.id === id)
      if (strategy) {
        strategy.status = 'paused'
      }
      ElMessage.success('策略暂停成功')
    } catch (error) {
      console.error('暂停策略失败:', error)
      ElMessage.error('暂停策略失败')
    }
  }

  /**
   * 恢复策略
   */
  const resumeStrategy = async (id: string) => {
    try {
      await strategyApi.resumeStrategy(id)
      const strategy = strategies.value.find(s => s.id === id)
      if (strategy) {
        strategy.status = 'running'
      }
      ElMessage.success('策略恢复成功')
    } catch (error) {
      console.error('恢复策略失败:', error)
      ElMessage.error('恢复策略失败')
    }
  }

  /**
   * 获取策略详情
   */
  const getStrategyDetail = async (id: string) => {
    try {
      const strategy = await strategyApi.getStrategy(id)
      currentStrategy.value = strategy
      return strategy
    } catch (error) {
      console.error('获取策略详情失败:', error)
      ElMessage.error('获取策略详情失败')
      throw error
    }
  }

  /**
   * 获取策略性能数据
   */
  const getStrategyPerformance = async (id: string): Promise<StrategyPerformance> => {
    try {
      return await strategyApi.getStrategyPerformance(id)
    } catch (error) {
      console.error('获取策略性能失败:', error)
      ElMessage.error('获取策略性能失败')
      throw error
    }
  }

  /**
   * 克隆策略
   */
  const cloneStrategy = async (id: string) => {
    try {
      const originalStrategy = strategies.value.find(s => s.id === id)
      if (!originalStrategy) {
        throw new Error('策略不存在')
      }

      const clonedStrategy = await strategyApi.cloneStrategy(id)
      strategies.value.unshift(clonedStrategy)
      ElMessage.success('策略克隆成功')
      return clonedStrategy
    } catch (error) {
      console.error('克隆策略失败:', error)
      ElMessage.error('克隆策略失败')
      throw error
    }
  }

  /**
   * 过滤后的策略列表
   */
  const filteredStrategies = computed(() => {
    if (selectedStatus.value === 'all') return strategies.value
    return strategies.value.filter(s => s.status === selectedStatus.value)
  })

  /**
   * 运行中的策略数量
   */
  const runningStrategiesCount = computed(() => {
    return strategies.value.filter(s => s.status === 'running').length
  })

  /**
   * 盈利策略数量
   */
  const profitableStrategiesCount = computed(() => {
    return strategies.value.filter(s => s.totalReturn > 0).length
  })

  /**
   * 总收益
   */
  const totalReturn = computed(() => {
    return strategies.value.reduce((sum, s) => sum + (s.totalReturn || 0), 0)
  })

  /**
   * 策略状态选项
   */
  const statusOptions = [
    { value: 'all', label: '全部', color: '' },
    { value: 'draft', label: '草稿', color: 'info' },
    { value: 'testing', label: '测试中', color: 'warning' },
    { value: 'running', label: '运行中', color: 'success' },
    { value: 'paused', label: '已暂停', color: 'warning' },
    { value: 'stopped', label: '已停止', color: 'danger' },
    { value: 'error', label: '错误', color: 'danger' }
  ] as const

  return {
    loading,
    strategies,
    currentStrategy,
    selectedStatus,
    filteredStrategies,
    runningStrategiesCount,
    profitableStrategiesCount,
    totalReturn,
    statusOptions,
    fetchStrategies,
    createStrategy,
    updateStrategy,
    deleteStrategy,
    startStrategy,
    stopStrategy,
    pauseStrategy,
    resumeStrategy,
    getStrategyDetail,
    getStrategyPerformance,
    cloneStrategy
  }
}