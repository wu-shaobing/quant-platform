import { httpClient } from './http'
import type { 
  ApiResponse, 
  ListResponse, 
  StrategyData, 
  QueryParams 
} from '@/types/api'
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
import { API_PATHS } from '@/utils/constants'

/**
 * 策略相关API接口
 */
export const strategyApi = {
  // ============ 策略管理 ============
  
  /**
   * 获取策略列表
   */
  async getStrategies(params?: QueryParams): Promise<ListResponse<StrategyData>> {
    const response = await httpClient.get<StrategyData[]>('/strategy', { params })
    return response.data
  },
  
  /**
   * 获取单个策略详情
   * @param id - 策略ID
   */
  async getStrategy(id: string): Promise<ApiResponse<StrategyData>> {
    const response = await httpClient.get<StrategyData>(`/strategy/${id}`)
    return response.data
  },
  
  /**
   * 创建新策略
   * @param strategyData - 策略数据
   */
  async createStrategy(data: StrategyCreateRequest): Promise<ApiResponse<StrategyData>> {
    const response = await httpClient.post<StrategyData>('/strategy', data)
    return response.data
  },
  
  /**
   * 更新策略
   * @param id - 策略ID
   * @param strategyData - 更新的策略数据
   */
  async updateStrategy(id: string, data: StrategyUpdateRequest): Promise<ApiResponse<StrategyData>> {
    const response = await httpClient.put<StrategyData>(`/strategy/${id}`, data)
    return response.data
  },
  
  /**
   * 删除策略
   * @param id - 策略ID
   */
  async deleteStrategy(id: string): Promise<ApiResponse<void>> {
    const response = await httpClient.delete<void>(`/strategy/${id}`)
    return response.data
  },
  
  // ============ 策略运行管理 ============
  
  /**
   * 启动策略
   * @param id - 策略ID
   * @param config - 运行配置
   */
  async startStrategy(id: string, data: StrategyRunRequest): Promise<ApiResponse<StrategyData>> {
    const response = await httpClient.post<StrategyData>(`/strategy/${id}/start`, data)
    return response.data
  },

  /**
   * 停止策略
   * @param instanceId - 策略实例ID
   */
  async stopStrategy(id: string): Promise<ApiResponse<StrategyData>> {
    const response = await httpClient.post<StrategyData>(`/strategy/${id}/stop`)
    return response.data
  },

  /**
   * 暂停策略
   * @param instanceId - 策略实例ID
   */
  async pauseStrategy(id: string): Promise<ApiResponse<StrategyData>> {
    const response = await httpClient.post<StrategyData>(`/strategy/${id}/pause`)
    return response.data
  },

  /**
   * 恢复策略
   * @param instanceId - 策略实例ID
   */
  async resumeStrategy(id: string): Promise<ApiResponse<StrategyData>> {
    const response = await httpClient.post<StrategyData>(`/strategy/${id}/resume`)
    return response.data
  },

  /**
   * 获取策略实例列表
   */
  async getStrategyInstances(params?: {
    strategyId?: string
    status?: StrategyStatus
  }): Promise<StrategyInstance[]> {
    const response = await httpClient.get(API_PATHS.STRATEGY.LIST, { params })
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
    const response = await httpClient.get(`${API_PATHS.STRATEGY.SIGNALS}`, { params })
    return response.data
  },
  
  // ============ 回测管理 ============
  
  /**
   * 运行回测
   * @param config - 回测配置
   */
  async runBacktest(config: BacktestConfig): Promise<BacktestResult> {
    const response = await httpClient.post(API_PATHS.BACKTEST.RUN, config)
    return response.data
  },
  
  /**
   * 获取回测历史
   */
  async getBacktestHistory(params?: PaginationRequest): Promise<PaginationResponse<BacktestResult>> {
    const response = await httpClient.get(API_PATHS.BACKTEST.HISTORY, { params })
    return response.data
  },
  
  /**
   * 获取回测结果详情
   * @param id - 回测ID
   */
  getBacktestResult(id: string): Promise<BacktestResult> {
    return httpClient.get(`${API_PATHS.BACKTEST.RESULT}/${id}`)
  },

  /**
   * 取消回测
   * @param id - 回测ID
   */
  async cancelBacktest(id: string): Promise<void> {
    await httpClient.post(`${API_PATHS.BACKTEST.RUN}/${id}/cancel`)
  },

  /**
   * 删除回测
   * @param id - 回测ID
   */
  async deleteBacktest(id: string): Promise<void> {
    await httpClient.delete(`${API_PATHS.BACKTEST.RESULT}/${id}`)
  },

  // ============ 其他策略相关操作 ============

  /**
   * 获取策略状态
   * @param id - 策略ID
   */
  async getStrategyStatus(id: string): Promise<ApiResponse<any>> {
    const response = await httpClient.get<any>(`/strategy/${id}/status`)
    return response.data
  },

  /**
   * 获取策略日志
   * @param id - 策略ID
   */
  async getStrategyLogs(id: string, params?: QueryParams): Promise<ListResponse<any>> {
    const response = await httpClient.get<any[]>(`/strategy/${id}/logs`, { params })
    return response.data
  },

  /**
   * 获取策略性能
   * @param id - 策略ID
   */
  async getStrategyPerformance(id: string): Promise<ApiResponse<any>> {
    const response = await httpClient.get<any>(`/strategy/${id}/performance`)
    return response.data
  },

  /**
   * 获取策略持仓
   * @param id - 策略ID
   */
  async getStrategyPositions(id: string): Promise<ApiResponse<any[]>> {
    const response = await httpClient.get<any[]>(`/strategy/${id}/positions`)
    return response.data
  },

  /**
   * 获取策略交易记录
   * @param id - 策略ID
   */
  async getStrategyTrades(id: string, params?: QueryParams): Promise<ListResponse<any>> {
    const response = await httpClient.get<any[]>(`/strategy/${id}/trades`, { params })
    return response.data
  },

  /**
   * 克隆策略
   * @param id - 策略ID
   */
  async cloneStrategy(id: string): Promise<ApiResponse<StrategyData>> {
    const response = await httpClient.post<StrategyData>(`/strategy/${id}/clone`)
    return response.data
  },

  /**
   * 验证策略代码
   * @param code - 策略代码
   */
  async validateStrategy(code: string): Promise<ApiResponse<any>> {
    const response = await httpClient.post<any>('/strategy/validate', { code })
    return response.data
  },

  /**
   * 获取策略模板
   */
  async getStrategyTemplates(): Promise<ApiResponse<any[]>> {
    const response = await httpClient.get<any[]>('/strategy/templates')
    return response.data
  },

  /**
   * 从模板创建策略
   * @param templateId - 模板ID
   * @param data - 策略数据
   */
  async createFromTemplate(templateId: string, data: Partial<StrategyCreateRequest>): Promise<ApiResponse<StrategyData>> {
    const response = await httpClient.post<StrategyData>(`/strategy/templates/${templateId}/create`, data)
    return response.data
  },

  /**
   * 获取策略分类
   */
  async getStrategyCategories(): Promise<ApiResponse<string[]>> {
    const response = await httpClient.get<string[]>('/strategy/categories')
    return response.data
  },

  /**
   * 获取策略标签
   */
  async getStrategyTags(): Promise<ApiResponse<string[]>> {
    const response = await httpClient.get<string[]>('/strategy/tags')
    return response.data
  },

  /**
   * 搜索策略
   * @param keyword - 关键词
   * @param filters - 过滤条件
   */
  async searchStrategies(keyword: string, filters?: Record<string, any>): Promise<ApiResponse<StrategyData[]>> {
    const response = await httpClient.get<StrategyData[]>('/strategy/search', {
      params: { q: keyword, ...filters }
    })
    return response.data
  },

  /**
   * 收藏策略
   * @param id - 策略ID
   */
  async favoriteStrategy(id: string): Promise<ApiResponse<void>> {
    const response = await httpClient.post<void>(`/strategy/${id}/favorite`)
    return response.data
  },

  /**
   * 取消收藏策略
   * @param id - 策略ID
   */
  async unfavoriteStrategy(id: string): Promise<ApiResponse<void>> {
    const response = await httpClient.delete<void>(`/strategy/${id}/favorite`)
    return response.data
  },

  /**
   * 获取收藏的策略
   */
  async getFavoriteStrategies(params?: QueryParams): Promise<ListResponse<StrategyData>> {
    const response = await httpClient.get<StrategyData[]>('/strategy/favorites', { params })
    return response.data
  },

  /**
   * 导出策略
   * @param id - 策略ID
   * @param format - 导出格式
   */
  async exportStrategy(id: string, format: 'json' | 'py' = 'json'): Promise<void> {
    const response = await httpClient.get(`/strategy/${id}/export`, {
      params: { format },
      responseType: 'blob'
    })
    
    // 创建下载链接
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `strategy-${id}.${format}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },

  /**
   * 导入策略
   * @param file - 策略文件
   */
  async importStrategy(file: File): Promise<ApiResponse<StrategyData>> {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await httpClient.post<StrategyData>('/strategy/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }
}

export default strategyApi


