import { http } from './http'
import type { 
  Strategy, 
  StrategyInstance,
  StrategySignal,
  BacktestConfig,
  BacktestResult,
  StrategyStatus,
  StrategyType
} from '@/types/strategy'
import type { PaginationRequest, PaginationResponse } from '@/types'

const BASE_URL = '/strategy'

/**
 * 策略相关API接口
 */
export const strategyApi = {
  // ============ 策略管理 ============
  
  /**
   * 获取策略列表
   */
  async getStrategies(params?: {
    page?: number
    pageSize?: number
    status?: StrategyStatus
    type?: StrategyType
    keyword?: string
  }) {
    const response = await http.get('/strategies', { params })
    return response.data
  },
  
  /**
   * 获取单个策略详情
   * @param id - 策略ID
   */
  getStrategyById(id: string): Promise<Strategy> {
    return http.get(`${BASE_URL}/${id}`)
  },
  
  /**
   * 创建新策略
   * @param strategyData - 策略数据
   */
  createStrategy(strategyData: Partial<Strategy>): Promise<Strategy> {
    return http.post(`${BASE_URL}`, strategyData)
  },
  
  /**
   * 更新策略
   * @param id - 策略ID
   * @param strategyData - 更新的策略数据
   */
  updateStrategy(id: string, strategyData: Partial<Strategy>): Promise<Strategy> {
    return http.put(`${BASE_URL}/${id}`, strategyData)
  },
  
  /**
   * 删除策略
   * @param id - 策略ID
   */
  deleteStrategy(id: string): Promise<void> {
    return http.delete(`${BASE_URL}/${id}`)
  },
  
  // ============ 策略运行管理 ============
  
  /**
   * 启动策略
   * @param id - 策略ID
   * @param config - 运行配置
   */
  async startStrategy(id: string, config?: any): Promise<StrategyInstance> {
    const response = await http.post(`${BASE_URL}/${id}/start`, config)
    return response.data
  },

  /**
   * 停止策略
   * @param instanceId - 策略实例ID
   */
  async stopStrategy(instanceId: string): Promise<void> {
    await http.post(`${BASE_URL}/instances/${instanceId}/stop`)
  },

  /**
   * 暂停策略
   * @param instanceId - 策略实例ID
   */
  async pauseStrategy(instanceId: string): Promise<StrategyInstance> {
    const response = await http.post(`${BASE_URL}/instances/${instanceId}/pause`)
    return response.data
  },

  /**
   * 恢复策略
   * @param instanceId - 策略实例ID
   */
  async resumeStrategy(instanceId: string): Promise<StrategyInstance> {
    const response = await http.post(`${BASE_URL}/instances/${instanceId}/resume`)
    return response.data
  },

  /**
   * 获取策略实例列表
   */
  async getStrategyInstances(params?: {
    strategyId?: string
    status?: StrategyStatus
  }): Promise<StrategyInstance[]> {
    const response = await http.get(`${BASE_URL}/instances`, { params })
    return response.data
  },

  /**
   * 获取策略信号
   */
  async getStrategySignals(params?: {
    strategyInstanceId?: string
    symbol?: string
    limit?: number
  }): Promise<StrategySignal[]> {
    const response = await http.get(`${BASE_URL}/signals`, { params })
    return response.data
  },
  
  // ============ 回测管理 ============
  
  /**
   * 运行回测
   * @param config - 回测配置
   */
  async runBacktest(config: BacktestConfig): Promise<BacktestResult> {
    const response = await http.post(`${BASE_URL}/backtest/run`, config)
    return response.data
  },
  
  /**
   * 获取回测历史
   */
  async getBacktestHistory(params?: PaginationRequest): Promise<PaginationResponse<BacktestResult>> {
    const response = await http.get(`${BASE_URL}/backtest/history`, { params })
    return response.data
  },
  
  /**
   * 获取回测结果详情
   * @param id - 回测ID
   */
  getBacktestResult(id: string): Promise<BacktestResult> {
    return http.get(`${BASE_URL}/backtest/${id}`)
  },

  /**
   * 取消回测
   * @param id - 回测ID
   */
  async cancelBacktest(id: string): Promise<void> {
    await http.post(`${BASE_URL}/backtest/${id}/cancel`)
  },

  /**
   * 删除回测
   * @param id - 回测ID
   */
  async deleteBacktest(id: string): Promise<void> {
    await http.delete(`${BASE_URL}/backtest/${id}`)
  }
}

export default strategyApi


