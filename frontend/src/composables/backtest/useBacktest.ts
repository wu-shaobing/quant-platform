// src/composables/backtest/useBacktest.ts
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { 
  BacktestTask, 
  BacktestFormData, 
  BacktestResult,
  BacktestStatus 
} from '@/types/backtest'

export const useBacktest = () => {
  // 状态
  const loading = ref(false)
  const tasks = ref<BacktestTask[]>([])
  const currentTask = ref<BacktestTask | null>(null)
  
  // 计算属性
  const runningTasks = computed(() => 
    tasks.value.filter(task => task.status === 'running')
  )
  
  const completedTasks = computed(() => 
    tasks.value.filter(task => task.status === 'completed')
  )
  
  const failedTasks = computed(() => 
    tasks.value.filter(task => task.status === 'failed')
  )
  
  // 创建回测任务
  const createBacktest = async (formData: BacktestFormData): Promise<string> => {
    try {
      loading.value = true
      
      // 构建任务数据
      const taskData = {
        name: formData.name,
        strategyId: formData.strategyId,
        config: {
          stockPool: formData.stockPool,
          startDate: formData.dateRange[0].toISOString().split('T')[0],
          endDate: formData.dateRange[1].toISOString().split('T')[0],
          frequency: formData.frequency,
          initialCapital: formData.initialCapital,
          commission: formData.commission,
          stampTax: formData.stampTax,
          slippage: 0.001, // 默认滑点
          maxDrawdown: formData.maxDrawdown,
          maxPositionRatio: formData.maxPositionRatio,
          riskControl: {
            maxLeverage: 1
          }
        }
      }
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 创建新任务
      const newTask: BacktestTask = {
        id: `bt_${Date.now()}`,
        name: formData.name,
        strategyId: formData.strategyId,
        strategyName: '测试策略', // 这里应该从策略列表获取
        status: 'pending',
        progress: 0,
        config: taskData.config,
        createTime: Date.now()
      }
      
      tasks.value.unshift(newTask)
      currentTask.value = newTask
      
      // 启动回测
      await startBacktest(newTask.id)
      
      ElMessage.success('回测任务创建成功')
      return newTask.id
      
    } catch (error) {
      console.error('创建回测失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '创建回测失败')
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 启动回测
  const startBacktest = async (taskId: string): Promise<void> => {
    const task = tasks.value.find(t => t.id === taskId)
    if (!task) {
      throw new Error('任务不存在')
    }
    
    try {
      // 更新任务状态
      task.status = 'running'
      task.startTime = Date.now()
      task.progress = 0
      
      // 模拟回测进度
      const progressInterval = setInterval(() => {
        if (task.progress < 100 && task.status === 'running') {
          task.progress += Math.random() * 10
          if (task.progress >= 100) {
            task.progress = 100
            task.status = 'completed'
            task.endTime = Date.now()
            
            // 生成模拟结果
            task.result = generateMockResult()
            
            clearInterval(progressInterval)
            ElMessage.success(`回测任务 "${task.name}" 完成`)
          }
        }
      }, 500)
      
    } catch (error) {
      task.status = 'failed'
      task.errorMessage = error instanceof Error ? error.message : '回测执行失败'
      throw error
    }
  }
  
  // 停止回测
  const stopBacktest = async (taskId: string): Promise<void> => {
    const task = tasks.value.find(t => t.id === taskId)
    if (!task) {
      throw new Error('任务不存在')
    }
    
    if (task.status !== 'running') {
      throw new Error('任务未在运行中')
    }
    
    try {
      task.status = 'cancelled'
      task.endTime = Date.now()
      
      ElMessage.success('回测任务已停止')
      
    } catch (error) {
      console.error('停止回测失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '停止回测失败')
      throw error
    }
  }
  
  // 删除回测任务
  const deleteBacktest = async (taskId: string): Promise<void> => {
    const taskIndex = tasks.value.findIndex(t => t.id === taskId)
    if (taskIndex === -1) {
      throw new Error('任务不存在')
    }
    
    const task = tasks.value[taskIndex]
    if (task.status === 'running') {
      throw new Error('无法删除正在运行的任务')
    }
    
    try {
      tasks.value.splice(taskIndex, 1)
      
      if (currentTask.value?.id === taskId) {
        currentTask.value = null
      }
      
      ElMessage.success('回测任务已删除')
      
    } catch (error) {
      console.error('删除回测失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '删除回测失败')
      throw error
    }
  }
  
  // 获取回测结果
  const getBacktestResult = async (taskId: string): Promise<BacktestResult | null> => {
    const task = tasks.value.find(t => t.id === taskId)
    if (!task || !task.result) {
      return null
    }
    
    return task.result
  }
  
  // 设置当前任务
  const setCurrentTask = (taskId: string | null): void => {
    if (taskId) {
      const task = tasks.value.find(t => t.id === taskId)
      currentTask.value = task || null
    } else {
      currentTask.value = null
    }
  }
  
  // 获取任务列表
  const fetchTasks = async (): Promise<void> => {
    try {
      loading.value = true
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 这里应该从API获取真实数据
      
    } catch (error) {
      console.error('获取任务列表失败:', error)
      ElMessage.error('获取任务列表失败')
    } finally {
      loading.value = false
    }
  }
  
  // 生成模拟回测结果
  const generateMockResult = (): BacktestResult => {
    const mockResult: BacktestResult = {
      summary: {
        totalReturn: 0.15 + Math.random() * 0.3, // 15%-45%的收益率
        annualizedReturn: 0.12 + Math.random() * 0.2,
        volatility: 0.15 + Math.random() * 0.1,
        sharpeRatio: 0.8 + Math.random() * 1.2,
        maxDrawdown: -(0.05 + Math.random() * 0.15),
        calmarRatio: 0.5 + Math.random() * 1.0,
        winRate: 0.45 + Math.random() * 0.3,
        totalTrades: Math.floor(50 + Math.random() * 200),
        avgHoldingDays: Math.floor(5 + Math.random() * 20),
        turnoverRate: 1 + Math.random() * 3,
        finalValue: 1000000 * (1.15 + Math.random() * 0.3)
      },
      performance: {
        totalReturn: 0.15 + Math.random() * 0.3,
        annualizedReturn: 0.12 + Math.random() * 0.2,
        excessReturn: 0.03 + Math.random() * 0.1,
        alpha: 0.02 + Math.random() * 0.05,
        beta: 0.8 + Math.random() * 0.4,
        informationRatio: 0.3 + Math.random() * 0.7,
        trackingError: 0.02 + Math.random() * 0.03,
        treynorRatio: 0.1 + Math.random() * 0.15,
        jensenAlpha: 0.01 + Math.random() * 0.03
      },
      riskMetrics: {
        volatility: 0.15 + Math.random() * 0.1,
        downSideDeviation: 0.1 + Math.random() * 0.08,
        maxDrawdown: -(0.05 + Math.random() * 0.15),
        maxDrawdownDuration: Math.floor(10 + Math.random() * 50),
        var95: -(0.02 + Math.random() * 0.03),
        var99: -(0.03 + Math.random() * 0.05),
        expectedShortfall: -(0.04 + Math.random() * 0.06),
        sharpeRatio: 0.8 + Math.random() * 1.2,
        sortinoRatio: 1.0 + Math.random() * 1.5,
        calmarRatio: 0.5 + Math.random() * 1.0,
        omegaRatio: 1.2 + Math.random() * 0.8
      },
      trades: [],
      positions: [],
      equity: [],
      drawdown: [],
      monthlyReturns: [],
      yearlyReturns: []
    }
    
    return mockResult
  }
  
  return {
    // 状态
    loading,
    tasks,
    currentTask,
    
    // 计算属性
    runningTasks,
    completedTasks,
    failedTasks,
    
    // 方法
    createBacktest,
    startBacktest,
    stopBacktest,
    deleteBacktest,
    getBacktestResult,
    setCurrentTask,
    fetchTasks
  }
}