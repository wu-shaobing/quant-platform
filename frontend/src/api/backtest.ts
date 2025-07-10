import { httpClient } from './http'
import type { 
  ApiResponse, 
  ListResponse, 
  BacktestData, 
  QueryParams 
} from '@/types/api'
import type { 
  Backtest,
  BacktestConfig, 
  BacktestResult, 
  BacktestReport,
  BacktestProgress,
  OptimizationResult,
  Strategy
} from '@/types/backtest'
import type { PaginationRequest, PaginationResponse } from '@/types'

const BASE_URL = '/backtest'

export interface BacktestCreateRequest {
  name: string
  strategyId: string
  symbol: string
  startDate: string
  endDate: string
  initialCash: number
  parameters?: Record<string, any>
}

export interface BacktestUpdateRequest {
  name?: string
  isFavorite?: boolean
}

/**
 * 回测相关API接口
 */
export const backtestApi = {
  // ============ 回测管理 ============
  
  /**
   * 获取回测列表
   */
  getBacktests: async (params?: QueryParams): Promise<ListResponse<BacktestData>> => {
    const endpoint = import.meta.env.DEV ? '/backtest/mock' : '/backtest'
    const response = await httpClient.get(endpoint, { params })
    return (response.data as any).data ?? response.data
  },

  /**
   * 获取回测详情
   */
  getBacktest: async (id: string): Promise<ApiResponse<BacktestData>> => {
    const response = await httpClient.get<BacktestData>(`/backtest/${id}`)
    return response.data
  },

  /**
   * 创建回测
   */
  createBacktest: async (data: BacktestCreateRequest): Promise<ApiResponse<BacktestData>> => {
    const response = await httpClient.post<BacktestData>('/backtest', data)
    return response.data
  },

  /**
   * 更新回测
   */
  updateBacktest: async (
    id: string, 
    data: BacktestUpdateRequest
  ): Promise<ApiResponse<BacktestData>> => {
    const response = await httpClient.put<BacktestData>(`/backtest/${id}`, data)
    return response.data
  },

  /**
   * 删除回测
   */
  deleteBacktest: async (id: string): Promise<ApiResponse<void>> => {
    const response = await httpClient.delete<void>(`/backtest/${id}`)
    return response.data
  },

  // ============ 回测执行控制 ============

  /**
   * 启动回测
   */
  startBacktest: async (id: string): Promise<ApiResponse<BacktestData>> => {
    const response = await httpClient.post<BacktestData>(`/backtest/${id}/start`)
    return response.data
  },

  /**
   * 停止回测
   */
  stopBacktest: async (id: string): Promise<ApiResponse<BacktestData>> => {
    const response = await httpClient.post<BacktestData>(`/backtest/${id}/stop`)
    return response.data
  },

  /**
   * 获取回测状态
   */
  async getBacktestStatus(id: string) {
    const response = await httpClient.get(`${BASE_URL}/${id}/status`)
    return response.data
  },

  /**
   * 获取回测进度
   */
  async getBacktestProgress(id: string): Promise<BacktestProgress> {
    const response = await httpClient.get(`${BASE_URL}/${id}/progress`)
    return response.data
  },

  // ============ 回测结果分析 ============

  /**
   * 获取回测结果
   */
  getBacktestResults: async (id: string): Promise<ApiResponse<any>> => {
    const response = await httpClient.get<any>(`/backtest/${id}/results`)
    return response.data
  },

  /**
   * 获取回测图表数据
   */
  getBacktestChartData: async (id: string): Promise<ApiResponse<any>> => {
    const response = await httpClient.get<any>(`/backtest/${id}/chart`)
    return response.data
  },

  /**
   * 获取回测报告
   */
  async getBacktestReport(id: string): Promise<BacktestReport> {
    const response = await httpClient.get(`${BASE_URL}/${id}/report`)
    return response.data
  },

  /**
   * 获取回测绩效指标
   */
  async getBacktestMetrics(id: string) {
    const response = await httpClient.get(`${BASE_URL}/${id}/metrics`)
    return response.data
  },

  /**
   * 获取回测净值曲线
   */
  async getBacktestEquityCurve(id: string, period?: 'daily' | 'weekly' | 'monthly') {
    const response = await httpClient.get(`${BASE_URL}/${id}/equity-curve`, {
      params: { period }
    })
    return response.data
  },

  /**
   * 获取回测收益统计
   */
  async getBacktestReturns(id: string) {
    const response = await httpClient.get(`${BASE_URL}/${id}/returns`)
    return response.data
  },

  /**
   * 获取回测风险指标
   */
  async getBacktestRiskMetrics(id: string) {
    const response = await httpClient.get(`${BASE_URL}/${id}/risk-metrics`)
    return response.data
  },

  // ============ 回测交易记录 ============

  /**
   * 获取回测交易记录
   */
  async getBacktestTrades(id: string, params?: {
    page?: number
    pageSize?: number
    symbol?: string
    startDate?: string
    endDate?: string
  }) {
    const response = await httpClient.get(`${BASE_URL}/${id}/trades`, { params })
    return response.data
  },

  /**
   * 获取回测持仓记录
   */
  async getBacktestPositions(id: string, date?: string) {
    const response = await httpClient.get(`${BASE_URL}/${id}/positions`, {
      params: { date }
    })
    return response.data
  },

  /**
   * 获取回测资金变动
   */
  async getBacktestCashFlow(id: string) {
    const response = await httpClient.get(`${BASE_URL}/${id}/cash-flow`)
    return response.data
  },

  // ============ 回测对比分析 ============

  /**
   * 比较多个回测结果
   */
  async compareBacktests(ids: string[]) {
    const response = await httpClient.post(`${BASE_URL}/compare`, { ids })
    return response.data
  },

  /**
   * 获取基准对比
   */
  async getBenchmarkComparison(id: string, benchmark: string) {
    const response = await httpClient.get(`${BASE_URL}/${id}/benchmark`, {
      params: { benchmark }
    })
    return response.data
  },

  // ============ 回测配置模板 ============

  /**
   * 获取回测配置模板
   */
  async getBacktestTemplates() {
    const response = await httpClient.get('/backtest-templates')
    return response.data
  },

  /**
   * 保存回测配置为模板
   */
  async saveBacktestTemplate(config: BacktestConfig, name: string) {
    const response = await httpClient.post('/backtest-templates', {
      name,
      config
    })
    return response.data
  },

  /**
   * 从模板创建回测
   */
  async createFromTemplate(templateId: string, overrides?: Partial<BacktestConfig>) {
    const response = await httpClient.post(`/backtest-templates/${templateId}/create`, overrides)
    return response.data
  },

  // ============ 策略优化 ============

  /**
   * 策略优化
   */
  optimizeStrategy(config: BacktestConfig): Promise<OptimizationResult> {
    return httpClient.post(`${BASE_URL}/optimize`, config)
  },

  /**
   * 获取策略列表
   */
  getStrategies(): Promise<Strategy[]> {
    return httpClient.get(`${BASE_URL}/strategies`)
  },

  // ============ 克隆回测 ============

  /**
   * 克隆回测
   */
  cloneBacktest: async (id: string): Promise<ApiResponse<BacktestData>> => {
    const response = await httpClient.post<BacktestData>(`/backtest/${id}/clone`)
    return response.data
  },

  // ============ 导出回测报告 ============

  /**
   * 导出回测报告
   */
  exportBacktestReport: async (id: string, format: 'pdf' | 'excel' = 'pdf'): Promise<void> => {
    const response = await httpClient.get(`/backtest/${id}/export`, {
      params: { format },
      responseType: 'blob'
    })
    
    // 创建下载链接
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `backtest-report-${id}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }
}

export default backtestApi









