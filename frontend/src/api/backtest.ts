import { http } from './http'
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

/**
 * 回测相关API接口
 */
export const backtestApi = {
  // ============ 回测管理 ============
  
  /**
   * 获取回测列表
   */
  getBacktests(params: PaginationRequest): Promise<PaginationResponse<BacktestResult>> {
    return http.get(`${BASE_URL}/list`, { params })
  },

  /**
   * 获取回测详情
   */
  getBacktest(id: string): Promise<BacktestResult> {
    return http.get(`${BASE_URL}/${id}`)
  },

  /**
   * 创建回测
   */
  createBacktest(config: BacktestConfig): Promise<BacktestResult> {
    return http.post(`${BASE_URL}/create`, config)
  },

  /**
   * 运行回测
   */
  async runBacktest(id: string): Promise<Backtest> {
    const response = await http.post(`${BASE_URL}/${id}/run`)
    return response.data
  },

  /**
   * 取消回测
   */
  async cancelBacktest(id: string): Promise<void> {
    await http.post(`${BASE_URL}/${id}/cancel`)
  },

  /**
   * 删除回测
   */
  deleteBacktest(id: string): Promise<void> {
    return http.delete(`${BASE_URL}/${id}`)
  },

  // ============ 回测执行控制 ============

  /**
   * 启动回测 (别名，兼容旧API)
   */
  async startBacktest(id: string) {
    return this.runBacktest(id)
  },

  /**
   * 停止回测 (别名，兼容旧API)
   */
  async stopBacktest(id: string) {
    return this.cancelBacktest(id)
  },

  /**
   * 获取回测状态
   */
  async getBacktestStatus(id: string) {
    const response = await http.get(`${BASE_URL}/${id}/status`)
    return response.data
  },

  /**
   * 获取回测进度
   */
  async getBacktestProgress(id: string): Promise<BacktestProgress> {
    const response = await http.get(`${BASE_URL}/${id}/progress`)
    return response.data
  },

  // ============ 回测结果分析 ============

  /**
   * 获取回测结果
   */
  async getBacktestResult(id: string): Promise<BacktestResult> {
    const response = await http.get(`${BASE_URL}/${id}/result`)
    return response.data
  },

  /**
   * 获取回测报告
   */
  getBacktestReport(id: string): Promise<BacktestReport> {
    return http.get(`${BASE_URL}/${id}/report`)
  },

  /**
   * 获取回测绩效指标
   */
  async getBacktestMetrics(id: string) {
    const response = await http.get(`${BASE_URL}/${id}/metrics`)
    return response.data
  },

  /**
   * 获取回测净值曲线
   */
  async getBacktestEquityCurve(id: string, period?: 'daily' | 'weekly' | 'monthly') {
    const response = await http.get(`${BASE_URL}/${id}/equity-curve`, {
      params: { period }
    })
    return response.data
  },

  /**
   * 获取回测收益统计
   */
  async getBacktestReturns(id: string) {
    const response = await http.get(`${BASE_URL}/${id}/returns`)
    return response.data
  },

  /**
   * 获取回测风险指标
   */
  async getBacktestRiskMetrics(id: string) {
    const response = await http.get(`${BASE_URL}/${id}/risk-metrics`)
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
    const response = await http.get(`${BASE_URL}/${id}/trades`, { params })
    return response.data
  },

  /**
   * 获取回测持仓记录
   */
  async getBacktestPositions(id: string, date?: string) {
    const response = await http.get(`${BASE_URL}/${id}/positions`, {
      params: { date }
    })
    return response.data
  },

  /**
   * 获取回测资金变动
   */
  async getBacktestCashFlow(id: string) {
    const response = await http.get(`${BASE_URL}/${id}/cash-flow`)
    return response.data
  },

  // ============ 回测对比分析 ============

  /**
   * 比较多个回测结果
   */
  async compareBacktests(ids: string[]) {
    const response = await http.post(`${BASE_URL}/compare`, { ids })
    return response.data
  },

  /**
   * 获取基准对比
   */
  async getBenchmarkComparison(id: string, benchmark: string) {
    const response = await http.get(`${BASE_URL}/${id}/benchmark`, {
      params: { benchmark }
    })
    return response.data
  },

  // ============ 回测配置模板 ============

  /**
   * 获取回测配置模板
   */
  async getBacktestTemplates() {
    const response = await http.get('/backtest-templates')
    return response.data
  },

  /**
   * 保存回测配置为模板
   */
  async saveBacktestTemplate(config: BacktestConfig, name: string) {
    const response = await http.post('/backtest-templates', {
      name,
      config
    })
    return response.data
  },

  /**
   * 从模板创建回测
   */
  async createFromTemplate(templateId: string, overrides?: Partial<BacktestConfig>) {
    const response = await http.post(`/backtest-templates/${templateId}/create`, overrides)
    return response.data
  },

  // ============ 策略优化 ============

  /**
   * 策略优化
   */
  optimizeStrategy(config: BacktestConfig): Promise<OptimizationResult> {
    return http.post(`${BASE_URL}/optimize`, config)
  },

  /**
   * 获取策略列表
   */
  getStrategies(): Promise<Strategy[]> {
    return http.get(`${BASE_URL}/strategies`)
  }
}

export default backtestApi









