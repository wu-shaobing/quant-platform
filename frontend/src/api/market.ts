/**
 * 市场数据 API
 */
import { httpClient } from './http'
import { API_PATHS } from '@/utils/constants'
import type {
  QuoteData,
  KLineData,
  KLineParams,
  QuoteParams,
  SearchParams,
  SearchResult,
  MarketOverview,
  SectorData,
  NewsData,
  RankingData,
  RankingType,
  MarketStatus,
  OrderBookData,
  StockSearchResult,
  WatchlistItem,
  DepthData,
  MarketSector,
  NewsItem,
  IndexData
} from '@/types/market'
import { mockService } from '@/services/mock.service'
import type { 
  ApiResponse, 
  ListResponse, 
  TickData, 
  BarData, 
  QueryParams 
} from '@/types/api'

// 配置
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export interface MarketDataRequest {
  symbol: string
  startDate?: string
  endDate?: string
  interval?: string
  limit?: number
}

export interface SymbolInfo {
  symbol: string
  name: string
  exchange: string
  type: string
  minTick: number
  multiplier: number
  marginRate: number
  feeRate: number
  status: string
}

/**
 * 市场数据API类
 */
export class MarketAPI {
  /**
   * 获取实时行情
   */
  async getQuote(symbols: string | string[]): Promise<QuoteData[]> {
    const symbolList = Array.isArray(symbols) ? symbols : [symbols]
    
    if (USE_MOCK) {
      return mockService.getQuoteData(symbolList)
    }
    
    const response = await httpClient.get<QuoteData[]>(API_PATHS.MARKET.QUOTE, {
      params: {
        symbols: symbolList.join(',')
      }
    })
    
    return response.data
  }

  /**
   * 批量获取行情数据
   */
  async getQuotes(params: QuoteParams): Promise<QuoteData[]> {
    const response = await httpClient.get<QuoteData[]>(API_PATHS.MARKET.QUOTE, {
      params: {
        symbols: params.symbols.join(','),
        fields: params.fields?.join(',')
      }
    })
    
    return response.data
  }

  /**
   * 获取K线数据
   */
  async getKLineData(params: KLineParams): Promise<KLineData[]> {
    const response = await httpClient.get<KLineData[]>(API_PATHS.MARKET.KLINE, {
      params: {
        symbol: params.symbol,
        period: params.period,
        limit: params.limit || 1000,
        start_time: params.startTime,
        end_time: params.endTime
      }
    })
    
    return response.data
  }

  /**
   * 获取历史K线数据
   */
  async getHistoryKLineData(params: KLineParams): Promise<KLineData[]> {
    const response = await httpClient.get<KLineData[]>(`${API_PATHS.MARKET.KLINE}/history`, {
      params: {
        symbol: params.symbol,
        period: params.period,
        limit: params.limit || 1000,
        start_time: params.startTime,
        end_time: params.endTime
      }
    })
    
    return response.data
  }

  /**
   * 搜索股票
   */
  async searchStocks(params: SearchParams): Promise<StockSearchResult[]> {
    if (USE_MOCK) {
      // Mock搜索逻辑
      const mockStocks = await mockService.getQuoteData(['000001', '000002', '000858', '600036', '600519'])
      return mockStocks
        .filter(stock => 
          stock.symbol.includes(params.keyword) || 
          stock.name.includes(params.keyword)
        )
        .slice(0, params.limit || 10)
        .map(stock => ({
          symbol: stock.symbol,
          name: stock.name,
          currentPrice: stock.currentPrice,
          changePercent: stock.changePercent,
          market: stock.symbol.startsWith('6') ? 'SH' : 'SZ'
        }))
    }
    
    const response = await httpClient.get<StockSearchResult[]>(API_PATHS.MARKET.SEARCH, {
      params
    })
    return response.data
  }

  /**
   * 获取市场概览
   */
  async getMarketOverview(): Promise<MarketOverview[]> {
    if (USE_MOCK) {
      return mockService.getMarketOverview()
    }
    
    const response = await httpClient.get<MarketOverview[]>(API_PATHS.MARKET.OVERVIEW)
    return response.data
  }

  /**
   * 获取指定市场概览
   */
  async getMarketOverviewByMarket(market: string): Promise<MarketOverview> {
    const response = await httpClient.get<MarketOverview>(`${API_PATHS.MARKET.OVERVIEW}/${market}`)
    return response.data
  }

  /**
   * 获取板块数据
   */
  async getSectors(): Promise<SectorData[]> {
    const response = await httpClient.get<SectorData[]>(API_PATHS.MARKET.SECTORS)
    return response.data
  }

  /**
   * 获取指定板块数据
   */
  async getSectorDetail(sectorCode: string): Promise<SectorData> {
    const response = await httpClient.get<SectorData>(`${API_PATHS.MARKET.SECTORS}/${sectorCode}`)
    return response.data
  }

  /**
   * 获取指数数据
   */
  async getIndices(): Promise<IndexData[]> {
    const response = await httpClient.get<IndexData[]>(API_PATHS.MARKET.INDICES)
    return response.data
  }

  /**
   * 获取新闻资讯
   */
  async getNews(params?: {
    category?: string
    limit?: number
    offset?: number
    symbol?: string
  }): Promise<NewsData[]> {
    const response = await httpClient.get<NewsData[]>(API_PATHS.MARKET.NEWS, {
      params
    })
    return response.data
  }

  /**
   * 获取排行榜数据
   */
  async getRanking(type: RankingType, params?: {
    market?: string
    limit?: number
    direction?: 'asc' | 'desc'
  }): Promise<RankingData[]> {
    const response = await httpClient.get<RankingData[]>(`${API_PATHS.MARKET.OVERVIEW}/ranking`, {
      params: {
        type,
        ...params
      }
    })
    return response.data
  }

  /**
   * 获取涨跌停板数据
   */
  async getLimitUpDown(): Promise<{
    limitUp: RankingData[]
    limitDown: RankingData[]
  }> {
    const response = await httpClient.get<{
      limitUp: RankingData[]
      limitDown: RankingData[]
    }>(`${API_PATHS.MARKET.RANKING}/limit`)
    return response.data
  }

  /**
   * 获取龙虎榜数据
   */
  async getDragonTiger(date?: string): Promise<any[]> {
    const response = await httpClient.get<any[]>(`${API_PATHS.MARKET.RANKING}/dragon-tiger`, {
      params: { date }
    })
    return response.data
  }

  /**
   * 获取订单簿数据
   */
  async getOrderBook(symbol: string, level = 5): Promise<OrderBookData> {
    const response = await httpClient.get<OrderBookData>(API_PATHS.MARKET.ORDERBOOK, {
      params: {
        symbol,
        level
      }
    })
    return response.data
  }

  /**
   * 获取分时数据
   */
  async getTickData(symbol: string, date?: string): Promise<any[]> {
    const response = await httpClient.get<any[]>(API_PATHS.MARKET.TICK, {
      params: {
        symbol,
        date
      }
    })
    return response.data
  }

  /**
   * 获取股票基本信息
   */
  async getStockInfo(symbol: string): Promise<any> {
    const response = await httpClient.get<any>(`${API_PATHS.MARKET.QUOTE}/info`, {
      params: { symbol }
    })
    return response.data
  }

  /**
   * 获取财务数据
   */
  async getFinancialData(symbol: string, params?: {
    type?: 'income' | 'balance' | 'cashflow'
    period?: 'quarter' | 'year'
    limit?: number
  }): Promise<any[]> {
    const response = await httpClient.get<any[]>(`${API_PATHS.MARKET.QUOTE}/financial`, {
      params: {
        symbol,
        ...params
      }
    })
    return response.data
  }

  /**
   * 获取技术指标数据
   */
  async getIndicatorData(symbol: string, params: {
    indicator: string
    period: string
    params?: Record<string, any>
    limit?: number
  }): Promise<any[]> {
    const response = await httpClient.get<any[]>(`${API_PATHS.MARKET.KLINE}/indicator`, {
      params: {
        symbol,
        ...params
      }
    })
    return response.data
  }

  /**
   * 获取市场状态
   */
  async getMarketStatus(): Promise<MarketStatus[]> {
    const response = await httpClient.get<MarketStatus[]>(`${API_PATHS.MARKET.OVERVIEW}/status`)
    return response.data
  }

  /**
   * 获取交易日历
   */
  async getTradingCalendar(year?: number): Promise<{
    tradingDays: string[]
    holidays: string[]
  }> {
    const response = await httpClient.get<{
      tradingDays: string[]
      holidays: string[]
    }>(`${API_PATHS.MARKET.OVERVIEW}/calendar`, {
      params: { year }
    })
    return response.data
  }

  /**
   * 获取股票公告
   */
  async getAnnouncements(symbol: string, params?: {
    type?: string
    limit?: number
    offset?: number
  }): Promise<any[]> {
    const response = await httpClient.get<any[]>(`${API_PATHS.MARKET.QUOTE}/announcements`, {
      params: {
        symbol,
        ...params
      }
    })
    return response.data
  }

  /**
   * 获取研报数据
   */
  async getResearchReports(symbol?: string, params?: {
    analyst?: string
    rating?: string
    limit?: number
    offset?: number
  }): Promise<any[]> {
    const response = await httpClient.get<any[]>(`${API_PATHS.MARKET.NEWS}/research`, {
      params: {
        symbol,
        ...params
      }
    })
    return response.data
  }

  /**
   * 获取股东信息
   */
  async getShareholders(symbol: string, type: 'major' | 'institutional' = 'major'): Promise<any[]> {
    const response = await httpClient.get<any[]>(`${API_PATHS.MARKET.QUOTE}/shareholders`, {
      params: {
        symbol,
        type
      }
    })
    return response.data
  }

  /**
   * 获取同行业股票
   */
  async getSameIndustryStocks(symbol: string, limit = 20): Promise<QuoteData[]> {
    const response = await httpClient.get<QuoteData[]>(`${API_PATHS.MARKET.QUOTE}/same-industry`, {
      params: {
        symbol,
        limit
      }
    })
    return response.data
  }

  /**
   * 获取相关股票
   */
  async getRelatedStocks(symbol: string, limit = 10): Promise<QuoteData[]> {
    const response = await httpClient.get<QuoteData[]>(`${API_PATHS.MARKET.QUOTE}/related`, {
      params: {
        symbol,
        limit
      }
    })
    return response.data
  }

  /**
   * 获取股票评级
   */
  async getStockRating(symbol: string): Promise<{
    overallRating: number
    ratings: Array<{
      institution: string
      rating: string
      targetPrice?: number
      date: string
    }>
  }> {
    const response = await httpClient.get<{
      overallRating: number
      ratings: Array<{
        institution: string
        rating: string
        targetPrice?: number
        date: string
      }>
    }>(`${API_PATHS.MARKET.QUOTE}/rating`, {
      params: { symbol }
    })
    return response.data
  }

  /**
   * 获取自选股列表
   */
  async getWatchlist(): Promise<WatchlistItem[]> {
    if (USE_MOCK) {
      return []
    }
    const response = await httpClient.get<WatchlistItem[]>('/market/watchlist')
    return response.data
  }

  /**
   * 添加股票到自选股
   */
  async addToWatchlist(symbol: string): Promise<void> {
    if (USE_MOCK) return
    await httpClient.post('/market/watchlist', { symbol })
  }

  /**
   * 从自选股移除股票
   */
  async removeFromWatchlist(symbol: string): Promise<void> {
    if (USE_MOCK) return
    await httpClient.delete(`/market/watchlist/${symbol}`)
  }

  /**
   * 兼容旧代码：复数形式 getRankings
   */
  async getRankings(opts: { type: RankingType; limit?: number; market?: string; direction?: 'asc' | 'desc' }): Promise<RankingData[]> {
    const { type, ...rest } = opts
    return this.getRanking(type, rest)
  }

  /**
   * 获取股票列表（支持市场、行业等筛选）
   */
  async getStockList(params: {
    market?: string
    industry?: string
    page?: number
    pageSize?: number
  } = {}): Promise<QuoteData[]> {
    const response = await httpClient.get<QuoteData[]>(API_PATHS.MARKET.STOCKS, {
      params
    })
    return response.data
  }
}

// 创建实例
export const marketApi = new MarketAPI()

// 导出默认实例
export default marketApi

// 获取实时行情
export const getTick = async (symbol: string): Promise<ApiResponse<TickData>> => {
  const response = await httpClient.get<TickData>(`/market/tick/${symbol}`)
  return response.data
}

// 获取多个品种的实时行情
export const getMultipleTicks = async (symbols: string[]): Promise<ApiResponse<TickData[]>> => {
  const response = await httpClient.post<TickData[]>('/market/ticks', { symbols })
  return response.data
}

// 获取K线数据
export const getKlineData = async (params: MarketDataRequest): Promise<ApiResponse<BarData[]>> => {
  const response = await httpClient.get<BarData[]>('/market/kline', { params })
  return response.data
}

// 获取深度数据
export const getDepthData = async (symbol: string): Promise<ApiResponse<DepthData>> => {
  const response = await httpClient.get<DepthData>(`/market/depth/${symbol}`)
  return response.data
}

// 获取交易品种列表
export const getSymbols = async (params?: QueryParams): Promise<ListResponse<SymbolInfo>> => {
  const response = await httpClient.get<SymbolInfo[]>('/market/symbols', { params })
  return response.data
}

// 获取品种详情
export const getSymbolInfo = async (symbol: string): Promise<ApiResponse<SymbolInfo>> => {
  const response = await httpClient.get<SymbolInfo>(`/market/symbol/${symbol}`)
  return response.data
}

// 搜索交易品种
export const searchSymbols = async (keyword: string): Promise<ApiResponse<SymbolInfo[]>> => {
  const response = await httpClient.get<SymbolInfo[]>('/market/search', { 
    params: { q: keyword } 
  })
  return response.data
}

// 获取热门品种
export const getHotSymbols = async (limit: number = 10): Promise<ApiResponse<SymbolInfo[]>> => {
  const response = await httpClient.get<SymbolInfo[]>('/market/hot', { 
    params: { limit } 
  })
  return response.data
}

// 获取涨跌幅排行
export const getRankingList = async (
  type: 'gainers' | 'losers' | 'active',
  limit: number = 20
): Promise<ApiResponse<TickData[]>> => {
  const response = await httpClient.get<TickData[]>(`/market/ranking/${type}`, { 
    params: { limit } 
  })
  return response.data
}

// 获取市场统计
export const getMarketStats = async (): Promise<ApiResponse<any>> => {
  const response = await httpClient.get<any>('/market/stats')
  return response.data
}

// 获取交易日历
export const getTradingCalendar = async (
  startDate: string,
  endDate: string
): Promise<ApiResponse<any[]>> => {
  const response = await httpClient.get<any[]>('/market/calendar', {
    params: { startDate, endDate }
  })
  return response.data
}

// 获取历史波动率
export const getHistoricalVolatility = async (
  symbol: string,
  period: number = 20
): Promise<ApiResponse<number[]>> => {
  const response = await httpClient.get<number[]>(`/market/volatility/${symbol}`, {
    params: { period }
  })
  return response.data
}

// 获取技术指标数据
export const getTechnicalIndicators = async (
  symbol: string,
  indicators: string[],
  params?: Record<string, any>
): Promise<ApiResponse<Record<string, number[]>>> => {
  const response = await httpClient.post<Record<string, number[]>>('/market/indicators', {
    symbol,
    indicators,
    params
  })
  return response.data
}

// 订阅实时行情
export const subscribeMarketData = async (symbols: string[]): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/market/subscribe', { symbols })
  return response.data
}

// 取消订阅实时行情
export const unsubscribeMarketData = async (symbols: string[]): Promise<ApiResponse<void>> => {
  const response = await httpClient.post<void>('/market/unsubscribe', { symbols })
  return response.data
}

// 获取当前订阅列表
export const getSubscriptions = async (): Promise<ApiResponse<string[]>> => {
  const response = await httpClient.get<string[]>('/market/subscriptions')
  return response.data
}

