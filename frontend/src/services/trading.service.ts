import { http } from '@/api/http'
import { EventEmitter } from 'events'
import { Decimal } from 'decimal.js'
import type { 
  Order, 
  Position, 
  Account, 
  OrderFormData,
  TradeRecord,
  RiskMetrics,
  PortfolioSummary 
} from '@/types/trading'

/**
 * 交易服务类
 */
class TradingService extends EventEmitter {
  private static instance: TradingService
  private ordersCache = new Map<string, Order>()
  private positionsCache = new Map<string, Position>()
  private accountCache: Account | null = null
  private lastUpdateTime = 0

  private constructor() {
    super()
  }

  /**
   * 获取单例实例
   */
  public static getInstance(): TradingService {
    if (!TradingService.instance) {
      TradingService.instance = new TradingService()
    }
    return TradingService.instance
  }

  /**
   * 提交订单
   * @param orderData 订单数据
   * @returns 订单结果
   */
  async submitOrder(orderData: OrderFormData): Promise<Order> {
    try {
      // 订单前置检查
      await this.validateOrder(orderData)

      const response = await http.post<{ data: Order }>('/trading/orders', orderData)
      
      if (response.data) {
        // 更新缓存
        this.ordersCache.set(response.data.id, response.data)
        
        // 发出事件
        this.emit('orderSubmitted', response.data)
        
        return response.data
      } else {
        throw new Error('提交订单失败')
      }
    } catch (error) {
      console.error('提交订单失败:', error)
      throw error
    }
  }

  /**
   * 取消订单
   * @param orderId 订单ID
   * @returns 取消结果
   */
  async cancelOrder(orderId: string): Promise<Order> {
    try {
      const response = await http.delete<{ data: Order }>(`/trading/orders/${orderId}`)
      
      if (response.data) {
        // 更新缓存
        this.ordersCache.set(response.data.id, response.data)
        
        // 发出事件
        this.emit('orderCancelled', response.data)
        
        return response.data
      } else {
        throw new Error('取消订单失败')
      }
    } catch (error) {
      console.error('取消订单失败:', error)
      throw error
    }
  }

  /**
   * 修改订单
   * @param orderId 订单ID
   * @param updateData 更新数据
   * @returns 修改结果
   */
  async modifyOrder(orderId: string, updateData: Partial<OrderFormData>): Promise<Order> {
    try {
      const response = await http.put<{ data: Order }>(`/trading/orders/${orderId}`, updateData)
      
      if (response.data) {
        // 更新缓存
        this.ordersCache.set(response.data.id, response.data)
        
        // 发出事件
        this.emit('orderModified', response.data)
        
        return response.data
      } else {
        throw new Error('修改订单失败')
      }
    } catch (error) {
      console.error('修改订单失败:', error)
      throw error
    }
  }

  /**
   * 获取订单列表
   * @param params 查询参数
   * @returns 订单列表
   */
  async getOrders(params?: {
    status?: string
    symbol?: string
    startDate?: string
    endDate?: string
    page?: number
    limit?: number
  }): Promise<{ orders: Order[]; total: number }> {
    try {
      const response = await http.get<{ 
        data: { orders: Order[]; total: number } 
      }>('/trading/orders', { params })
      
      if (response.data) {
        // 更新缓存
        response.data.orders.forEach(order => {
          this.ordersCache.set(order.id, order)
        })
        
        return response.data
      } else {
        throw new Error('获取订单列表失败')
      }
    } catch (error) {
      console.error('获取订单列表失败:', error)
      throw error
    }
  }

  /**
   * 获取单个订单详情
   * @param orderId 订单ID
   * @returns 订单详情
   */
  async getOrder(orderId: string): Promise<Order> {
    try {
      // 先从缓存获取
      const cached = this.ordersCache.get(orderId)
      if (cached && this.isCacheValid()) {
        return cached
      }

      const response = await http.get<{ data: Order }>(`/trading/orders/${orderId}`)
      
      if (response.data) {
        // 更新缓存
        this.ordersCache.set(response.data.id, response.data)
        
        return response.data
      } else {
        throw new Error('获取订单详情失败')
      }
    } catch (error) {
      console.error('获取订单详情失败:', error)
      throw error
    }
  }

  /**
   * 获取持仓列表
   * @returns 持仓列表
   */
  async getPositions(): Promise<Position[]> {
    try {
      const response = await http.get<{ data: Position[] }>('/trading/positions')
      
      if (response.data) {
        // 更新缓存
        this.positionsCache.clear()
        response.data.forEach(position => {
          this.positionsCache.set(position.symbol, position)
        })
        
        this.lastUpdateTime = Date.now()
        
        return response.data
      } else {
        throw new Error('获取持仓列表失败')
      }
    } catch (error) {
      console.error('获取持仓列表失败:', error)
      throw error
    }
  }

  /**
   * 获取单个持仓详情
   * @param symbol 股票代码
   * @returns 持仓详情
   */
  async getPosition(symbol: string): Promise<Position | null> {
    try {
      // 先从缓存获取
      const cached = this.positionsCache.get(symbol)
      if (cached && this.isCacheValid()) {
        return cached
      }

      const response = await http.get<{ data: Position }>(`/trading/positions/${symbol}`)
      
      if (response.data) {
        // 更新缓存
        this.positionsCache.set(symbol, response.data)
        
        return response.data
      } else {
        return null
      }
    } catch (error) {
      console.error('获取持仓详情失败:', error)
      return null
    }
  }

  /**
   * 获取账户信息
   * @returns 账户信息
   */
  async getAccount(): Promise<Account> {
    try {
      // 先从缓存获取
      if (this.accountCache && this.isCacheValid()) {
        return this.accountCache
      }

      const response = await http.get<{ data: Account }>('/trading/account')
      
      if (response.data) {
        // 更新缓存
        this.accountCache = response.data
        this.lastUpdateTime = Date.now()
        
        return response.data
      } else {
        throw new Error('获取账户信息失败')
      }
    } catch (error) {
      console.error('获取账户信息失败:', error)
      throw error
    }
  }

  /**
   * 获取交易记录
   * @param params 查询参数
   * @returns 交易记录
   */
  async getTradeRecords(params?: {
    symbol?: string
    startDate?: string
    endDate?: string
    page?: number
    limit?: number
  }): Promise<{ records: TradeRecord[]; total: number }> {
    try {
      const response = await http.get<{ 
        data: { records: TradeRecord[]; total: number } 
      }>('/trading/trades', { params })
      
      if (response.data) {
        return response.data
      } else {
        throw new Error('获取交易记录失败')
      }
    } catch (error) {
      console.error('获取交易记录失败:', error)
      throw error
    }
  }

  /**
   * 获取投资组合汇总
   * @returns 投资组合汇总
   */
  async getPortfolioSummary(): Promise<PortfolioSummary> {
    try {
      const response = await http.get<{ data: PortfolioSummary }>('/trading/portfolio/summary')
      
      if (response.data) {
        return response.data
      } else {
        throw new Error('获取投资组合汇总失败')
      }
    } catch (error) {
      console.error('获取投资组合汇总失败:', error)
      throw error
    }
  }

  /**
   * 计算风险指标
   * @param positions 持仓列表
   * @param account 账户信息
   * @returns 风险指标
   */
  calculateRiskMetrics(positions: Position[], account: Account): RiskMetrics {
    const totalMarketValue = positions.reduce((sum, pos) => 
      new Decimal(sum).plus(pos.marketValue).toNumber(), 0
    )
    
    const totalCost = positions.reduce((sum, pos) => 
      new Decimal(sum).plus(pos.totalCost).toNumber(), 0
    )
    
    const totalUnrealizedPnl = positions.reduce((sum, pos) => 
      new Decimal(sum).plus(pos.unrealizedPnl).toNumber(), 0
    )
    
    // 计算集中度风险
    const concentrationRisk = this.calculateConcentrationRisk(positions, totalMarketValue)
    
    // 计算行业分布
    const sectorDistribution = this.calculateSectorDistribution(positions, totalMarketValue)
    
    // 计算VaR (简化版本)
    const var95 = this.calculateVaR(positions, 0.95)
    const var99 = this.calculateVaR(positions, 0.99)
    
    return {
      totalMarketValue,
      totalCost,
      totalUnrealizedPnl,
      totalUnrealizedPnlPercent: totalCost > 0 ? 
        new Decimal(totalUnrealizedPnl).div(totalCost).mul(100).toNumber() : 0,
      concentrationRisk,
      sectorDistribution,
      var95,
      var99,
      maxDrawdown: 0, // 需要历史数据计算
      sharpeRatio: 0, // 需要历史收益率数据计算
      beta: 0, // 需要市场数据计算
      leverage: new Decimal(totalMarketValue).div(account.totalAssets).toNumber()
    }
  }

  /**
   * 计算手续费
   * @param orderData 订单数据
   * @returns 手续费信息
   */
  calculateFees(orderData: OrderFormData): {
    commission: number
    stampTax: number
    transferFee: number
    totalFee: number
  } {
    const amount = new Decimal(orderData.price).mul(orderData.quantity)
    
    // 佣金 (最低5元)
    const commissionRate = 0.0003 // 万分之三
    const commission = Math.max(amount.mul(commissionRate).toNumber(), 5)
    
    // 印花税 (卖出时收取)
    const stampTaxRate = 0.001 // 千分之一
    const stampTax = orderData.side === 'sell' ? 
      amount.mul(stampTaxRate).toNumber() : 0
    
    // 过户费
    const transferFeeRate = 0.00002 // 万分之0.2
    const transferFee = amount.mul(transferFeeRate).toNumber()
    
    const totalFee = new Decimal(commission)
      .plus(stampTax)
      .plus(transferFee)
      .toNumber()
    
    return {
      commission,
      stampTax,
      transferFee,
      totalFee
    }
  }

  /**
   * 验证订单
   * @param orderData 订单数据
   */
  private async validateOrder(orderData: OrderFormData): Promise<void> {
    // 获取账户信息
    const account = await this.getAccount()
    
    // 买入时检查资金
    if (orderData.side === 'buy') {
      const amount = new Decimal(orderData.price).mul(orderData.quantity)
      const fees = this.calculateFees(orderData)
      const totalCost = amount.plus(fees.totalFee)
      
      if (totalCost.toNumber() > account.availableCash) {
        throw new Error('可用资金不足')
      }
    }
    
    // 卖出时检查持仓
    if (orderData.side === 'sell') {
      const position = await this.getPosition(orderData.symbol)
      
      if (!position) {
        throw new Error('没有该股票的持仓')
      }
      
      if (orderData.quantity > position.availableQuantity) {
        throw new Error('可卖数量不足')
      }
    }
    
    // 检查交易时间
    if (!this.isMarketOpen()) {
      throw new Error('当前不在交易时间')
    }
    
    // 检查涨跌停限制
    await this.checkPriceLimits(orderData)
  }

  /**
   * 检查市场是否开放
   * @returns 是否开放
   */
  private isMarketOpen(): boolean {
    const now = new Date()
    const hour = now.getHours()
    const minute = now.getMinutes()
    const dayOfWeek = now.getDay()
    
    // 周末不开市
    if (dayOfWeek === 0 || dayOfWeek === 6) {
      return false
    }
    
    // 简化的交易时间检查 (9:30-11:30, 13:00-15:00)
    const morningStart = 9 * 60 + 30
    const morningEnd = 11 * 60 + 30
    const afternoonStart = 13 * 60
    const afternoonEnd = 15 * 60
    
    const currentTime = hour * 60 + minute
    
    return (currentTime >= morningStart && currentTime <= morningEnd) ||
           (currentTime >= afternoonStart && currentTime <= afternoonEnd)
  }

  /**
   * 计算集中度风险
   */
  private calculateConcentrationRisk(positions: Position[], totalValue: number): {
    topHolding: number
    top5Holdings: number
    top10Holdings: number
  } {
    if (totalValue === 0) {
      return { topHolding: 0, top5Holdings: 0, top10Holdings: 0 }
    }
    
    const sortedPositions = positions
      .sort((a, b) => b.marketValue - a.marketValue)
    
    const topHolding = sortedPositions.length > 0 ? 
      new Decimal(sortedPositions[0].marketValue).div(totalValue).mul(100).toNumber() : 0
    
    const top5Value = sortedPositions
      .slice(0, 5)
      .reduce((sum, pos) => new Decimal(sum).plus(pos.marketValue).toNumber(), 0)
    const top5Holdings = new Decimal(top5Value).div(totalValue).mul(100).toNumber()
    
    const top10Value = sortedPositions
      .slice(0, 10)
      .reduce((sum, pos) => new Decimal(sum).plus(pos.marketValue).toNumber(), 0)
    const top10Holdings = new Decimal(top10Value).div(totalValue).mul(100).toNumber()
    
    return { topHolding, top5Holdings, top10Holdings }
  }

  /**
   * 计算行业分布
   */
  private calculateSectorDistribution(positions: Position[], totalValue: number): {
    [sector: string]: number
  } {
    const distribution: { [sector: string]: number } = {}
    
    if (totalValue === 0) return distribution
    
    positions.forEach(position => {
      const sector = position.sector || '其他'
      const weight = new Decimal(position.marketValue).div(totalValue).mul(100).toNumber()
      
      distribution[sector] = (distribution[sector] || 0) + weight
    })
    
    return distribution
  }

  /**
   * 计算VaR (简化版本)
   */
  private calculateVaR(positions: Position[], confidence: number): number {
    // 这里使用简化的VaR计算，实际应该基于历史收益率分布
    const totalValue = positions.reduce((sum, pos) => 
      new Decimal(sum).plus(pos.marketValue).toNumber(), 0
    )
    
    // 假设日收益率标准差为2%
    const dailyVolatility = 0.02
    
    // 根据置信度获取分位数 (简化)
    const zScore = confidence === 0.95 ? 1.645 : 2.326
    
    return new Decimal(totalValue).mul(dailyVolatility).mul(zScore).toNumber()
  }

  /**
   * 检查缓存是否有效
   */
  private isCacheValid(): boolean {
    const now = Date.now()
    const maxAge = 30000 // 30秒缓存
    
    return now - this.lastUpdateTime < maxAge
  }

  /**
   * 清除缓存
   */
  clearCache(): void {
    this.ordersCache.clear()
    this.positionsCache.clear()
    this.accountCache = null
    this.lastUpdateTime = 0
  }

  /**
   * 获取缓存的订单
   */
  getCachedOrders(): Order[] {
    return Array.from(this.ordersCache.values())
  }

  /**
   * 获取缓存的持仓
   */
  getCachedPositions(): Position[] {
    return Array.from(this.positionsCache.values())
  }

  /**
   * 根据股票代码获取持仓
   */
  getCachedPositionBySymbol(symbol: string): Position | null {
    return this.positionsCache.get(symbol) || null
  }
}

// 导出单例实例
export const tradingService = TradingService.getInstance()
export default tradingService 