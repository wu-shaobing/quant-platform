/**
 * 市场数据管理组合函数
 * 提供行情数据获取、搜索、订阅等功能
 */
import { ref, computed, onUnmounted } from 'vue'
import { marketApi } from '@/api'
import { useWebSocket } from './useWebSocket'
import type { QuoteData, KLineData, StockInfo, MarketSearchResult } from '@/types/market'

// 搜索结果缓存
const searchCache = new Map<string, { data: MarketSearchResult[], timestamp: number }>()
const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

/**
 * 市场数据管理
 */
export const useMarketData = () => {
  // WebSocket 连接
  const { isConnected, subscribe, unsubscribe, send } = useWebSocket({
    url: import.meta.env.VITE_WS_URL,
    debug: import.meta.env.NODE_ENV === 'development'
  })

  // 状态管理
  const quotes = ref<Map<string, QuoteData>>(new Map())
  const klineData = ref<Map<string, KLineData[]>>(new Map())
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 订阅的股票列表
  const subscribedSymbols = ref<Set<string>>(new Set())

  // 计算属性
  const quotesArray = computed(() => Array.from(quotes.value.values()))
  const hasData = computed(() => quotes.value.size > 0)

  // 错误处理
  const handleError = (err: any, context: string) => {
    const message = err?.message || err || '未知错误'
    error.value = `${context}: ${message}`
    console.error(`[MarketData] ${context}:`, err)
  }

  // 清除错误
  const clearError = () => {
    error.value = null
  }

  /**
   * 获取股票信息
   */
  const getStockInfo = async (symbol: string): Promise<StockInfo | null> => {
    try {
      clearError()
      const data = await marketApi.getStockInfo(symbol)
      return data
    } catch (err) {
      handleError(err, '获取股票信息失败')
      return null
    }
  }

  /**
   * 搜索股票
   */
  const searchStocks = async (keyword: string): Promise<MarketSearchResult[]> => {
    if (!keyword || keyword.length < 2) {
      return []
    }

    // 检查缓存
    const cached = searchCache.get(keyword)
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached.data
    }

    try {
      clearError()
      loading.value = true
      
      const results = await marketApi.searchStocks(keyword)
      
      // 缓存结果
      searchCache.set(keyword, {
        data: results,
        timestamp: Date.now()
      })
      
      return results
    } catch (err) {
      handleError(err, '搜索股票失败')
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取实时行情
   */
  const getQuote = async (symbol: string): Promise<QuoteData | null> => {
    try {
      clearError()
      const data = await marketApi.getQuote(symbol)
      
      // 更新本地缓存
      if (data) {
        quotes.value.set(symbol, data)
      }
      
      return data
    } catch (err) {
      handleError(err, '获取行情失败')
      return null
    }
  }

  /**
   * 批量获取行情
   */
  const getQuotes = async (symbols: string[]): Promise<QuoteData[]> => {
    try {
      clearError()
      loading.value = true
      
      const promises = symbols.map(symbol => getQuote(symbol))
      const results = await Promise.allSettled(promises)
      
      return results
        .filter((result): result is PromiseFulfilledResult<QuoteData> => 
          result.status === 'fulfilled' && result.value !== null
        )
        .map(result => result.value)
    } catch (err) {
      handleError(err, '批量获取行情失败')
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取K线数据
   */
  const getKLineData = async (
    symbol: string, 
    period: string, 
    limit?: number
  ): Promise<KLineData[]> => {
    try {
      clearError()
      loading.value = true
      
      const data = await marketApi.getKLineData({
        symbol,
        period,
        limit
      })
      
      // 更新本地缓存
      const key = `${symbol}_${period}`
      klineData.value.set(key, data)
      
      return data
    } catch (err) {
      handleError(err, '获取K线数据失败')
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * 订阅实时行情
   */
  const subscribeQuote = (symbol: string) => {
    if (!isConnected.value) {
      console.warn('[MarketData] WebSocket not connected, cannot subscribe')
      return
    }

    if (subscribedSymbols.value.has(symbol)) {
      return // 已经订阅
    }

    subscribe(`quote.${symbol}`, { symbol }, (data) => {
      if (data.quote) {
        quotes.value.set(symbol, data.quote)
      }
    })

    subscribedSymbols.value.add(symbol)
  }

  /**
   * 取消订阅实时行情
   */
  const unsubscribeQuote = (symbol: string) => {
    if (!subscribedSymbols.value.has(symbol)) {
      return // 未订阅
    }

    unsubscribe(`quote.${symbol}`)
    subscribedSymbols.value.delete(symbol)
  }

  /**
   * 订阅K线数据
   */
  const subscribeKLine = (symbol: string, period: string) => {
    if (!isConnected.value) {
      console.warn('[MarketData] WebSocket not connected, cannot subscribe')
      return
    }

    const channel = `kline.${symbol}.${period}`
    
    subscribe(channel, { symbol, period }, (data) => {
      if (data.kline) {
        const key = `${symbol}_${period}`
        const existing = klineData.value.get(key) || []
        
        // 更新或添加K线数据
        const index = existing.findIndex(k => k.timestamp === data.kline.timestamp)
        if (index >= 0) {
          existing[index] = data.kline
        } else {
          existing.push(data.kline)
          existing.sort((a, b) => a.timestamp - b.timestamp)
        }
        
        klineData.value.set(key, existing)
      }
    })
  }

  /**
   * 取消订阅K线数据
   */
  const unsubscribeKLine = (symbol: string, period: string) => {
    const channel = `kline.${symbol}.${period}`
    unsubscribe(channel)
  }

  /**
   * 获取市场概览
   */
  const getMarketOverview = async () => {
    try {
      clearError()
      const data = await marketApi.getMarketOverview()
      return data
    } catch (err) {
      handleError(err, '获取市场概览失败')
      return null
    }
  }

  /**
   * 获取板块数据
   */
  const getSectorData = async () => {
    try {
      clearError()
      const data = await marketApi.getSectorData()
      return data
    } catch (err) {
      handleError(err, '获取板块数据失败')
      return []
    }
  }

  /**
   * 获取排行榜数据
   */
  const getRankingData = async (type: string, limit = 20) => {
    try {
      clearError()
      const data = await marketApi.getRanking(type as any, { limit })
      return data
    } catch (err) {
      handleError(err, '获取排行榜失败')
      return []
    }
  }

  /**
   * 清除缓存数据
   */
  const clearCache = () => {
    quotes.value.clear()
    klineData.value.clear()
    searchCache.clear()
    subscribedSymbols.value.clear()
  }

  /**
   * 获取指定股票的行情数据
   */
  const getQuoteBySymbol = (symbol: string): QuoteData | undefined => {
    return quotes.value.get(symbol)
  }

  /**
   * 获取指定股票的K线数据
   */
  const getKLineBySymbol = (symbol: string, period: string): KLineData[] => {
    const key = `${symbol}_${period}`
    return klineData.value.get(key) || []
  }

  /**
   * 批量订阅行情
   */
  const subscribeMultipleQuotes = (symbols: string[]) => {
    symbols.forEach(symbol => subscribeQuote(symbol))
  }

  /**
   * 批量取消订阅
   */
  const unsubscribeMultipleQuotes = (symbols: string[]) => {
    symbols.forEach(symbol => unsubscribeQuote(symbol))
  }

  // 组件卸载时清理订阅
  onUnmounted(() => {
    // 取消所有订阅
    subscribedSymbols.value.forEach(symbol => {
      unsubscribeQuote(symbol)
    })
  })

  return {
    // 状态
    quotes: readonly(quotes),
    klineData: readonly(klineData),
    quotesArray,
    hasData,
    loading: readonly(loading),
    error: readonly(error),
    subscribedSymbols: readonly(subscribedSymbols),

    // 方法
    getStockInfo,
    searchStocks,
    getQuote,
    getQuotes,
    getKLineData,
    subscribeQuote,
    unsubscribeQuote,
    subscribeKLine,
    unsubscribeKLine,
    getMarketOverview,
    getSectorData,
    getRankingData,
    clearCache,
    clearError,
    getQuoteBySymbol,
    getKLineBySymbol,
    subscribeMultipleQuotes,
    unsubscribeMultipleQuotes
  }
} 