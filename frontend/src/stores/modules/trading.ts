import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tradingApi } from '@/api'
import type { 
  Account, 
  Position, 
  Order, 
  TradeRecord,
  OrderSubmitData,
  OrderType,
  OrderSide,
  OrderStatus 
} from '@/types/trading'

export const useTradingStore = defineStore('trading', () => {
  // ============ 状态定义 ============
  
  // 账户信息
  const account = ref<Account>({
    accountId: '',
    totalAssets: 0,
    availableCash: 0,
    frozenCash: 0,
    marketValue: 0,
    totalProfit: 0,
    totalProfitPercent: 0,
    dailyProfit: 0,
    dailyProfitPercent: 0,
    commission: 0,
    lastUpdateTime: Date.now()
  })

  // 持仓列表
  const positions = ref<Position[]>([])

  // 订单列表
  const orders = ref<Order[]>([])

  // 交易记录
  const trades = ref<TradeRecord[]>([])

  // 加载状态
  const loading = ref({
    account: false,
    positions: false,
    orders: false,
    trades: false,
    submit: false
  })

  // 错误状态
  const errors = ref({
    account: null as string | null,
    positions: null as string | null,
    orders: null as string | null,
    trades: null as string | null,
    submit: null as string | null
  })

  // ============ 计算属性 ============

  // 总持仓市值
  const totalPositionValue = computed(() => {
    return positions.value.reduce((sum, position) => sum + position.marketValue, 0)
  })

  // 总持仓成本
  const totalPositionCost = computed(() => {
    return positions.value.reduce((sum, position) => sum + position.cost, 0)
  })

  // 总浮动盈亏
  const totalUnrealizedPnl = computed(() => {
    return positions.value.reduce((sum, position) => sum + position.unrealizedPnl, 0)
  })

  // 总浮动盈亏百分比
  const totalUnrealizedPnlPercent = computed(() => {
    return totalPositionCost.value > 0 
      ? (totalUnrealizedPnl.value / totalPositionCost.value) * 100 
      : 0
  })

  // 活跃订单（未成交和部分成交）
  const activeOrders = computed(() => {
    return orders.value.filter(order => 
      ['pending', 'partial'].includes(order.status)
    )
  })

  // 今日订单
  const todayOrders = computed(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const todayTimestamp = today.getTime()
    
    return orders.value.filter(order => order.createTime >= todayTimestamp)
  })

  // 持仓股票列表
  const positionSymbols = computed(() => {
    return positions.value.map(position => position.symbol)
  })

  // 按股票分组的持仓
  const positionsBySymbol = computed(() => {
    const map = new Map<string, Position>()
    positions.value.forEach(position => {
      map.set(position.symbol, position)
    })
    return map
  })

  // 风险指标
  const riskMetrics = computed(() => {
    const totalAssets = account.value.totalAssets
    const maxPositionValue = Math.max(...positions.value.map(p => p.marketValue), 0)
    const maxPositionPercent = totalAssets > 0 ? (maxPositionValue / totalAssets) * 100 : 0
    
    return {
      maxPositionPercent,
      positionCount: positions.value.length,
      concentrationRisk: maxPositionPercent > 30 ? 'high' : maxPositionPercent > 20 ? 'medium' : 'low',
      leverageRatio: totalAssets > 0 ? totalPositionValue.value / totalAssets : 0
    }
  })

  // ============ 数据获取方法 ============

  // 获取账户信息
  const fetchAccount = async () => {
    loading.value.account = true
    errors.value.account = null
    
    try {
      const accountData = await tradingApi.getAccount()
      account.value = {
        ...accountData,
        lastUpdateTime: Date.now()
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取账户信息失败'
      errors.value.account = message
      throw error
    } finally {
      loading.value.account = false
    }
  }

  // 获取持仓信息
  const fetchPositions = async () => {
    loading.value.positions = true
    errors.value.positions = null
    
    try {
      const positionsData = await tradingApi.getPositions()
      positions.value = positionsData
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取持仓信息失败'
      errors.value.positions = message
      throw error
    } finally {
      loading.value.positions = false
    }
  }

  // 获取订单信息
  const fetchOrders = async (params?: {
    status?: OrderStatus
    symbol?: string
    startDate?: string
    endDate?: string
    limit?: number
  }) => {
    loading.value.orders = true
    errors.value.orders = null
    
    try {
      const ordersData = await tradingApi.getOrders(params)
      orders.value = ordersData
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取订单信息失败'
      errors.value.orders = message
      throw error
    } finally {
      loading.value.orders = false
    }
  }

  // 获取交易记录
  const fetchTrades = async (params?: {
    symbol?: string
    startDate?: string
    endDate?: string
    limit?: number
  }) => {
    loading.value.trades = true
    errors.value.trades = null
    
    try {
      const tradesData = await tradingApi.getTrades(params)
      trades.value = tradesData
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取交易记录失败'
      errors.value.trades = message
      throw error
    } finally {
      loading.value.trades = false
    }
  }

  // ============ 交易操作方法 ============

  // 提交订单
  const submitOrder = async (orderData: OrderSubmitData) => {
    loading.value.submit = true
    errors.value.submit = null
    
    try {
      // 前置验证
      await validateOrder(orderData)
      
      // 提交订单
      const order = await tradingApi.createOrder(orderData)
      
      // 更新本地订单列表
      orders.value.unshift(order)
      
      // 刷新账户和持仓信息
      await Promise.all([
        fetchAccount(),
        fetchPositions()
      ])
      
      return order
    } catch (error) {
      const message = error instanceof Error ? error.message : '订单提交失败'
      errors.value.submit = message
      throw error
    } finally {
      loading.value.submit = false
    }
  }

  // 撤销订单
  const cancelOrder = async (orderId: string) => {
    try {
      await tradingApi.cancelOrder(orderId)
      
      // 更新本地订单状态
      const orderIndex = orders.value.findIndex(order => order.id === orderId)
      if (orderIndex !== -1) {
        orders.value[orderIndex].status = 'cancelled'
        orders.value[orderIndex].updateTime = Date.now()
      }
      
      // 刷新相关数据
      await Promise.all([
        fetchAccount(),
        fetchOrders()
      ])
    } catch (error) {
      const message = error instanceof Error ? error.message : '撤销订单失败'
      throw new Error(message)
    }
  }

  // 批量撤销订单
  const cancelMultipleOrders = async (orderIds: string[]) => {
    const results = await Promise.allSettled(
      orderIds.map(id => cancelOrder(id))
    )
    
    const failed = results
      .map((result, index) => ({ result, id: orderIds[index] }))
      .filter(({ result }) => result.status === 'rejected')
      .map(({ id }) => id)
    
    if (failed.length > 0) {
      throw new Error(`部分订单撤销失败: ${failed.join(', ')}`)
    }
  }

  // ============ 数据更新方法 ============

  // 更新持仓实时数据
  const updatePositionPrice = (symbol: string, currentPrice: number) => {
    const position = positions.value.find(p => p.symbol === symbol)
    if (position) {
      const oldMarketValue = position.marketValue
      position.currentPrice = currentPrice
      position.marketValue = position.totalQuantity * currentPrice
      position.unrealizedPnl = position.marketValue - position.cost
      position.unrealizedPnlPercent = position.cost > 0 
        ? (position.unrealizedPnl / position.cost) * 100 
        : 0
      
      // 更新账户总资产
      const marketValueChange = position.marketValue - oldMarketValue
      account.value.totalAssets += marketValueChange
      account.value.marketValue += marketValueChange
    }
  }

  // 更新订单状态
  const updateOrderStatus = (orderId: string, status: OrderStatus, filledQuantity?: number) => {
    const order = orders.value.find(o => o.id === orderId)
    if (order) {
      order.status = status
      order.updateTime = Date.now()
      
      if (filledQuantity !== undefined) {
        order.filledQuantity = filledQuantity
      }
    }
  }

  // ============ 工具方法 ============

  // 获取指定股票的持仓
  const getPositionBySymbol = (symbol: string): Position | undefined => {
    return positions.value.find(position => position.symbol === symbol)
  }

  // 获取指定股票的可用数量
  const getAvailableQuantity = (symbol: string): number => {
    const position = getPositionBySymbol(symbol)
    return position ? position.availableQuantity : 0
  }

  // 检查是否可以卖出
  const canSell = (symbol: string, quantity: number): boolean => {
    const availableQuantity = getAvailableQuantity(symbol)
    return availableQuantity >= quantity
  }

  // 检查是否可以买入
  const canBuy = (symbol: string, price: number, quantity: number): boolean => {
    const requiredAmount = price * quantity
    const estimatedFee = calculateFee('buy', requiredAmount)
    const totalRequired = requiredAmount + estimatedFee
    
    return account.value.availableCash >= totalRequired
  }

  // 计算手续费
  const calculateFee = (side: OrderSide, amount: number): number => {
    // 简化的手续费计算，实际应该根据券商规则
    const commissionRate = 0.0003 // 万分之三
    const minCommission = 5 // 最低5元
    
    let fee = amount * commissionRate
    
    // 卖出时额外收取印花税
    if (side === 'sell') {
      const stampTax = amount * 0.001 // 千分之一
      fee += stampTax
    }
    
    return Math.max(fee, minCommission)
  }

  // 订单验证
  const validateOrder = async (orderData: OrderSubmitData) => {
    const { symbol, side, price, quantity, orderType } = orderData
    
    // 基础验证
    if (!symbol || !side || quantity <= 0) {
      throw new Error('订单参数不完整')
    }
    
    if (['limit', 'stop', 'stop-profit'].includes(orderType) && (!price || price <= 0)) {
      throw new Error('限价单必须指定有效价格')
    }
    
    // 买入验证
    if (side === 'buy') {
      const orderPrice = orderType === 'market' ? 0 : price // 市价单价格待确定
      if (orderType !== 'market' && !canBuy(symbol, orderPrice, quantity)) {
        throw new Error('可用资金不足')
      }
    }
    
    // 卖出验证
    if (side === 'sell' && !canSell(symbol, quantity)) {
      throw new Error('可卖数量不足')
    }
    
    // 数量必须是100的倍数（A股规则）
    if (quantity % 100 !== 0) {
      throw new Error('买卖数量必须是100股的倍数')
    }
  }

  // 计算订单预估金额
  const calculateOrderAmount = (orderData: Partial<OrderSubmitData>) => {
    const { side, price, quantity, orderType } = orderData
    
    if (!side || !quantity || quantity <= 0) {
      return { amount: 0, fee: 0, total: 0 }
    }
    
    let orderPrice = 0
    if (orderType === 'market') {
      // 市价单需要根据当前市价估算
      orderPrice = 0 // 这里应该从行情数据获取当前价格
    } else if (price && price > 0) {
      orderPrice = price
    }
    
    const amount = orderPrice * quantity
    const fee = calculateFee(side, amount)
    const total = side === 'buy' ? amount + fee : amount - fee
    
    return { amount, fee, total }
  }

  // ============ 初始化方法 ============

  // 初始化所有数据
  const initialize = async () => {
    try {
      await Promise.all([
        fetchAccount(),
        fetchPositions(),
        fetchOrders({ limit: 100 }),
        fetchTrades({ limit: 100 })
      ])
    } catch (error) {
      console.error('初始化交易数据失败:', error)
      throw error
    }
  }

  // 刷新所有数据
  const refresh = async () => {
    try {
      await Promise.all([
        fetchAccount(),
        fetchPositions(),
        fetchOrders({ status: 'pending' }) // 只获取活跃订单
      ])
    } catch (error) {
      console.error('刷新交易数据失败:', error)
      throw error
    }
  }

  // ============ 重置方法 ============

  // 重置所有状态
  const reset = () => {
    account.value = {
      accountId: '',
      totalAssets: 0,
      availableCash: 0,
      frozenCash: 0,
      marketValue: 0,
      totalProfit: 0,
      totalProfitPercent: 0,
      dailyProfit: 0,
      dailyProfitPercent: 0,
      commission: 0,
      lastUpdateTime: Date.now()
    }
    
    positions.value = []
    orders.value = []
    trades.value = []
    
    // 重置加载状态
    Object.keys(loading.value).forEach(key => {
      loading.value[key as keyof typeof loading.value] = false
    })
    
    // 重置错误状态
    Object.keys(errors.value).forEach(key => {
      errors.value[key as keyof typeof errors.value] = null
    })
  }

  // ============ 返回状态和方法 ============

  return {
    // 状态
    account,
    positions,
    orders,
    trades,
    loading,
    errors,
    
    // 计算属性
    totalPositionValue,
    totalPositionCost,
    totalUnrealizedPnl,
    totalUnrealizedPnlPercent,
    activeOrders,
    todayOrders,
    positionSymbols,
    positionsBySymbol,
    riskMetrics,
    
    // 数据获取方法
    fetchAccount,
    fetchPositions,
    fetchOrders,
    fetchTrades,
    
    // 交易操作方法
    submitOrder,
    cancelOrder,
    cancelMultipleOrders,
    
    // 数据更新方法
    updatePositionPrice,
    updateOrderStatus,
    
    // 工具方法
    getPositionBySymbol,
    getAvailableQuantity,
    canSell,
    canBuy,
    calculateFee,
    validateOrder,
    calculateOrderAmount,
    
    // 初始化方法
    initialize,
    refresh,
    reset
  }
}) 