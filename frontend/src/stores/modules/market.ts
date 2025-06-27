import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { marketApi } from '@/api/market'
import { useWebSocket } from '@/composables/useWebSocket'
import type { 
  QuoteData, 
  KLineData, 
  StockInfo,
  MarketOverview,
  SectorData,
  NewsData,
  SearchResult,
  WatchlistItem,
  TimePeriod,
  StockMarket,
  OrderBookData,
  FinancialData,
  RankingData,
  RankingType
} from '@/types/market'

export const useMarketStore = defineStore('market', () => {
  // ============ 状态定义 ============
  
  // 实时行情数据 Map<symbol, QuoteData>
  const quotes = ref(new Map<string, QuoteData>())
  
  // K线数据 Map<symbol-period, KLineData[]>
  const klineData = ref(new Map<string, KLineData[]>())
  
  // 搜索结果缓存
  const searchResults = ref<SearchResult[]>([])
  
  // 自选股列表
  const watchlist = ref<WatchlistItem[]>([])
  
  // 市场概览数据
  const marketOverview = ref<MarketOverview[]>([])
  
  // 板块数据
  const sectors = ref<SectorData[]>([])
  
  // 新闻资讯
  const news = ref<NewsData[]>([])
  
  // 排行榜数据
  const rankings = ref(new Map<RankingType, RankingData[]>())
  
  // 订单簿数据
  const orderBooks = ref(new Map<string, OrderBookData>())
  
  // 财务数据缓存
  const financialData = ref(new Map<string, FinancialData[]>())
  
  // 当前选中的股票
  const selectedStock = ref<StockInfo | null>(null)
  
  // 当前选中的时间周期
  const selectedPeriod = ref<TimePeriod>('1d')
  
  // 当前选中的市场
  const selectedMarket = ref<StockMarket>('SH')
  
  // WebSocket订阅列表
  const subscriptions = ref(new Set<string>())
  
  // 加载状态
  const loading = ref({
    quotes: false,
    kline: false,
    search: false,
    watchlist: false,
    overview: false,
    sectors: false,
    news: false,
    rankings: false,
    orderbook: false,
    financial: false
  })
  
  // 错误状态
  const errors = ref({
    quotes: null as string | null,
    kline: null as string | null,
    search: null as string | null,
    watchlist: null as string | null,
    overview: null as string | null,
    sectors: null as string | null,
    news: null as string | null,
    rankings: null as string | null,
    orderbook: null as string | null,
    financial: null as string | null
  })

  // WebSocket实例
  const { socket, connected, connect, disconnect, subscribe, unsubscribe } = useWebSocket()

  // ============ 计算属性 ============

  // 自选股行情数据
  const watchlistQuotes = computed(() => {
    return watchlist.value.map(item => ({
      ...item,
      quote: quotes.value.get(item.symbol) || null
    })).filter(item => item.quote !== null)
  })

  // 市场统计数据
  const marketStats = computed(() => {
    const totalUp = marketOverview.value.reduce((sum, market) => sum + market.upCount, 0)
    const totalDown = marketOverview.value.reduce((sum, market) => sum + market.downCount, 0)
    const totalFlat = marketOverview.value.reduce((sum, market) => sum + market.flatCount, 0)
    const total = totalUp + totalDown + totalFlat
    
    return {
      totalUp,
      totalDown,
      totalFlat,
      total,
      upPercent: total > 0 ? (totalUp / total) * 100 : 0,
      downPercent: total > 0 ? (totalDown / total) * 100 : 0
    }
  })

  // 涨幅榜前10
  const topGainers = computed(() => {
    return rankings.value.get('change_percent')?.slice(0, 10) || []
  })

  // 跌幅榜前10
  const topLosers = computed(() => {
    const changePercent = rankings.value.get('change_percent') || []
    return changePercent.slice(-10).reverse()
  })

  // 成交额榜前10
  const topTurnover = computed(() => {
    return rankings.value.get('turnover')?.slice(0, 10) || []
  })

  // 活跃板块前5
  const activeSectors = computed(() => {
    return sectors.value
      .sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent))
      .slice(0, 5)
  })

  // 当前选中股票的行情
  const selectedStockQuote = computed(() => {
    return selectedStock.value ? quotes.value.get(selectedStock.value.symbol) : null
  })

  // 当前选中股票的K线数据
  const selectedStockKLine = computed(() => {
    if (!selectedStock.value) return []
    const key = `${selectedStock.value.symbol}-${selectedPeriod.value}`
    return klineData.value.get(key) || []
  })

  // ============ 行情数据方法 ============

  // 获取单只股票行情
  const fetchQuote = async (symbol: string) => {
    loading.value.quotes = true
    errors.value.quotes = null
    
    try {
      const quote = await marketApi.getQuote(symbol)
      quotes.value.set(symbol, quote)
      return quote
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取行情失败'
      errors.value.quotes = message
      throw error
    } finally {
      loading.value.quotes = false
    }
  }

  // 批量获取行情
  const fetchQuotes = async (symbols: string[]) => {
    loading.value.quotes = true
    errors.value.quotes = null
    
    try {
      const quotesData = await marketApi.getQuotes({ symbols })
      quotesData.forEach(quote => {
        quotes.value.set(quote.symbol, quote)
      })
      return quotesData
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取行情失败'
      errors.value.quotes = message
      throw error
    } finally {
      loading.value.quotes = false
    }
  }

  // 获取K线数据
  const fetchKLineData = async (symbol: string, period: TimePeriod = '1d', limit = 500) => {
    loading.value.kline = true
    errors.value.kline = null
    
    try {
      const data = await marketApi.getKLineData({ symbol, period, limit })
      const key = `${symbol}-${period}`
      klineData.value.set(key, data)
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取K线数据失败'
      errors.value.kline = message
      throw error
    } finally {
      loading.value.kline = false
    }
  }

  // 获取历史K线数据
  const fetchHistoryKLineData = async (
    symbol: string, 
    period: TimePeriod, 
    startTime: number, 
    endTime: number
  ) => {
    loading.value.kline = true
    errors.value.kline = null
    
    try {
      const data = await marketApi.getKLineData({ 
        symbol, 
        period, 
        startTime, 
        endTime,
        limit: 10000
      })
      const key = `${symbol}-${period}`
      klineData.value.set(key, data)
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取历史K线数据失败'
      errors.value.kline = message
      throw error
    } finally {
      loading.value.kline = false
    }
  }

  // ============ 搜索相关方法 ============

  // 搜索股票
  const searchStocks = async (keyword: string, market?: StockMarket) => {
    if (!keyword.trim()) {
      searchResults.value = []
      return []
    }

    loading.value.search = true
    errors.value.search = null
    
    try {
      const results = await marketApi.searchStocks({ keyword, market, limit: 20 })
      searchResults.value = results
      return results
    } catch (error) {
      const message = error instanceof Error ? error.message : '搜索失败'
      errors.value.search = message
      searchResults.value = []
      throw error
    } finally {
      loading.value.search = false
    }
  }

  // 清空搜索结果
  const clearSearchResults = () => {
    searchResults.value = []
  }

  // ============ 自选股管理 ============

  // 获取自选股列表
  const fetchWatchlist = async () => {
    loading.value.watchlist = true
    errors.value.watchlist = null
    
    try {
      const data = await marketApi.getWatchlist()
      watchlist.value = data
      
      // 订阅自选股行情
      const symbols = data.map(item => item.symbol)
      if (symbols.length > 0) {
        await subscribeQuotes(symbols)
      }
      
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取自选股失败'
      errors.value.watchlist = message
      throw error
    } finally {
      loading.value.watchlist = false
    }
  }

  // 添加自选股
  const addToWatchlist = async (symbol: string, name: string) => {
    try {
      await marketApi.addToWatchlist(symbol)
      
      const newItem: WatchlistItem = {
        symbol,
        name,
        addTime: Date.now(),
        sort: watchlist.value.length
      }
      
      watchlist.value.push(newItem)
      
      // 订阅新股票的行情
      await subscribeQuote(symbol)
      
      return newItem
    } catch (error) {
      const message = error instanceof Error ? error.message : '添加自选股失败'
      throw new Error(message)
    }
  }

  // 从自选股移除
  const removeFromWatchlist = async (symbol: string) => {
    try {
      await marketApi.removeFromWatchlist(symbol)
      
      const index = watchlist.value.findIndex(item => item.symbol === symbol)
      if (index !== -1) {
        watchlist.value.splice(index, 1)
      }
      
      // 取消订阅
      await unsubscribeQuote(symbol)
    } catch (error) {
      const message = error instanceof Error ? error.message : '移除自选股失败'
      throw new Error(message)
    }
  }

  // 检查是否在自选股中
  const isInWatchlist = (symbol: string): boolean => {
    return watchlist.value.some(item => item.symbol === symbol)
  }

  // ============ 市场概览方法 ============

  // 获取市场概览
  const fetchMarketOverview = async () => {
    loading.value.overview = true
    errors.value.overview = null
    
    try {
      const data = await marketApi.getMarketOverview()
      marketOverview.value = data
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取市场概览失败'
      errors.value.overview = message
      throw error
    } finally {
      loading.value.overview = false
    }
  }

  // 获取板块数据
  const fetchSectors = async () => {
    loading.value.sectors = true
    errors.value.sectors = null
    
    try {
      const data = await marketApi.getSectors()
      sectors.value = data
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取板块数据失败'
      errors.value.sectors = message
      throw error
    } finally {
      loading.value.sectors = false
    }
  }

  // 获取新闻资讯
  const fetchNews = async (limit = 20) => {
    loading.value.news = true
    errors.value.news = null
    
    try {
      const data = await marketApi.getNews({ limit })
      news.value = data
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取新闻失败'
      errors.value.news = message
      throw error
    } finally {
      loading.value.news = false
    }
  }

  // 获取排行榜数据
  const fetchRankings = async (type: RankingType, limit = 50) => {
    loading.value.rankings = true
    errors.value.rankings = null
    
    try {
      const data = await marketApi.getRankings({ type, limit })
      rankings.value.set(type, data)
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取排行榜失败'
      errors.value.rankings = message
      throw error
    } finally {
      loading.value.rankings = false
    }
  }

  // 获取订单簿数据
  const fetchOrderBook = async (symbol: string) => {
    loading.value.orderbook = true
    errors.value.orderbook = null
    
    try {
      const data = await marketApi.getOrderBook(symbol)
      orderBooks.value.set(symbol, data)
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取订单簿失败'
      errors.value.orderbook = message
      throw error
    } finally {
      loading.value.orderbook = false
    }
  }

  // 获取财务数据
  const fetchFinancialData = async (symbol: string) => {
    loading.value.financial = true
    errors.value.financial = null
    
    try {
      const data = await marketApi.getFinancialData(symbol)
      financialData.value.set(symbol, data)
      return data
    } catch (error) {
      const message = error instanceof Error ? error.message : '获取财务数据失败'
      errors.value.financial = message
      throw error
    } finally {
      loading.value.financial = false
    }
  }

  // ============ WebSocket实时数据 ============

  // 连接WebSocket
  const connectWebSocket = async () => {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
    await connect(wsUrl)
    
    // 设置消息处理器
    if (socket.value) {
      socket.value.on('quote', (data: QuoteData) => {
        quotes.value.set(data.symbol, data)
      })
      
      socket.value.on('kline', (data: { symbol: string; period: TimePeriod; kline: KLineData }) => {
        const key = `${data.symbol}-${data.period}`
        const existingData = klineData.value.get(key) || []
        
        // 更新或添加K线数据
        const index = existingData.findIndex(k => k.timestamp === data.kline.timestamp)
        if (index !== -1) {
          existingData[index] = data.kline
        } else {
          existingData.push(data.kline)
          existingData.sort((a, b) => a.timestamp - b.timestamp)
        }
        
        klineData.value.set(key, existingData)
      })
      
      socket.value.on('orderbook', (data: OrderBookData) => {
        orderBooks.value.set(data.symbol, data)
      })
    }
  }

  // 订阅单只股票行情
  const subscribeQuote = async (symbol: string) => {
    if (connected.value && socket.value) {
      await subscribe('quote', { symbol })
      subscriptions.value.add(`quote:${symbol}`)
    }
  }

  // 订阅多只股票行情
  const subscribeQuotes = async (symbols: string[]) => {
    if (connected.value && socket.value) {
      for (const symbol of symbols) {
        await subscribeQuote(symbol)
      }
    }
  }

  // 取消订阅行情
  const unsubscribeQuote = async (symbol: string) => {
    if (connected.value && socket.value) {
      await unsubscribe('quote', { symbol })
      subscriptions.value.delete(`quote:${symbol}`)
    }
  }

  // 订阅K线数据
  const subscribeKLine = async (symbol: string, period: TimePeriod) => {
    if (connected.value && socket.value) {
      await subscribe('kline', { symbol, period })
      subscriptions.value.add(`kline:${symbol}:${period}`)
    }
  }

  // 取消订阅K线数据
  const unsubscribeKLine = async (symbol: string, period: TimePeriod) => {
    if (connected.value && socket.value) {
      await unsubscribe('kline', { symbol, period })
      subscriptions.value.delete(`kline:${symbol}:${period}`)
    }
  }

  // 订阅订单簿
  const subscribeOrderBook = async (symbol: string) => {
    if (connected.value && socket.value) {
      await subscribe('orderbook', { symbol })
      subscriptions.value.add(`orderbook:${symbol}`)
    }
  }

  // ============ 状态管理方法 ============

  // 设置选中股票
  const setSelectedStock = async (stock: StockInfo) => {
    selectedStock.value = stock
    
    // 获取该股票的行情和K线数据
    await Promise.all([
      fetchQuote(stock.symbol),
      fetchKLineData(stock.symbol, selectedPeriod.value)
    ])
    
    // 订阅实时数据
    await Promise.all([
      subscribeQuote(stock.symbol),
      subscribeKLine(stock.symbol, selectedPeriod.value)
    ])
  }

  // 设置时间周期
  const setPeriod = async (period: TimePeriod) => {
    const oldPeriod = selectedPeriod.value
    selectedPeriod.value = period
    
    if (selectedStock.value) {
      // 取消旧周期订阅
      await unsubscribeKLine(selectedStock.value.symbol, oldPeriod)
      
      // 获取新周期数据并订阅
      await fetchKLineData(selectedStock.value.symbol, period)
      await subscribeKLine(selectedStock.value.symbol, period)
    }
  }

  // 设置选中市场
  const setSelectedMarket = (market: StockMarket) => {
    selectedMarket.value = market
  }

  // 更新行情数据
  const updateQuote = (symbol: string, quote: Partial<QuoteData>) => {
    const existingQuote = quotes.value.get(symbol)
    if (existingQuote) {
      quotes.value.set(symbol, { ...existingQuote, ...quote })
    }
  }

  // 更新K线数据
  const updateKLineData = (symbol: string, period: TimePeriod, newData: KLineData) => {
    const key = `${symbol}-${period}`
    const existingData = klineData.value.get(key) || []
    
    // 查找是否存在相同时间戳的数据
    const index = existingData.findIndex(k => k.timestamp === newData.timestamp)
    if (index !== -1) {
      existingData[index] = newData
    } else {
      existingData.push(newData)
      existingData.sort((a, b) => a.timestamp - b.timestamp)
    }
    
    klineData.value.set(key, existingData)
  }

  // ============ 初始化和清理 ============

  // 初始化市场数据
  const initialize = async () => {
    try {
      // 连接WebSocket
      await connectWebSocket()
      
      // 获取基础数据
      await Promise.all([
        fetchMarketOverview(),
        fetchWatchlist(),
        fetchSectors(),
        fetchNews(10),
        fetchRankings('change_percent'),
        fetchRankings('turnover')
      ])
    } catch (error) {
      console.error('初始化市场数据失败:', error)
      throw error
    }
  }

  // 刷新数据
  const refresh = async () => {
    try {
      await Promise.all([
        fetchMarketOverview(),
        fetchSectors(),
        // 刷新自选股行情
        fetchQuotes(watchlist.value.map(item => item.symbol))
      ])
    } catch (error) {
      console.error('刷新市场数据失败:', error)
      throw error
    }
  }

  // 清理所有订阅
  const cleanup = async () => {
    // 取消所有WebSocket订阅
    for (const subscription of subscriptions.value) {
      const [type, ...params] = subscription.split(':')
      if (type === 'quote') {
        await unsubscribeQuote(params[0])
      } else if (type === 'kline') {
        await unsubscribeKLine(params[0], params[1] as TimePeriod)
      }
    }
    
    subscriptions.value.clear()
    
    // 断开WebSocket连接
    disconnect()
  }

  // 重置状态
  const reset = () => {
    quotes.value.clear()
    klineData.value.clear()
    searchResults.value = []
    watchlist.value = []
    marketOverview.value = []
    sectors.value = []
    news.value = []
    rankings.value.clear()
    orderBooks.value.clear()
    financialData.value.clear()
    selectedStock.value = null
    selectedPeriod.value = '1d'
    selectedMarket.value = 'SH'
    subscriptions.value.clear()
    
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
    quotes,
    klineData,
    searchResults,
    watchlist,
    marketOverview,
    sectors,
    news,
    rankings,
    orderBooks,
    financialData,
    selectedStock,
    selectedPeriod,
    selectedMarket,
    subscriptions,
    loading,
    errors,
    connected,
    
    // 计算属性
    watchlistQuotes,
    marketStats,
    topGainers,
    topLosers,
    topTurnover,
    activeSectors,
    selectedStockQuote,
    selectedStockKLine,
    
    // 行情数据方法
    fetchQuote,
    fetchQuotes,
    fetchKLineData,
    fetchHistoryKLineData,
    
    // 获取单个股票行情（从缓存）
    getQuote: (symbol: string) => quotes.value.get(symbol),
    
    // 搜索方法
    searchStocks,
    clearSearchResults,
    
    // 自选股管理
    fetchWatchlist,
    addToWatchlist,
    removeFromWatchlist,
    isInWatchlist,
    
    // 市场数据方法
    fetchMarketOverview,
    fetchSectors,
    fetchNews,
    fetchRankings,
    fetchOrderBook,
    fetchFinancialData,
    
    // WebSocket方法
    connectWebSocket,
    subscribeQuote,
    subscribeQuotes,
    unsubscribeQuote,
    subscribeKLine,
    unsubscribeKLine,
    subscribeOrderBook,
    
    // 状态管理方法
    setSelectedStock,
    setPeriod,
    setSelectedMarket,
    updateQuote,
    updateKLineData,
    
    // 初始化和清理
    initialize,
    refresh,
    cleanup,
    reset
  }
})

