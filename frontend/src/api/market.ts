/**
 * 市场数据 API
 */
import { http } from './http'
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
  OrderBookData
} from '@/types/market'



/**
 * 市场数据API类
 */
export class MarketAPI {
  /**
   * 获取实时行情
   */
  async getQuote(symbols: string | string[]): Promise<QuoteData[]> {
    const symbolList = Array.isArray(symbols) ? symbols : [symbols]
    
    const response = await http.get<QuoteData[]>(API_PATHS.MARKET.QUOTE, {
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
    const response = await http.get<QuoteData[]>(API_PATHS.MARKET.QUOTE, {
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
    const response = await http.get<KLineData[]>(API_PATHS.MARKET.KLINE, {
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
    const response = await http.get<KLineData[]>(`${API_PATHS.MARKET.KLINE}/history`, {
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
  async searchStocks(params: SearchParams): Promise<SearchResult[]> {
    const response = await http.get<SearchResult[]>(API_PATHS.MARKET.SEARCH, {
      params: {
        keyword: params.keyword,
        market: params.market,
        type: params.type,
        limit: params.limit || 20
      }
    })
    
    return response.data
  }

  /**
   * 获取市场概览
   */
  async getMarketOverview(): Promise<MarketOverview[]> {
    const response = await http.get<MarketOverview[]>(API_PATHS.MARKET.OVERVIEW)
    return response.data
  }

  /**
   * 获取指定市场概览
   */
  async getMarketOverviewByMarket(market: string): Promise<MarketOverview> {
    const response = await http.get<MarketOverview>(`${API_PATHS.MARKET.OVERVIEW}/${market}`)
    return response.data
  }

  /**
   * 获取板块数据
   */
  async getSectors(): Promise<SectorData[]> {
    const response = await http.get<SectorData[]>(API_PATHS.MARKET.SECTORS)
    return response.data
  }

  /**
   * 获取指定板块数据
   */
  async getSectorDetail(sectorCode: string): Promise<SectorData> {
    const response = await http.get<SectorData>(`${API_PATHS.MARKET.SECTORS}/${sectorCode}`)
    return response.data
  }

  /**
   * 获取指数列表
   */
  async getIndices(): Promise<QuoteData[]> {
    const response = await http.get<QuoteData[]>(API_PATHS.MARKET.INDICES)
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
    const response = await http.get<NewsData[]>(API_PATHS.MARKET.NEWS, {
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
    const response = await http.get<RankingData[]>(`${API_PATHS.MARKET.OVERVIEW}/ranking`, {
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
    const response = await http.get<{
      limitUp: RankingData[]
      limitDown: RankingData[]
    }>(`${API_PATHS.MARKET.OVERVIEW}/limit`)
    return response.data
  }

  /**
   * 获取龙虎榜数据
   */
  async getDragonTiger(date?: string): Promise<any[]> {
    const response = await http.get<any[]>(`${API_PATHS.MARKET.OVERVIEW}/dragon-tiger`, {
      params: { date }
    })
    return response.data
  }

  /**
   * 获取订单簿数据
   */
  async getOrderBook(symbol: string, level = 5): Promise<OrderBookData> {
    const response = await http.get<OrderBookData>(`${API_PATHS.MARKET.QUOTE}/orderbook`, {
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
    const response = await http.get<any[]>(`${API_PATHS.MARKET.QUOTE}/tick`, {
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
    const response = await http.get<any>(`${API_PATHS.MARKET.QUOTE}/info`, {
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
    const response = await http.get<any[]>(`${API_PATHS.MARKET.QUOTE}/financial`, {
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
    const response = await http.get<any[]>(`${API_PATHS.MARKET.KLINE}/indicator`, {
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
    const response = await http.get<MarketStatus[]>(`${API_PATHS.MARKET.OVERVIEW}/status`)
    return response.data
  }

  /**
   * 获取交易日历
   */
  async getTradingCalendar(year?: number): Promise<{
    tradingDays: string[]
    holidays: string[]
  }> {
    const response = await http.get<{
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
    const response = await http.get<any[]>(`${API_PATHS.MARKET.QUOTE}/announcements`, {
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
    const response = await http.get<any[]>(`${API_PATHS.MARKET.NEWS}/research`, {
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
    const response = await http.get<any[]>(`${API_PATHS.MARKET.QUOTE}/shareholders`, {
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
    const response = await http.get<QuoteData[]>(`${API_PATHS.MARKET.QUOTE}/same-industry`, {
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
    const response = await http.get<QuoteData[]>(`${API_PATHS.MARKET.QUOTE}/related`, {
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
    const response = await http.get<{
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
}

// 创建实例
export const marketApi = new MarketAPI()

// 导出默认实例
export default marketApi

