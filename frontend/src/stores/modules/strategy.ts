import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { strategyApi } from '@/api'
import { ElMessage } from 'element-plus'
import type { 
  Strategy, 
  StrategyInstance,
  StrategySignal,
  BacktestConfig,
  BacktestResult,
  PerformanceReport,
  StrategyStatus,
  StrategyType
} from '@/types/strategy'

export const useStrategyStore = defineStore('strategy', () => {
  // ============ 状态定义 ============
  
  // 策略列表
  const strategies = ref<Strategy[]>([])
  
  // 策略实例列表（运行中的策略）
  const strategyInstances = ref<StrategyInstance[]>([])
  
  // 策略信号
  const signals = ref<StrategySignal[]>([])
  
  // 回测结果
  const backtestResults = ref<BacktestResult[]>([])
  
  // 当前选中的策略
  const selectedStrategy = ref<Strategy | null>(null)
  
  // 当前编辑的策略
  const editingStrategy = ref<Strategy | null>(null)
  
  // 加载状态
  const loading = ref({
    strategies: false,
    instances: false,
    signals: false,
    backtest: false,
    create: false,
    update: false,
    delete: false,
    run: false
  })
  
  // 错误状态
  const errors = ref({
    strategies: null as string | null,
    instances: null as string | null,
    signals: null as string | null,
    backtest: null as string | null,
    create: null as string | null,
    update: null as string | null,
    delete: null as string | null,
    run: null as string | null
  })

  // ============ 计算属性 ============

  // 按状态分组的策略
  const strategiesByStatus = computed(() => {
    const groups: Record<StrategyStatus, Strategy[]> = {
      editing: [],
      running: [],
      paused: [],
      stopped: [],
      error: [],
      archived: []
    }
    
    strategies.value.forEach(strategy => {
      groups[strategy.status].push(strategy)
    })
    
    return groups
  })

  // 按类型分组的策略
  const strategiesByType = computed(() => {
    const groups: Record<StrategyType, Strategy[]> = {
      trend_following: [],
      mean_reversion: [],
      momentum: [],
      arbitrage: [],
      grid: [],
      scalping: [],
      event_driven: [],
      custom: []
    }
    
    strategies.value.forEach(strategy => {
      groups[strategy.type].push(strategy)
    })
    
    return groups
  })

  // 运行中的策略数量
  const runningStrategiesCount = computed(() => {
    return strategyInstances.value.filter(instance => instance.status === 'running').length
  })

  // 今日信号数量
  const todaySignalsCount = computed(() => {
    const today = new Date().toDateString()
    return signals.value.filter(signal => 
      new Date(signal.timestamp).toDateString() === today
    ).length
  })

  // 总盈亏
  const totalPnL = computed(() => {
    return strategyInstances.value.reduce((total, instance) => total + instance.pnl, 0)
  })

  // ============ 策略管理方法 ============

  // 获取策略列表
  const fetchStrategies = async (params?: {
    page?: number
    pageSize?: number
    status?: string
    type?: string
    keyword?: string
  }) => {
    loading.value.strategies = true
    errors.value.strategies = null
    
    try {
      const data = await strategyApi.getStrategies(params)
      strategies.value = data.items || data
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取策略列表失败'
      errors.value.strategies = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.strategies = false
    }
  }

  // 获取推荐策略列表
  const getFeaturedStrategies = async () => {
    try {
      // 模拟推荐策略数据，实际项目中应该调用 API
      return [
        {
          id: '1',
          name: 'AI量化选股策略',
          author: '量化团队',
          description: '基于人工智能技术的量化选股策略，通过机器学习模型分析市场数据',
          riskLevel: 'medium',
          annualReturn: 0.25,
          maxDrawdown: -0.08,
          sharpeRatio: 1.85,
          viewCount: 1250,
          favoriteCount: 89,
          downloadCount: 156,
          rating: 4.5,
          isFavorited: false
        },
        {
          id: '2',
          name: '均值回归策略',
          author: '策略专家',
          description: '经典的均值回归策略，适合震荡市场环境',
          riskLevel: 'low',
          annualReturn: 0.15,
          maxDrawdown: -0.05,
          sharpeRatio: 1.2,
          viewCount: 980,
          favoriteCount: 67,
          downloadCount: 234,
          rating: 4.2,
          isFavorited: true
        }
      ]
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取推荐策略失败'
      ElMessage.error(message)
      throw error
    }
  }

  // 获取策略列表（兼容 StrategyHub 的调用方式）
  const getStrategies = async (params?: {
    page?: number
    pageSize?: number
    search?: string
    category?: string
    riskLevel?: string
    returnRange?: string
    sortBy?: string
  }) => {
    try {
      // 模拟策略列表数据，实际项目中应该调用 API
      const mockStrategies = [
        {
          id: '1',
          name: 'AI量化选股策略',
          author: '量化团队',
          description: '基于人工智能技术的量化选股策略',
          category: 'ai',
          riskLevel: 'medium',
          annualReturn: 0.25,
          maxDrawdown: -0.08,
          sharpeRatio: 1.85,
          viewCount: 1250,
          favoriteCount: 89,
          downloadCount: 156,
          rating: 4.5,
          isFavorited: false
        }
      ]

      return {
        items: mockStrategies,
        total: mockStrategies.length
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取策略列表失败'
      ElMessage.error(message)
      throw error
    }
  }

  // 获取策略详情
  const fetchStrategyById = async (id: string) => {
    try {
      const strategy = await strategyApi.getStrategyById(id)
      selectedStrategy.value = strategy
      return strategy
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取策略详情失败'
      ElMessage.error(message)
      throw error
    }
  }

  // 创建策略
  const createStrategy = async (strategyData: Partial<Strategy>) => {
    loading.value.create = true
    errors.value.create = null
    
    try {
      const newStrategy = await strategyApi.createStrategy(strategyData)
      strategies.value.unshift(newStrategy)
      ElMessage.success('策略创建成功')
      return newStrategy
    } catch (error) {
      const message = error instanceof Error ? error.message : '创建策略失败'
      errors.value.create = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.create = false
    }
  }

  // 更新策略
  const updateStrategy = async (id: string, strategyData: Partial<Strategy>) => {
    loading.value.update = true
    errors.value.update = null
    
    try {
      const updatedStrategy = await strategyApi.updateStrategy(id, strategyData)
      const index = strategies.value.findIndex(s => s.id === id)
      if (index !== -1) {
        strategies.value[index] = updatedStrategy
      }
      if (selectedStrategy.value?.id === id) {
        selectedStrategy.value = updatedStrategy
      }
      ElMessage.success('策略更新成功')
      return updatedStrategy
    } catch (error) {
      const message = error instanceof Error ? error.message : '更新策略失败'
      errors.value.update = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.update = false
    }
  }

  // 删除策略
  const deleteStrategy = async (id: string) => {
    loading.value.delete = true
    errors.value.delete = null
    
    try {
      await strategyApi.deleteStrategy(id)
      strategies.value = strategies.value.filter(s => s.id !== id)
      if (selectedStrategy.value?.id === id) {
        selectedStrategy.value = null
      }
      ElMessage.success('策略删除成功')
    } catch (error) {
      const message = error instanceof Error ? error.message : '删除策略失败'
      errors.value.delete = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.delete = false
    }
  }

  // ============ 策略运行管理 ============

  // 启动策略
  const startStrategy = async (strategyId: string, config?: any) => {
    loading.value.run = true
    errors.value.run = null
    
    try {
      const instance = await strategyApi.startStrategy(strategyId, config)
      strategyInstances.value.push(instance)
      
      // 更新策略状态
      const strategy = strategies.value.find(s => s.id === strategyId)
      if (strategy) {
        strategy.status = 'running'
      }
      
      ElMessage.success('策略启动成功')
      return instance
    } catch (error) {
      const message = error instanceof Error ? error.message : '启动策略失败'
      errors.value.run = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.run = false
    }
  }

  // 停止策略
  const stopStrategy = async (instanceId: string) => {
    try {
      await strategyApi.stopStrategy(instanceId)
      
      const instance = strategyInstances.value.find(i => i.id === instanceId)
      if (instance) {
        instance.status = 'stopped'
        instance.stopTime = new Date().toISOString()
      }
      
      ElMessage.success('策略停止成功')
    } catch (error) {
      const message = error instanceof Error ? error.message : '停止策略失败'
      ElMessage.error(message)
      throw error
    }
  }

  // ============ 回测管理 ============

  // 运行回测
  const runBacktest = async (config: BacktestConfig) => {
    loading.value.backtest = true
    errors.value.backtest = null
    
    try {
      const result = await strategyApi.runBacktest(config)
      backtestResults.value.unshift(result)
      ElMessage.success('回测启动成功')
      return result
    } catch (error) {
      const message = error instanceof Error ? error.message : '启动回测失败'
      errors.value.backtest = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.backtest = false
    }
  }

  // 获取回测历史
  const fetchBacktestHistory = async (params?: any) => {
    loading.value.backtest = true
    
    try {
      const data = await strategyApi.getBacktestHistory(params)
      backtestResults.value = data.items || data
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取回测历史失败'
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.backtest = false
    }
  }

  // 获取回测结果详情
  const fetchBacktestResult = async (id: string) => {
    try {
      const result = await strategyApi.getBacktestResult(id)
      const index = backtestResults.value.findIndex(r => r.id === id)
      if (index !== -1) {
        backtestResults.value[index] = result
      }
      return result
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取回测结果失败'
      ElMessage.error(message)
      throw error
    }
  }

  // ============ 工具方法 ============

  // 设置选中的策略
  const setSelectedStrategy = (strategy: Strategy | null) => {
    selectedStrategy.value = strategy
  }

  // 设置编辑的策略
  const setEditingStrategy = (strategy: Strategy | null) => {
    editingStrategy.value = strategy
  }

  // 清除错误
  const clearErrors = () => {
    Object.keys(errors.value).forEach(key => {
      errors.value[key as keyof typeof errors.value] = null
    })
  }

  // 收藏策略
  const favoriteStrategy = async (strategyId: string) => {
    try {
      // 模拟收藏操作
      ElMessage.success('收藏成功')
    } catch (error) {
      const message = error instanceof Error ? error.message : '收藏失败'
      ElMessage.error(message)
      throw error
    }
  }

  // 取消收藏策略
  const unfavoriteStrategy = async (strategyId: string) => {
    try {
      // 模拟取消收藏操作
      ElMessage.success('取消收藏成功')
    } catch (error) {
      const message = error instanceof Error ? error.message : '取消收藏失败'
      ElMessage.error(message)
      throw error
    }
  }

  // 下载策略
  const downloadStrategy = async (strategyId: string) => {
    try {
      const strategy = strategies.value.find(s => s.id === strategyId)
      if (!strategy) {
        throw new Error('策略不存在')
      }
      
      ElMessage.success('策略下载成功')
      return strategy
    } catch (error) {
      const message = error instanceof Error ? error.message : '下载策略失败'
      ElMessage.error(message)
      throw error
    }
  }

  // 导入策略
  const importStrategy = async (strategyData: any) => {
    loading.value.create = true
    errors.value.create = null
    
    try {
      // 生成唯一ID
      const id = `imported_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      
      // 构建策略对象
      const strategy: Strategy = {
        id,
        name: strategyData.name,
        description: strategyData.description,
        author: strategyData.author || 'Unknown',
        version: strategyData.version || '1.0.0',
        type: strategyData.category === 'custom' ? 'custom' : 'trend_following',
        status: 'editing',
        riskLevel: strategyData.riskLevel || 'medium',
        tags: strategyData.tags || [],
        sourceCode: strategyData.sourceCode,
        language: strategyData.language || 'python',
        entryPoint: strategyData.entryPoint,
        parameters: strategyData.parameters || [],
        config: {
          initialCapital: 100000,
          maxPositionSize: 0.1,
          stopLoss: 0.05,
          takeProfit: 0.15,
          maxHoldings: 10,
          rebalanceFrequency: 'daily',
          benchmark: 'CSI300',
          startDate: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
          endDate: new Date().toISOString()
        },
        performance: {
          totalReturn: 0,
          annualReturn: 0,
          sharpeRatio: 0,
          maxDrawdown: 0,
          winRate: 0,
          profitFactor: 0,
          totalTrades: 0,
          avgHoldingPeriod: 0,
          volatility: 0,
          beta: 0,
          alpha: 0,
          informationRatio: 0,
          calmarRatio: 0,
          sortinoRatio: 0
        },
        backtest: {
          lastRunTime: null,
          status: 'pending',
          progress: 0,
          results: []
        },
        createdAt: strategyData.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isPublic: false,
        isFavorited: false,
        viewCount: 0,
        downloadCount: 0,
        favoriteCount: 0,
        rating: 0,
        comments: []
      }

      // 添加到策略列表
      strategies.value.unshift(strategy)
      
      // 实际项目中应该调用API保存策略
      // await strategyApi.createStrategy(strategy)
      
      ElMessage.success(`策略 "${strategy.name}" 导入成功`)
      return strategy
      
    } catch (error) {
      const message = error instanceof Error ? error.message : '导入策略失败'
      errors.value.create = message
      ElMessage.error(message)
      throw error
    } finally {
      loading.value.create = false
    }
  }

  // 导出策略
  const exportStrategy = async (strategyId: string, format: 'json' | 'python' | 'javascript' = 'json') => {
    try {
      const strategy = strategies.value.find(s => s.id === strategyId)
      if (!strategy) {
        throw new Error('策略不存在')
      }

      let exportData: any
      let fileName: string
      let mimeType: string

      switch (format) {
        case 'json':
          exportData = JSON.stringify(strategy, null, 2)
          fileName = `${strategy.name}_${strategy.version}.json`
          mimeType = 'application/json'
          break
          
        case 'python':
          exportData = generatePythonCode(strategy)
          fileName = `${strategy.name}_${strategy.version}.py`
          mimeType = 'text/x-python'
          break
          
        case 'javascript':
          exportData = generateJavaScriptCode(strategy)
          fileName = `${strategy.name}_${strategy.version}.js`
          mimeType = 'text/javascript'
          break
          
        default:
          throw new Error('不支持的导出格式')
      }

      // 创建下载链接
      const blob = new Blob([exportData], { type: mimeType })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      ElMessage.success(`策略已导出为 ${format.toUpperCase()} 格式`)
      return exportData
      
    } catch (error) {
      const message = error instanceof Error ? error.message : '导出策略失败'
      ElMessage.error(message)
      throw error
    }
  }

  // 生成Python代码
  const generatePythonCode = (strategy: Strategy): string => {
    const metadata = `"""
@name ${strategy.name}
@description ${strategy.description}
@author ${strategy.author}
@version ${strategy.version}
@risk ${strategy.riskLevel}
@category ${strategy.type}
@tags ${strategy.tags.join(', ')}
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class ${strategy.entryPoint || 'Strategy'}:
    def __init__(self, config: Dict):
        self.config = config
        self.positions = {}
        self.signals = []
        
    def initialize(self):
        """策略初始化"""
        pass
        
    def handle_data(self, data: pd.DataFrame):
        """处理市场数据"""
        pass
        
    def before_trading_start(self, data: pd.DataFrame):
        """开盘前处理"""
        pass
        
    def after_trading_end(self, data: pd.DataFrame):
        """收盘后处理"""
        pass

# 原始代码
${strategy.sourceCode || '# 策略代码将在这里显示'}
`
    return metadata
  }

  // 生成JavaScript代码
  const generateJavaScriptCode = (strategy: Strategy): string => {
    const metadata = `/**
 * @name ${strategy.name}
 * @description ${strategy.description}
 * @author ${strategy.author}
 * @version ${strategy.version}
 * @risk ${strategy.riskLevel}
 * @category ${strategy.type}
 * @tags ${strategy.tags.join(', ')}
 */

class ${strategy.entryPoint || 'Strategy'} {
  constructor(config) {
    this.config = config;
    this.positions = {};
    this.signals = [];
  }
  
  initialize() {
    // 策略初始化
  }
  
  handleData(data) {
    // 处理市场数据
  }
  
  beforeTradingStart(data) {
    // 开盘前处理
  }
  
  afterTradingEnd(data) {
    // 收盘后处理
  }
}

// 原始代码
${strategy.sourceCode || '// 策略代码将在这里显示'}

module.exports = ${strategy.entryPoint || 'Strategy'};
`
    return metadata
  }

  // 重置状态
  const reset = () => {
    strategies.value = []
    strategyInstances.value = []
    signals.value = []
    backtestResults.value = []
    selectedStrategy.value = null
    editingStrategy.value = null
    clearErrors()
  }

  return {
    // 状态
    strategies,
    strategyInstances,
    signals,
    backtestResults,
    selectedStrategy,
    editingStrategy,
    loading,
    errors,
    
    // 计算属性
    strategiesByStatus,
    strategiesByType,
    runningStrategiesCount,
    todaySignalsCount,
    totalPnL,
    
    // 方法
    fetchStrategies,
    getStrategies,
    getFeaturedStrategies,
    fetchStrategyById,
    createStrategy,
    updateStrategy,
    deleteStrategy,
    startStrategy,
    stopStrategy,
    runBacktest,
    fetchBacktestHistory,
    fetchBacktestResult,
    favoriteStrategy,
    unfavoriteStrategy,
    downloadStrategy,
    importStrategy,
    exportStrategy,
    setSelectedStrategy,
    setEditingStrategy,
    clearErrors,
    reset
  }
}) 