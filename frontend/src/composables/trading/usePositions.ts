import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useWebSocket } from '@/composables/useWebSocket'
import { formatCurrency, formatPercent } from '@/utils/formatters'
// import { tradingApi } from '@/api/trading'
import type { Position, AccountSummary } from '@/types/trading'

/**
 * usePositions 组合式函数
 * 提供持仓列表管理、账户概览、买卖操作等功能
 */
export const usePositions = () => {
  const loading = ref(false)
  const positions = ref<Position[]>([])
  const accountSummary = ref<AccountSummary>({
    totalAssets: 0,
    availableCash: 0,
    todayPnl: 0,
    totalPnl: 0,
    totalMarketValue: 0,
    totalCostValue: 0,
    totalAssetsChange: 0,
    totalAssetsChangePercent: 0,
    todayPnlPercent: 0,
    cashRatio: 0
  })

  // WebSocket连接状态
  const wsConnected = ref(false)

  // 计算属性
  const totalPnl = computed(() => {
    return positions.value.reduce((sum, pos) => sum + pos.unrealizedPnl, 0)
  })

  const totalPnlPercent = computed(() => {
    const totalCost = positions.value.reduce((sum, pos) => sum + (pos.avgPrice * pos.size), 0)
    return totalCost > 0 ? (totalPnl.value / totalCost) * 100 : 0
  })

  const totalMarketValue = computed(() => {
    return positions.value.reduce((sum, pos) => sum + pos.markPrice * pos.size, 0)
  })

  const profitablePositions = computed(() => {
    return positions.value.filter(pos => pos.unrealizedPnl > 0).length
  })

  const losingPositions = computed(() => {
    return positions.value.filter(pos => pos.unrealizedPnl < 0).length
  })

  /**
   * 获取持仓列表
   */
  const fetchPositions = async () => {
    try {
      loading.value = true

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      // 模拟持仓数据
      positions.value = [
        {
          symbol: '000001',
          side: 'long',
          size: 1000,
          avgPrice: 12.30,
          markPrice: 13.20,
          unrealizedPnl: 900,
          unrealizedPnlPercent: 7.32,
          margin: 0,
          marginRatio: 0,
          liquidationPrice: 0,
          leverage: 1,
          createTime: new Date().toISOString(),
          updateTime: new Date().toISOString()
        },
        {
          symbol: '000002',
          side: 'long',
          size: 500,
          avgPrice: 18.50,
          markPrice: 17.80,
          unrealizedPnl: -350,
          unrealizedPnlPercent: -3.78,
          margin: 0,
          marginRatio: 0,
          liquidationPrice: 0,
          leverage: 1,
          createTime: new Date().toISOString(),
          updateTime: new Date().toISOString()
        },
        {
          symbol: '600036',
          side: 'long',
          size: 300,
          avgPrice: 41.20,
          markPrice: 42.80,
          unrealizedPnl: 480,
          unrealizedPnlPercent: 3.88,
          margin: 0,
          marginRatio: 0,
          liquidationPrice: 0,
          leverage: 1,
          createTime: new Date().toISOString(),
          updateTime: new Date().toISOString()
        }
      ]

      // 计算账户概览
      const totalMarketVal = totalMarketValue.value
      const totalCostValue = positions.value.reduce((sum, pos) => sum + pos.avgPrice * pos.size, 0)
      const totalPnlVal = totalPnl.value
      const todayPnl = positions.value.reduce((sum, pos) => sum + pos.unrealizedPnl * 0.3, 0) // 模拟今日盈亏
      const availableCash = 50000

      accountSummary.value = {
        totalAssets: totalMarketVal + availableCash,
        availableCash,
        todayPnl,
        totalPnl: totalPnlVal,
        totalMarketValue: totalMarketVal,
        totalCostValue,
        totalAssetsChange: totalPnlVal + todayPnl * 0.5,
        totalAssetsChangePercent: totalCostValue > 0 ? ((totalPnlVal + todayPnl * 0.5) / totalCostValue) * 100 : 0,
        todayPnlPercent: totalCostValue > 0 ? (todayPnl / totalCostValue) * 100 : 0,
        cashRatio: availableCash / (totalMarketVal + availableCash) * 100
      }

      ElMessage.success('持仓数据加载成功')
    } catch (error) {
      console.error('获取持仓列表失败:', error)
      ElMessage.error('获取持仓列表失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取账户概览
   */
  const fetchAccountSummary = async () => {
    // 在fetchPositions中一起计算了
  }

  /**
   * 买入股票
   */
  const buyStock = async (symbol: string, name?: string) => {
    try {
      // 这里应该打开交易弹窗或跳转到交易页面
      ElMessage.info(`准备买入 ${name || symbol}`)
      // 可以触发一个事件或调用路由跳转
    } catch (error) {
      console.error('买入操作失败:', error)
      ElMessage.error('买入操作失败')
    }
  }

  /**
   * 卖出股票
   */
  const sellStock = async (position: Position) => {
    try {
      // 这里应该打开卖出弹窗
      ElMessage.info(`准备卖出 ${position.symbol}`)
      // 可以触发一个事件或调用路由跳转
    } catch (error) {
      console.error('卖出操作失败:', error)
      ElMessage.error('卖出操作失败')
    }
  }

  /**
   * 卖出持仓
   */
  const sellPosition = async (positionId: string, quantity: number, price?: number) => {
    try {
      const position = positions.value.find(p => p.symbol === positionId)
      if (!position) {
        throw new Error('持仓不存在')
      }

      if (quantity > position.size) {
        throw new Error('卖出数量超过持仓数量')
      }

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))

      ElMessage.success(`成功提交卖出订单: ${position.symbol} ${quantity}股`)

      // 刷新持仓数据
      await fetchPositions()
    } catch (error) {
      console.error('卖出失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '卖出失败')
    }
  }

  /**
   * 买入更多
   */
  const buyMore = async (symbol: string, quantity: number, price?: number) => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 500))

      ElMessage.success(`成功提交买入订单: ${symbol} ${quantity}股`)

      // 刷新持仓数据
      await fetchPositions()
    } catch (error) {
      console.error('买入失败:', error)
      ElMessage.error('买入失败')
    }
  }

  /**
   * 一键清仓
   */
  const clearAllPositions = async () => {
    try {
      await ElMessageBox.confirm(
        '确定要清空所有持仓吗？此操作不可撤销。',
        '确认清仓',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )

      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))

      ElMessage.success('清仓订单已提交')

      // 刷新持仓数据
      await fetchPositions()
    } catch (error) {
      if (error !== 'cancel') {
        console.error('清仓失败:', error)
        ElMessage.error('清仓失败')
      }
    }
  }

  /**
   * 导出持仓数据
   */
  const exportPositions = async (data?: Position[]) => {
    try {
      const exportData = data || positions.value

      // 模拟导出逻辑
      const csvContent = [
        ['股票代码', '持仓数量', '成本价', '现价', '浮动盈亏', '盈亏比例'].join(','),
        ...exportData.map(pos => [
          pos.symbol,
          pos.size,
          pos.avgPrice,
          pos.markPrice,
          pos.unrealizedPnl,
          `${pos.unrealizedPnlPercent.toFixed(2)}%`
        ].join(','))
      ].join('\n')

      // 创建下载链接
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `持仓数据_${new Date().toISOString().slice(0, 10)}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      ElMessage.success('导出成功')
    } catch (error) {
      console.error('导出失败:', error)
      ElMessage.error('导出失败')
    }
  }

  /**
   * 订阅持仓更新
   */
  const subscribePositionUpdates = () => {
    // 这里应该建立WebSocket连接订阅持仓更新
    wsConnected.value = true
  }

  /**
   * 取消订阅持仓更新
   */
  const unsubscribePositionUpdates = () => {
    // 这里应该断开WebSocket连接
    wsConnected.value = false
  }

  /**
   * 刷新所有数据
   */
  const refreshAll = async () => {
    await Promise.all([
      fetchPositions(),
      fetchAccountSummary()
    ])
  }

  return {
    loading,
    positions,
    accountSummary,
    totalPnl,
    totalPnlPercent,
    totalMarketValue,
    profitablePositions,
    losingPositions,
    wsConnected,
    fetchPositions,
    fetchAccountSummary,
    buyStock,
    sellStock,
    sellPosition,
    buyMore,
    clearAllPositions,
    exportPositions,
    subscribePositionUpdates,
    unsubscribePositionUpdates,
    refreshAll
  }
}
