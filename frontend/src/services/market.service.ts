import { http } from '@/api/http'
import { io, Socket } from 'socket.io-client'
import { EventEmitter } from 'events'
import type { 
  QuoteData, 
  KLineData, 
  MarketSearchResult,
  MarketOverviewData,
  SectorData,
  MarketNewsItem,
  TradingCalendar 
} from '@/types/market'

/**
 * 市场数据服务类
 */
class MarketService extends EventEmitter {
  private static instance: MarketService
  private socket: Socket | null = null
  private subscriptions = new Set<string>()
  private quotesCache = new Map<string, QuoteData>()
  private klineCache = new Map<string, Map<string, KLineData[]>>()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectTimer: NodeJS.Timeout | null = null
  private heartbeatTimer: NodeJS.Timeout | null = null

  private constructor() {
    super()
    this.initWebSocket()
  }

  /**
   * 获取单例实例
   */
  public static getInstance(): MarketService {
    if (!MarketService.instance) {
      MarketService.instance = new MarketService()
    }
    return MarketService.instance
  }

  /**
   * 获取实时行情
   * @param symbol 股票代码
   * @returns 行情数据
   */
  async getQuote(symbol: string): Promise<QuoteData> {
    try {
      // 先从缓存获取
      const cached = this.quotesCache.get(symbol)
      if (cached && this.isCacheValid(cached.timestamp)) {
        return cached
      }

      // 从API获取
      const response = await http.get<{ data: QuoteData }>(`/market/quote/${symbol}`)
      
      if (response.data) {
        // 更新缓存
        this.quotesCache.set(symbol, response.data)
        return response.data
      } else {
        throw new Error('获取行情数据失败')
      }
    } catch (error) {
      console.error(`获取${symbol}行情失败:`, error)
      throw error
    }
  }

  /**
   * 批量获取实时行情
   * @param symbols 股票代码数组
   * @returns 行情数据数组
   */
  async getQuotes(symbols: string[]): Promise<QuoteData[]> {
    try {
      const response = await http.post<{ data: QuoteData[] }>('/market/quotes', {
        symbols
      })

      if (response.data) {
        // 更新缓存
        response.data.forEach(quote => {
          this.quotesCache.set(quote.symbol, quote)
        })
        
        return response.data
      } else {
        throw new Error('批量获取行情数据失败')
      }
    } catch (error) {
      console.error('批量获取行情失败:', error)
      throw error
    }
  }

  /**
   * 获取K线数据
   * @param symbol 股票代码
   * @param period 周期
   * @param limit 数量限制
   * @param startTime 开始时间
   * @param endTime 结束时间
   * @returns K线数据
   */
  async getKLineData(params: {
    symbol: string
    period: string
    limit?: number
    startTime?: number
    endTime?: number
  }): Promise<KLineData[]> {
    try {
      const { symbol, period } = params
      
      // 检查缓存
      const symbolCache = this.klineCache.get(symbol)
      const cached = symbolCache?.get(period)
      
      if (cached && cached.length > 0 && this.isKLineCacheValid(cached)) {
        return cached
      }

      // 从API获取
      const response = await http.get<{ data: KLineData[] }>('/market/kline', {
        params
      })

      if (response.data) {
        // 更新缓存
        if (!this.klineCache.has(symbol)) {
          this.klineCache.set(symbol, new Map())
        }
        this.klineCache.get(symbol)!.set(period, response.data)
        
        return response.data
      } else {
        throw new Error('获取K线数据失败')
      }
    } catch (error) {
      console.error('获取K线数据失败:', error)
      throw error
    }
  }

  /**
   * 搜索股票
   * @param keyword 关键词
   * @param limit 结果数量限制
   * @returns 搜索结果
   */
  async searchStocks(keyword: string, limit = 20): Promise<MarketSearchResult[]> {
    try {
      if (!keyword.trim()) return []

      const response = await http.get<{ data: MarketSearchResult[] }>('/market/search', {
        params: { keyword, limit }
      })

      return response.data || []
    } catch (error) {
      console.error('搜索股票失败:', error)
      throw error
    }
  }

  /**
   * 获取市场概览
   * @returns 市场概览数据
   */
  async getMarketOverview(): Promise<MarketOverviewData> {
    try {
      const response = await http.get<{ data: MarketOverviewData }>('/market/overview')
      
      if (response.data) {
        return response.data
      } else {
        throw new Error('获取市场概览失败')
      }
    } catch (error) {
      console.error('获取市场概览失败:', error)
      throw error
    }
  }

  /**
   * 获取板块数据
   * @returns 板块数据
   */
  async getSectorData(): Promise<SectorData[]> {
    try {
      const response = await http.get<{ data: SectorData[] }>('/market/sectors')
      
      return response.data || []
    } catch (error) {
      console.error('获取板块数据失败:', error)
      throw error
    }
  }

  /**
   * 获取涨跌幅排行
   * @param type 排行类型
   * @param limit 数量限制
   * @returns 排行数据
   */
  async getRankingList(type: 'gainers' | 'losers' | 'active', limit = 50): Promise<QuoteData[]> {
    try {
      const response = await http.get<{ data: QuoteData[] }>(`/market/ranking/${type}`, {
        params: { limit }
      })

      return response.data || []
    } catch (error) {
      console.error('获取排行数据失败:', error)
      throw error
    }
  }

  /**
   * 获取市场新闻
   * @param limit 数量限制
   * @param category 新闻分类
   * @returns 新闻数据
   */
  async getMarketNews(limit = 20, category?: string): Promise<MarketNewsItem[]> {
    try {
      const response = await http.get<{ data: MarketNewsItem[] }>('/market/news', {
        params: { limit, category }
      })

      return response.data || []
    } catch (error) {
      console.error('获取市场新闻失败:', error)
      throw error
    }
  }

  /**
   * 获取交易日历
   * @param year 年份
   * @param month 月份
   * @returns 交易日历
   */
  async getTradingCalendar(year?: number, month?: number): Promise<TradingCalendar> {
    try {
      const response = await http.get<{ data: TradingCalendar }>('/market/calendar', {
        params: { year, month }
      })

      if (response.data) {
        return response.data
      } else {
        throw new Error('获取交易日历失败')
      }
    } catch (error) {
      console.error('获取交易日历失败:', error)
      throw error
    }
  }

  /**
   * 订阅实时行情
   * @param symbol 股票代码
   */
  subscribeQuote(symbol: string): void {
    if (!this.socket || !this.socket.connected) {
      this.initWebSocket()
    }

    if (this.subscriptions.has(symbol)) return

    this.subscriptions.add(symbol)
    
    if (this.socket && this.socket.connected) {
      this.socket.emit('subscribe', { type: 'quote', symbol })
    }
  }

  /**
   * 取消订阅实时行情
   * @param symbol 股票代码
   */
  unsubscribeQuote(symbol: string): void {
    if (!this.subscriptions.has(symbol)) return

    this.subscriptions.delete(symbol)
    
    if (this.socket && this.socket.connected) {
      this.socket.emit('unsubscribe', { type: 'quote', symbol })
    }
  }

  /**
   * 批量订阅行情
   * @param symbols 股票代码数组
   */
  subscribeQuotes(symbols: string[]): void {
    symbols.forEach(symbol => this.subscribeQuote(symbol))
  }

  /**
   * 批量取消订阅
   * @param symbols 股票代码数组
   */
  unsubscribeQuotes(symbols: string[]): void {
    symbols.forEach(symbol => this.unsubscribeQuote(symbol))
  }

  /**
   * 获取已订阅的股票列表
   * @returns 股票代码数组
   */
  getSubscriptions(): string[] {
    return Array.from(this.subscriptions)
  }

  /**
   * 清除所有订阅
   */
  clearSubscriptions(): void {
    if (this.socket && this.socket.connected) {
      this.subscriptions.forEach(symbol => {
        this.socket!.emit('unsubscribe', { type: 'quote', symbol })
      })
    }
    
    this.subscriptions.clear()
  }

  /**
   * 获取缓存的行情数据
   * @param symbol 股票代码
   * @returns 行情数据或null
   */
  getCachedQuote(symbol: string): QuoteData | null {
    return this.quotesCache.get(symbol) || null
  }

  /**
   * 清除行情缓存
   * @param symbol 股票代码，不传则清除所有
   */
  clearQuoteCache(symbol?: string): void {
    if (symbol) {
      this.quotesCache.delete(symbol)
    } else {
      this.quotesCache.clear()
    }
  }

  /**
   * 清除K线缓存
   * @param symbol 股票代码，不传则清除所有
   */
  clearKLineCache(symbol?: string): void {
    if (symbol) {
      this.klineCache.delete(symbol)
    } else {
      this.klineCache.clear()
    }
  }

  /**
   * 获取WebSocket连接状态
   */
  isConnected(): boolean {
    return this.socket?.connected || false
  }

  /**
   * 手动重连WebSocket
   */
  reconnect(): void {
    if (this.socket) {
      this.socket.disconnect()
    }
    this.initWebSocket()
  }

  /**
   * 销毁服务
   */
  destroy(): void {
    this.clearSubscriptions()
    this.clearTimers()
    
    if (this.socket) {
      this.socket.removeAllListeners()
      this.socket.disconnect()
      this.socket = null
    }
    
    this.quotesCache.clear()
    this.klineCache.clear()
    this.removeAllListeners()
  }

  /**
   * 初始化WebSocket连接
   */
  private initWebSocket(): void {
    try {
      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
      
      this.socket = io(wsUrl, {
        transports: ['websocket'],
        timeout: 5000,
        forceNew: true
      })

      this.socket.on('connect', () => {
        console.log('市场数据WebSocket已连接')
        this.reconnectAttempts = 0
        this.emit('connected')
        
        // 重新订阅之前的股票
        this.resubscribeAll()
        
        // 启动心跳
        this.startHeartbeat()
      })

      this.socket.on('disconnect', (reason) => {
        console.log('市场数据WebSocket断开连接:', reason)
        this.emit('disconnected', reason)
        this.clearTimers()
        
        // 自动重连
        this.attemptReconnect()
      })

      this.socket.on('quote', (data: QuoteData) => {
        // 更新缓存
        this.quotesCache.set(data.symbol, data)
        
        // 发出事件
        this.emit('quote', data)
        this.emit(`quote:${data.symbol}`, data)
      })

      this.socket.on('kline', (data: { symbol: string; period: string; data: KLineData }) => {
        // 更新K线缓存
        const symbolCache = this.klineCache.get(data.symbol)
        if (symbolCache) {
          const klineData = symbolCache.get(data.period)
          if (klineData) {
            // 更新最新的K线数据
            const lastIndex = klineData.length - 1
            if (lastIndex >= 0 && klineData[lastIndex].timestamp === data.data.timestamp) {
              klineData[lastIndex] = data.data
            } else {
              klineData.push(data.data)
            }
          }
        }
        
        // 发出事件
        this.emit('kline', data)
        this.emit(`kline:${data.symbol}:${data.period}`, data.data)
      })

      this.socket.on('error', (error) => {
        console.error('市场数据WebSocket错误:', error)
        this.emit('error', error)
      })

      this.socket.on('pong', () => {
        // 心跳响应
      })

    } catch (error) {
      console.error('初始化WebSocket失败:', error)
      this.attemptReconnect()
    }
  }

  /**
   * 重新订阅所有股票
   */
  private resubscribeAll(): void {
    if (!this.socket || !this.socket.connected) return

    this.subscriptions.forEach(symbol => {
      this.socket!.emit('subscribe', { type: 'quote', symbol })
    })
  }

  /**
   * 尝试重连
   */
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket重连次数已达上限')
      this.emit('reconnectFailed')
      return
    }

    this.reconnectAttempts++
    const delay = Math.pow(2, this.reconnectAttempts) * 1000 // 指数退避

    this.reconnectTimer = setTimeout(() => {
      console.log(`尝试第${this.reconnectAttempts}次重连...`)
      this.initWebSocket()
    }, delay)
  }

  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.socket && this.socket.connected) {
        this.socket.emit('ping')
      }
    }, 30000) // 30秒心跳
  }

  /**
   * 清除定时器
   */
  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 检查缓存是否有效
   */
  private isCacheValid(timestamp: string): boolean {
    const cacheTime = new Date(timestamp).getTime()
    const now = Date.now()
    const maxAge = 5000 // 5秒缓存
    
    return now - cacheTime < maxAge
  }

  /**
   * 检查K线缓存是否有效
   */
  private isKLineCacheValid(data: KLineData[]): boolean {
    if (data.length === 0) return false
    
    const lastTimestamp = new Date(data[data.length - 1].timestamp).getTime()
    const now = Date.now()
    const maxAge = 60000 // 1分钟缓存
    
    return now - lastTimestamp < maxAge
  }
}

// 导出单例实例
export const marketService = MarketService.getInstance()
export default marketService 