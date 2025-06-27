import { http } from './http'
import type { 
  Order, 
  Position, 
  Trade, 
  Account, 
  OrderSubmitData,
  OrderCancelData,
  OrderModifyData,
  TradingStats
} from '@/types/trading'
import type { PaginationRequest, PaginationResponse } from '@/types'

const BASE_URL = '/trading'

/**
 * 交易相关API
 */
export const tradingApi = {
  /**
   * 获取账户信息
   */
  getAccount(): Promise<Account> {
    return http.get(`${BASE_URL}/account`)
  },

  /**
   * 获取持仓列表
   * @param params - 过滤参数
   */
  getPositions(params?: { symbol?: string; side?: 'long' | 'short' }): Promise<Position[]> {
    return http.get(`${BASE_URL}/positions`, { params })
  },
  
  /**
   * 获取订单列表
   * @param params - 分页和过滤参数
   */
  getOrders(params?: PaginationRequest & { status?: string; symbol?: string }): Promise<PaginationResponse<Order>> {
    return http.get(`${BASE_URL}/orders`, { params })
  },
  
  /**
   * 获取单个订单详情
   * @param orderId - 订单ID
   */
  getOrderDetails(orderId: string): Promise<Order> {
    return http.get(`${BASE_URL}/orders/${orderId}`)
  },
  
  /**
   * 提交新订单
   * @param orderData - 订单数据
   */
  submitOrder(orderData: OrderSubmitData): Promise<Order> {
    return http.post(`${BASE_URL}/orders`, orderData)
  },

  /**
   * 取消订单
   * @param cancelData - { orderId }
   */
  cancelOrder(cancelData: OrderCancelData): Promise<{ orderId: string; success: boolean }> {
    return http.post(`${BASE_URL}/orders/cancel`, cancelData)
  },
  
  /**
   * 修改订单
   * @param modifyData - 修改的订单数据
   */
  modifyOrder(modifyData: OrderModifyData): Promise<Order> {
    return http.put(`${BASE_URL}/orders/${modifyData.orderId}`, modifyData)
  },
  
  /**
   * 获取成交记录
   * @param params - 分页和过滤参数
   */
  getTrades(params?: PaginationRequest & { symbol?: string; from?: string; to?: string }): Promise<PaginationResponse<Trade>> {
    return http.get(`${BASE_URL}/trades`, { params })
  },
  
  /**
   * 获取交易统计
   */
  getTradingStats(): Promise<TradingStats> {
    return http.get(`${BASE_URL}/stats`)
  },

  getQuote: () => { throw new Error('Method not implemented') },
  getTicks: () => { throw new Error('Method not implemented') },
  getRiskWarnings: () => { throw new Error('Method not implemented') },
  getCashFlows: () => { throw new Error('Method not implemented') },
  getTradingRules: () => { throw new Error('Method not implemented') },
  getQuickTradeConfig: () => { throw new Error('Method not implemented') },
  updateQuickTradeConfig: () => { throw new Error('Method not implemented') }
}

// 设置默认导出
export default tradingApi
