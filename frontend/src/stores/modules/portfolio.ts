import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  Portfolio,
  PortfolioSummary,
  PortfolioPosition,
  PortfolioPerformance,
  PortfolioAllocation
} from '@/types/portfolio'

export const usePortfolioStore = defineStore('portfolio', () => {
  // State
  const portfolios = ref<Portfolio[]>([])
  const currentPortfolio = ref<Portfolio | null>(null)
  const positions = ref<PortfolioPosition[]>([])
  const performance = ref<PortfolioPerformance | null>(null)
  const allocation = ref<PortfolioAllocation[]>([])
  const portfolioTrend = ref<Array<{ date: string; totalAssets: number }>>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const totalValue = computed(() => {
    return positions.value.reduce((sum, pos) => sum + pos.marketValue, 0)
  })

  const totalPnL = computed(() => {
    return positions.value.reduce((sum, pos) => sum + pos.unrealizedPnL, 0)
  })

  const totalPnLPercent = computed(() => {
    const totalCost = positions.value.reduce((sum, pos) => sum + pos.costBasis, 0)
    return totalCost > 0 ? (totalPnL.value / totalCost) * 100 : 0
  })

  const summary = computed((): PortfolioSummary => ({
    totalValue: totalValue.value,
    totalPnL: totalPnL.value,
    totalPnLPercent: totalPnLPercent.value,
    positionCount: positions.value.length,
    cashBalance: currentPortfolio.value?.cashBalance || 0,
    availableCash: currentPortfolio.value?.availableCash || 0
  }))

  const topPositions = computed(() => {
    return [...positions.value]
      .sort((a, b) => b.marketValue - a.marketValue)
      .slice(0, 10)
  })

  const worstPerformers = computed(() => {
    return [...positions.value]
      .sort((a, b) => a.unrealizedPnLPercent - b.unrealizedPnLPercent)
      .slice(0, 5)
  })

  const bestPerformers = computed(() => {
    return [...positions.value]
      .sort((a, b) => b.unrealizedPnLPercent - a.unrealizedPnLPercent)
      .slice(0, 5)
  })

  // Actions
  const fetchPortfolios = async () => {
    try {
      isLoading.value = true
      error.value = null

      // TODO: Replace with actual API call
      // const response = await portfolioService.getPortfolios()
      // portfolios.value = response.data

      // Mock data for now
      portfolios.value = []
    } catch (err: any) {
      error.value = err.message || '获取投资组合失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const setCurrentPortfolio = async (portfolioId: string) => {
    try {
      isLoading.value = true
      error.value = null

      const portfolio = portfolios.value.find(p => p.id === portfolioId)
      if (!portfolio) {
        throw new Error('投资组合不存在')
      }

      currentPortfolio.value = portfolio

      // Fetch positions for this portfolio
      await fetchPositions(portfolioId)
      await fetchPerformance(portfolioId)
      await fetchAllocation(portfolioId)

    } catch (err: any) {
      error.value = err.message || '切换投资组合失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const fetchPositions = async (portfolioId?: string) => {
    try {
      const id = portfolioId || currentPortfolio.value?.id
      if (!id) return

      // TODO: Replace with actual API call
      // const response = await portfolioService.getPositions(id)
      // positions.value = response.data

      // Mock data for now
      positions.value = []
    } catch (err: any) {
      error.value = err.message || '获取持仓失败'
      throw err
    }
  }

  const fetchPerformance = async (portfolioId?: string) => {
    try {
      const id = portfolioId || currentPortfolio.value?.id
      if (!id) return

      // TODO: Replace with actual API call
      // const response = await portfolioService.getPerformance(id)
      // performance.value = response.data

      // Mock data for now
      performance.value = null
    } catch (err: any) {
      error.value = err.message || '获取绩效失败'
      throw err
    }
  }

  const fetchAllocation = async (portfolioId?: string) => {
    try {
      const id = portfolioId || currentPortfolio.value?.id
      if (!id) return

      // TODO: Replace with actual API call
      // const response = await portfolioService.getAllocation(id)
      // allocation.value = response.data

      // Mock data for now
      allocation.value = []
    } catch (err: any) {
      error.value = err.message || '获取配置失败'
      throw err
    }
  }

  const fetchPortfolioTrend = async (params: { timeRange: string; symbol: string }) => {
    try {
      isLoading.value = true
      error.value = null

      // TODO: Replace with actual API call
      // const response = await portfolioService.getPortfolioTrend(params)
      // portfolioTrend.value = response.data

      // Mock data for now
      const mockData = []
      const now = new Date()
      const days = params.timeRange === 'today' ? 1 : params.timeRange === 'week' ? 7 : 30
      
      for (let i = days - 1; i >= 0; i--) {
        const date = new Date(now)
        date.setDate(date.getDate() - i)
        mockData.push({
          date: date.toISOString().split('T')[0],
          totalAssets: 1000000 + Math.random() * 100000 - 50000
        })
      }
      
      portfolioTrend.value = mockData
    } catch (err: any) {
      error.value = err.message || '获取投资组合趋势失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const initialize = async () => {
    try {
      await fetchPortfolios()
      if (portfolios.value.length > 0) {
        await setCurrentPortfolio(portfolios.value[0].id)
      }
    } catch (err: any) {
      console.error('初始化投资组合失败:', err)
    }
  }

  const createPortfolio = async (portfolioData: Omit<Portfolio, 'id' | 'createdAt' | 'updatedAt'>) => {
    try {
      isLoading.value = true
      error.value = null

      // TODO: Replace with actual API call
      // const response = await portfolioService.createPortfolio(portfolioData)
      // const newPortfolio = response.data
      // portfolios.value.push(newPortfolio)
      // return newPortfolio

      // Mock implementation
      const newPortfolio: Portfolio = {
        ...portfolioData,
        id: Date.now().toString(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      portfolios.value.push(newPortfolio)
      return newPortfolio

    } catch (err: any) {
      error.value = err.message || '创建投资组合失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const updatePortfolio = async (portfolioId: string, updates: Partial<Portfolio>) => {
    try {
      isLoading.value = true
      error.value = null

      // TODO: Replace with actual API call
      // const response = await portfolioService.updatePortfolio(portfolioId, updates)
      // const updatedPortfolio = response.data

      // Mock implementation
      const index = portfolios.value.findIndex(p => p.id === portfolioId)
      if (index !== -1) {
        portfolios.value[index] = { ...portfolios.value[index], ...updates }
        if (currentPortfolio.value?.id === portfolioId) {
          currentPortfolio.value = portfolios.value[index]
        }
      }

    } catch (err: any) {
      error.value = err.message || '更新投资组合失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const deletePortfolio = async (portfolioId: string) => {
    try {
      isLoading.value = true
      error.value = null

      // TODO: Replace with actual API call
      // await portfolioService.deletePortfolio(portfolioId)

      // Mock implementation
      portfolios.value = portfolios.value.filter(p => p.id !== portfolioId)
      if (currentPortfolio.value?.id === portfolioId) {
        currentPortfolio.value = null
        positions.value = []
        performance.value = null
        allocation.value = []
      }

    } catch (err: any) {
      error.value = err.message || '删除投资组合失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const refreshData = async () => {
    if (currentPortfolio.value) {
      await Promise.all([
        fetchPositions(),
        fetchPerformance(),
        fetchAllocation()
      ])
    }
  }

  const clearError = () => {
    error.value = null
  }

  const reset = () => {
    portfolios.value = []
    currentPortfolio.value = null
    positions.value = []
    performance.value = null
    allocation.value = []
    portfolioTrend.value = []
    error.value = null
  }

  return {
    // State
    portfolios,
    currentPortfolio,
    positions,
    performance,
    allocation,
    portfolioTrend,
    isLoading,
    error,

    // Getters
    totalValue,
    totalPnL,
    totalPnLPercent,
    summary,
    topPositions,
    worstPerformers,
    bestPerformers,

    // Actions
    fetchPortfolios,
    setCurrentPortfolio,
    fetchPositions,
    fetchPerformance,
    fetchAllocation,
    fetchPortfolioTrend,
    createPortfolio,
    updatePortfolio,
    deletePortfolio,
    refreshData,
    initialize,
    clearError,
    reset
  }
}, {
  persist: {
    key: 'portfolio-store',
    storage: localStorage,
    paths: ['currentPortfolio']
  }
})
