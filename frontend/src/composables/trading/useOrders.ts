import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatCurrency, formatPercent } from '@/utils/formatters'
// import { tradingApi } from '@/api/trading'
import type { Order, OrderStats } from '@/types/trading'

/**
 * useOrders 组合式函数
 * 提供订单管理、统计分析、风险监控等功能
 */
export const useOrders = () => {
  const loading = ref(false)
  const orders = ref<Order[]>([])
  const selectedOrders = ref<Order[]>([])
  const wsConnected = ref(false)

  // 订单统计数据
  const orderStats = ref<OrderStats>({
    total: 0,
    pending: 0,
    filled: 0,
    partial: 0,
    cancelled: 0,
    rejected: 0,
    todayPending: 0,
    fillRate: 0,
    cancelRate: 0,
    avgFillPercent: 0,
    efficiency: 0,
    efficiencyChange: 0
  })

  // 计算属性
  const hasRiskOrders = computed(() => {
    return orders.value.some(order => 
      order.riskLevel && ['medium', 'high'].includes(order.riskLevel)
    )
  })

  const riskOrdersCount = computed(() => {
    return orders.value.filter(order => 
      order.riskLevel && ['medium', 'high'].includes(order.riskLevel)
    ).length
  })

  const activeOrdersCount = computed(() => {
    return orders.value.filter(order => 
      ['pending', 'partial'].includes(order.status)
    ).length
  })

  const avgFillTime = computed(() => {
    const filledOrders = orders.value.filter(order => order.status === 'filled')
    if (filledOrders.length === 0) return 0
    
    const totalTime = filledOrders.reduce((sum, order) => {
      const createTime = new Date(order.createTime).getTime()
      const updateTime = new Date(order.updateTime || order.createTime).getTime()
      return sum + (updateTime - createTime) / 1000
    }, 0)
    
    return Math.round(totalTime / filledOrders.length)
  })

  const avgSlippage = computed(() => {
    const filledOrders = orders.value.filter(order => 
      order.status === 'filled' && order.avgFillPrice && order.price
    )
    if (filledOrders.length === 0) return 0
    
    const totalSlippage = filledOrders.reduce((sum, order) => {
      const slippage = Math.abs(order.avgFillPrice! - order.price) / order.price * 100
      return sum + slippage
    }, 0)
    
    return (totalSlippage / filledOrders.length).toFixed(2)
  })

  const slippageClass = computed(() => {
    const slippage = parseFloat(avgSlippage.value)
    if (slippage > 0.5) return 'risk'
    if (slippage > 0.2) return 'warning'
    return 'normal'
  })

  /**
   * 获取订单列表
   */
  const fetchOrders = async () => {
    try {
      loading.value = true
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 模拟订单数据
      orders.value = [
        {
          id: 'ORD001',
          orderNo: 'T240110001',
          symbol: '000001',
          stockName: '平安银行',
          side: 'buy',
          orderType: 'limit',
          quantity: 1000,
          price: 12.58,
          filledQuantity: 1000,
          avgFillPrice: 12.60,
          fillPercent: 100,
          status: 'filled',
          riskLevel: 'low',
          isUrgent: false,
          createTime: '2024-01-10 09:30:00',
          updateTime: '2024-01-10 09:30:15',
          cancelling: false
        },
        {
          id: 'ORD002',
          orderNo: 'T240110002',
          symbol: '000002',
          stockName: '万科A',
          side: 'sell',
          orderType: 'limit',
          quantity: 500,
          price: 18.76,
          filledQuantity: 0,
          avgFillPrice: 0,
          fillPercent: 0,
          status: 'pending',
          riskLevel: 'medium',
          isUrgent: true,
          createTime: '2024-01-10 10:15:00',
          updateTime: '2024-01-10 10:15:00',
          cancelling: false
        },
        {
          id: 'ORD003',
          orderNo: 'T240110003',
          symbol: '600036',
          stockName: '招商银行',
          side: 'buy',
          orderType: 'market',
          quantity: 300,
          price: 42.30,
          filledQuantity: 0,
          avgFillPrice: 0,
          fillPercent: 0,
          status: 'cancelled',
          riskLevel: 'low',
          isUrgent: false,
          createTime: '2024-01-10 11:20:00',
          updateTime: '2024-01-10 11:25:00',
          cancelling: false
        },
        {
          id: 'ORD004',
          orderNo: 'T240110004',
          symbol: '000858',
          stockName: '五粮液',
          side: 'buy',
          orderType: 'limit',
          quantity: 100,
          price: 168.50,
          filledQuantity: 60,
          avgFillPrice: 168.80,
          fillPercent: 60,
          status: 'partial',
          riskLevel: 'high',
          isUrgent: false,
          createTime: '2024-01-10 13:45:00',
          updateTime: '2024-01-10 13:50:00',
          cancelling: false
        },
        {
          id: 'ORD005',
          orderNo: 'T240110005',
          stockCode: '600519',
          stockName: '贵州茅台',
          side: 'buy',
          orderType: 'stop',
          quantity: 10,
          price: 1650.00,
          filledQuantity: 0,
          avgFillPrice: 0,
          fillPercent: 0,
          status: 'rejected',
          riskLevel: 'high',
          isUrgent: true,
          rejectReason: '资金不足',
          createTime: '2024-01-10 14:20:00',
          updateTime: '2024-01-10 14:20:05',
          cancelling: false
        }
      ]
      
      // 计算统计数据
      calculateOrderStats()
      
      ElMessage.success('订单数据加载成功')
    } catch (error) {
      console.error('获取订单列表失败:', error)
      ElMessage.error('获取订单列表失败')
    } finally {
      loading.value = false
    }
  }

  /**
   * 计算订单统计
   */
  const calculateOrderStats = () => {
    const total = orders.value.length
    const pending = orders.value.filter(o => o.status === 'pending').length
    const filled = orders.value.filter(o => o.status === 'filled').length
    const partial = orders.value.filter(o => o.status === 'partial').length
    const cancelled = orders.value.filter(o => o.status === 'cancelled').length
    const rejected = orders.value.filter(o => o.status === 'rejected').length
    
    const fillRate = total > 0 ? Math.round((filled / total) * 100) : 0
    const cancelRate = total > 0 ? Math.round((cancelled / total) * 100) : 0
    
    const partialOrders = orders.value.filter(o => o.status === 'partial')
    const avgFillPercent = partialOrders.length > 0 
      ? Math.round(partialOrders.reduce((sum, o) => sum + o.fillPercent, 0) / partialOrders.length)
      : 0
    
    // 计算执行效率（基于成交率、撤单率、滑点等）
    const efficiency = Math.max(0, 100 - cancelRate - parseFloat(avgSlippage.value) * 10)
    
    orderStats.value = {
      total,
      pending,
      filled,
      partial,
      cancelled,
      rejected,
      todayPending: Math.floor(pending * 0.7), // 模拟今日新增
      fillRate,
      cancelRate,
      avgFillPercent,
      efficiency: Math.round(efficiency),
      efficiencyChange: Math.round((Math.random() - 0.5) * 10) // 模拟变化
    }
  }

  /**
   * 刷新订单数据
   */
  const refreshOrders = async () => {
    await fetchOrders()
  }

  /**
   * 撤销单个订单
   */
  const cancelOrder = async (orderId: string) => {
    try {
      const order = orders.value.find(o => o.id === orderId)
      if (!order) {
        throw new Error('订单不存在')
      }
      
      if (!['pending', 'partial'].includes(order.status)) {
        throw new Error('该订单无法撤销')
      }
      
      order.cancelling = true
      
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      order.status = 'cancelled'
      order.updateTime = new Date().toISOString()
      
      // 重新计算统计数据
      calculateOrderStats()
      
      ElMessage.success('订单撤销成功')
    } catch (error) {
      console.error('撤单失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '撤单失败')
    } finally {
      const order = orders.value.find(o => o.id === orderId)
      if (order) {
        order.cancelling = false
      }
    }
  }

  /**
   * 批量撤销订单
   */
  const batchCancelOrders = async (orderIds: string[]) => {
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      orderIds.forEach(orderId => {
        const order = orders.value.find(o => o.id === orderId)
        if (order && ['pending', 'partial'].includes(order.status)) {
          order.status = 'cancelled'
          order.updateTime = new Date().toISOString()
        }
      })
      
      // 重新计算统计数据
      calculateOrderStats()
      
      ElMessage.success(`成功撤销 ${orderIds.length} 个订单`)
    } catch (error) {
      console.error('批量撤单失败:', error)
      ElMessage.error('批量撤单失败')
    }
  }

  /**
   * 导出订单数据
   */
  const exportOrders = async (data?: Order[]) => {
    try {
      const exportData = data || orders.value
      
      // 模拟导出逻辑
      const csvContent = [
        ['订单号', '股票代码', '股票名称', '方向', '类型', '数量', '价格', '成交数量', '成交均价', '状态', '创建时间'].join(','),
        ...exportData.map(order => [
          order.orderNo,
          order.stockCode,
          order.stockName,
          order.side === 'buy' ? '买入' : '卖出',
          order.orderType,
          order.quantity,
          order.price,
          order.filledQuantity,
          order.avgFillPrice || 0,
          order.status,
          order.createTime
        ].join(','))
      ].join('\n')
      
      // 创建下载链接
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `订单数据_${new Date().toISOString().slice(0, 10)}.csv`)
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
   * 订阅订单更新
   */
  const subscribeOrderUpdates = () => {
    // 这里应该建立WebSocket连接订阅订单更新
    wsConnected.value = true
  }

  /**
   * 取消订阅订单更新
   */
  const unsubscribeOrderUpdates = () => {
    // 这里应该断开WebSocket连接
    wsConnected.value = false
  }

  return {
    loading,
    orders,
    selectedOrders,
    orderStats,
    wsConnected,
    hasRiskOrders,
    riskOrdersCount,
    activeOrdersCount,
    avgFillTime,
    avgSlippage,
    slippageClass,
    fetchOrders,
    refreshOrders,
    cancelOrder,
    batchCancelOrders,
    exportOrders,
    subscribeOrderUpdates,
    unsubscribeOrderUpdates,
    calculateOrderStats
  }
} 