import { httpClient } from './http'
import type { 
  ApiResponse, 
  ListResponse, 
  OrderData, 
  TradeData, 
  PositionData, 
  AccountData,
  QueryParams 
} from '@/types/api'

// 开发环境标识
const isDev = import.meta.env.DEV

export interface OrderCreateRequest {
  symbol: string
  side: 'buy' | 'sell'
  orderType: 'market' | 'limit' | 'stop' | 'stop_limit'
  quantity: number
  price?: number
  stopPrice?: number
  timeInForce?: 'GTC' | 'IOC' | 'FOK' | 'DAY'
  clientOrderId?: string
}

export interface OrderUpdateRequest {
  quantity?: number
  price?: number
  stopPrice?: number
}

export interface PositionCloseRequest {
  symbol: string
  quantity?: number  // 不传表示全部平仓
  price?: number     // 限价平仓价格
}

// ============ 订单管理 ============

// 获取订单列表
export const getOrders = async (params?: QueryParams): Promise<ListResponse<OrderData>> => {
  const endpoint = isDev ? '/trading/mock/orders' : '/trading/orders'
  const response = await httpClient.get(endpoint, { params })
  // 统一解包，返回真实列表数据（后端格式：{ success, message, data, total, ... }）
  return (response.data as any).data
}

// 获取订单详情
export const getOrder = async (orderId: string): Promise<ApiResponse<OrderData>> => {
  const response = await httpClient.get<OrderData>(`/trading/orders/${orderId}`)
  return response.data
}

// 创建订单
export const createOrder = async (data: OrderCreateRequest): Promise<ApiResponse<OrderData>> => {
  const response = await httpClient.post<OrderData>('/trading/orders', data)
  return response.data
}

// 修改订单
export const updateOrder = async (
  orderId: string, 
  data: OrderUpdateRequest
): Promise<ApiResponse<OrderData>> => {
  const response = await httpClient.put<OrderData>(`/trading/orders/${orderId}`, data)
  return response.data
}

// 取消订单
export const cancelOrder = async (orderId: string): Promise<ApiResponse<void>> => {
  const response = await httpClient.delete<void>(`/trading/orders/${orderId}`)
  return response.data
}

// 批量取消订单
export const cancelOrders = async (orderIds: string[]): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/trading/orders/cancel-batch', { orderIds })
  return response.data
}

// 取消所有订单
export const cancelAllOrders = async (symbol?: string): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/trading/orders/cancel-all', { symbol })
  return response.data
}

// ============ 成交记录 ============

// 获取成交记录
export const getTrades = async (params?: QueryParams): Promise<ListResponse<TradeData>> => {
  const endpoint = isDev ? '/trading/mock/trades' : '/trading/trades'
  const response = await httpClient.get(endpoint, { params })
  return (response.data as any).data
}

// 获取成交详情
export const getTrade = async (tradeId: string): Promise<ApiResponse<TradeData>> => {
  const response = await httpClient.get<TradeData>(`/trading/trades/${tradeId}`)
  return response.data
}

// ============ 持仓管理 ============

// 获取持仓列表
export const getPositions = async (params?: QueryParams): Promise<ListResponse<PositionData>> => {
  const endpoint = isDev ? '/trading/mock/positions' : '/trading/positions'
  const response = await httpClient.get(endpoint, { params })
  return (response.data as any).data
}

// 获取持仓详情
export const getPosition = async (symbol: string): Promise<ApiResponse<PositionData>> => {
  const response = await httpClient.get<PositionData>(`/trading/positions/${symbol}`)
  return response.data
}

// 平仓
export const closePosition = async (data: PositionCloseRequest): Promise<ApiResponse<OrderData>> => {
  const response = await httpClient.post<OrderData>('/trading/positions/close', data)
  return response.data
}

// 全部平仓
export const closeAllPositions = async (): Promise<ApiResponse<OrderData[]>> => {
  const response = await httpClient.post<OrderData[]>('/trading/positions/close-all')
  return response.data
}

// ============ 账户信息 ============

// 获取账户信息
export const getAccount = async (): Promise<AccountData> => {
  const endpoint = isDev ? '/trading/mock/account' : '/trading/account'
  const response = await httpClient.get(endpoint)
  return (response.data as any).data
}

// 获取账户历史
export const getAccountHistory = async (params?: QueryParams): Promise<ListResponse<any>> => {
  const response = await httpClient.get<any[]>('/trading/account/history', { params })
  return response.data
}

// 获取资金流水
export const getCashFlow = async (params?: QueryParams): Promise<ListResponse<any>> => {
  const response = await httpClient.get<any[]>('/trading/account/cash-flow', { params })
  return response.data
}

// ============ 风险管理 ============

// 获取风险指标
export const getRiskMetrics = async (): Promise<ApiResponse<any>> => {
  const response = await httpClient.get<any>('/trading/risk/metrics')
  return response.data
}

// 设置止损
export const setStopLoss = async (
  symbol: string, 
  stopPrice: number, 
  quantity?: number
): Promise<ApiResponse<OrderData>> => {
  const response = await httpClient.post<OrderData>('/trading/risk/stop-loss', {
    symbol,
    stopPrice,
    quantity
  })
  return response.data
}

// 设置止盈
export const setTakeProfit = async (
  symbol: string, 
  takeProfitPrice: number, 
  quantity?: number
): Promise<ApiResponse<OrderData>> => {
  const response = await httpClient.post<OrderData>('/trading/risk/take-profit', {
    symbol,
    takeProfitPrice,
    quantity
  })
  return response.data
}

// ============ 交易统计 ============

// 获取交易统计
export const getTradingStats = async (
  startDate?: string, 
  endDate?: string
): Promise<ApiResponse<any>> => {
  const response = await httpClient.get<any>('/trading/stats', {
    params: { startDate, endDate }
  })
  return response.data
}

// 获取收益分析
export const getPnLAnalysis = async (
  startDate?: string, 
  endDate?: string
): Promise<ApiResponse<any>> => {
  const response = await httpClient.get<any>('/trading/pnl-analysis', {
    params: { startDate, endDate }
  })
  return response.data
}

// 获取交易报告
export const getTradingReport = async (
  startDate: string, 
  endDate: string
): Promise<ApiResponse<any>> => {
  const response = await httpClient.get<any>('/trading/report', {
    params: { startDate, endDate }
  })
  return response.data
}

// ============ 市价单快捷操作 ============

// 市价买入
export const marketBuy = async (symbol: string, quantity: number): Promise<ApiResponse<OrderData>> => {
  return createOrder({
    symbol,
    side: 'buy',
    orderType: 'market',
    quantity
  })
}

// 市价卖出
export const marketSell = async (symbol: string, quantity: number): Promise<ApiResponse<OrderData>> => {
  return createOrder({
    symbol,
    side: 'sell',
    orderType: 'market',
    quantity
  })
}

// 限价买入
export const limitBuy = async (
  symbol: string, 
  quantity: number, 
  price: number
): Promise<ApiResponse<OrderData>> => {
  return createOrder({
    symbol,
    side: 'buy',
    orderType: 'limit',
    quantity,
    price
  })
}

// 限价卖出
export const limitSell = async (
  symbol: string, 
  quantity: number, 
  price: number
): Promise<ApiResponse<OrderData>> => {
  return createOrder({
    symbol,
    side: 'sell',
    orderType: 'limit',
    quantity,
    price
  })
}

// ============ 交易权限和状态 ============

// 获取交易权限
export const getTradingPermissions = async (): Promise<ApiResponse<any>> => {
  const response = await httpClient.get<any>('/trading/permissions')
  return response.data
}

// 获取交易状态
export const getTradingStatus = async (): Promise<ApiResponse<any>> => {
  const response = await httpClient.get<any>('/trading/status')
  return response.data
}

// 启用交易
export const enableTrading = async (): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/trading/enable')
  return response.data
}

// 禁用交易
export const disableTrading = async (): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/trading/disable')
  return response.data
}

// 默认导出 - 将所有函数组合成一个对象
export default {
  // 订单管理
  getOrders,
  getOrder,
  createOrder,
  updateOrder,
  cancelOrder,
  cancelOrders,
  cancelAllOrders,
  
  // 成交记录
  getTrades,
  getTrade,
  
  // 持仓管理
  getPositions,
  getPosition,
  closePosition,
  closeAllPositions,
  
  // 账户信息
  getAccount,
  getAccountHistory,
  getCashFlow,
  
  // 风险管理
  getRiskMetrics,
  setStopLoss,
  setTakeProfit,
  
  // 交易统计
  getTradingStats,
  getPnLAnalysis,
  getTradingReport,
  
  // 快捷操作
  marketBuy,
  marketSell,
  limitBuy,
  limitSell,
  
  // 交易权限和状态
  getTradingPermissions,
  getTradingStatus,
  enableTrading,
  disableTrading
}
