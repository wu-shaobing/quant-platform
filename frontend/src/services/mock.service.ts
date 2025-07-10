/**
 * Mock数据服务
 * 在后端API未完成时提供模拟数据支持
 */

import type { 
  QuoteData, 
  KLineData, 
  MarketOverview,
  SectorData,
  NewsData,
  RankingData
} from '@/types/market'
import type { 
  Account, 
  Position, 
  Order, 
  TradeRecord 
} from '@/types/trading'
import type { 
  Strategy,
  BacktestResult 
} from '@/types/strategy'

export class MockService {
  private static instance: MockService
  
  static getInstance(): MockService {
    if (!MockService.instance) {
      MockService.instance = new MockService()
    }
    return MockService.instance
  }

  // 延迟模拟网络请求
  private delay(ms: number = 300): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  // 生成随机价格变化
  private generatePriceChange(): { price: number; change: number; changePercent: number } {
    const basePrice = 10 + Math.random() * 200
    const change = (Math.random() - 0.5) * basePrice * 0.1
    const changePercent = (change / basePrice) * 100
    
    return {
      price: Number(basePrice.toFixed(2)),
      change: Number(change.toFixed(2)),
      changePercent: Number(changePercent.toFixed(2))
    }
  }

  // 模拟股票行情数据
  async getQuoteData(symbols: string[]): Promise<QuoteData[]> {
    await this.delay()
    
    return symbols.map(symbol => {
      const { price, change, changePercent } = this.generatePriceChange()
      const volume = Math.floor(Math.random() * 100000000)
      
      return {
        symbol,
        name: this.getStockName(symbol),
        currentPrice: price,
        openPrice: price - change,
        highPrice: price + Math.random() * 5,
        lowPrice: price - Math.random() * 5,
        prevClosePrice: price - change,
        change,
        changePercent,
        volume,
        amount: volume * price,
        turnoverRate: Math.random() * 10,
        pe: 10 + Math.random() * 50,
        pb: 1 + Math.random() * 5,
        marketCap: volume * price * 100,
        timestamp: Date.now()
      }
    })
  }

  // 模拟K线数据
  async getKLineData(symbol: string, period: string, limit: number = 100): Promise<KLineData[]> {
    await this.delay()
    
    const data: KLineData[] = []
    let basePrice = 50 + Math.random() * 100
    const now = Date.now()
    const periodMs = this.getPeriodMs(period)
    
    for (let i = limit - 1; i >= 0; i--) {
      const timestamp = now - i * periodMs
      const change = (Math.random() - 0.5) * basePrice * 0.05
      
      const open = basePrice
      const close = basePrice + change
      const high = Math.max(open, close) + Math.random() * basePrice * 0.02
      const low = Math.min(open, close) - Math.random() * basePrice * 0.02
      const volume = Math.floor(Math.random() * 10000000)
      
      data.push({
        symbol,
        timestamp,
        open: Number(open.toFixed(2)),
        high: Number(high.toFixed(2)),
        low: Number(low.toFixed(2)),
        close: Number(close.toFixed(2)),
        volume,
        amount: volume * close,
        changePercent: Number(((close - open) / open * 100).toFixed(2))
      })
      
      basePrice = close
    }
    
    return data
  }

  // 模拟市场概览数据
  async getMarketOverview(): Promise<MarketOverview[]> {
    await this.delay()
    
    const indices = ['SH000001', 'SZ399001', 'SZ399006', 'SH000688']
    
    return indices.map(symbol => {
      const { price, change, changePercent } = this.generatePriceChange()
      return {
        symbol,
        name: this.getIndexName(symbol),
        currentPrice: price * 100, // 指数价格更高
        change: change * 10,
        changePercent,
        volume: Math.floor(Math.random() * 1000000000),
        amount: Math.floor(Math.random() * 500000000000),
        timestamp: Date.now()
      }
    })
  }

  // 模拟排行榜数据
  async getRankingData(type: 'gainers' | 'losers' | 'volume'): Promise<RankingData[]> {
    await this.delay()
    
    const stocks = this.generateMockStocks(20)
    
    switch (type) {
      case 'gainers':
        return stocks.sort((a, b) => b.changePercent - a.changePercent).slice(0, 10)
      case 'losers':
        return stocks.sort((a, b) => a.changePercent - b.changePercent).slice(0, 10)
      case 'volume':
        return stocks.sort((a, b) => b.amount - a.amount).slice(0, 10)
      default:
        return stocks.slice(0, 10)
    }
  }

  // 模拟板块数据
  async getSectorData(): Promise<SectorData[]> {
    await this.delay()
    
    const sectors = [
      { code: 'tech', name: '科技板块' },
      { code: 'finance', name: '金融板块' },
      { code: 'healthcare', name: '医疗板块' },
      { code: 'energy', name: '能源板块' },
      { code: 'consumer', name: '消费板块' },
      { code: 'industrial', name: '工业板块' },
      { code: 'materials', name: '材料板块' },
      { code: 'telecom', name: '通信板块' }
    ]
    
    return sectors.map(sector => {
      const { changePercent } = this.generatePriceChange()
      return {
        code: sector.code,
        name: sector.name,
        changePercent,
        stockCount: Math.floor(Math.random() * 200) + 50,
        marketCap: Math.floor(Math.random() * 1000000000000),
        leadingStocks: this.generateMockStocks(3)
      }
    })
  }

  // 模拟新闻数据
  async getNewsData(): Promise<NewsData[]> {
    await this.delay()
    
    const titles = [
      '央行宣布降准0.5个百分点，释放长期资金约1万亿元',
      '科技股集体上涨，AI概念持续火热',
      '新能源汽车销量再创新高，产业链受益',
      '房地产政策调整，相关板块异动',
      '医药板块分化明显，创新药企业受关注',
      '半导体行业景气度提升，龙头企业业绩亮眼',
      '消费板块回暖迹象明显，白酒股领涨',
      '银行股估值修复，金融板块表现强势'
    ]
    
    const sources = ['财经网', '证券时报', '证券日报', '第一财经', '经济观察报']
    
    return titles.map((title, index) => ({
      id: `news_${index + 1}`,
      title,
      content: `${title}。详细内容请查看完整报道...`,
      source: sources[Math.floor(Math.random() * sources.length)],
      publishTime: Date.now() - Math.random() * 86400000, // 随机时间
      category: Math.random() > 0.5 ? 'market' : 'policy',
      tags: ['股市', '投资'],
      url: `https://example.com/news/${index + 1}`
    }))
  }

  // 模拟账户数据
  async getAccountData(): Promise<Account> {
    await this.delay()
    
    const totalAssets = 100000 + Math.random() * 500000
    const availableCash = totalAssets * (0.1 + Math.random() * 0.3)
    const marketValue = totalAssets - availableCash
    const dailyProfit = (Math.random() - 0.5) * totalAssets * 0.05
    
    return {
      accountId: 'mock_account_001',
      totalAssets: Number(totalAssets.toFixed(2)),
      availableCash: Number(availableCash.toFixed(2)),
      frozenCash: Number((Math.random() * 1000).toFixed(2)),
      marketValue: Number(marketValue.toFixed(2)),
      totalProfit: Number((totalAssets * 0.15).toFixed(2)),
      totalProfitPercent: 15.0,
      dailyProfit: Number(dailyProfit.toFixed(2)),
      dailyProfitPercent: Number((dailyProfit / totalAssets * 100).toFixed(2)),
      commission: Number((Math.random() * 100).toFixed(2)),
      lastUpdateTime: Date.now()
    }
  }

  // 模拟持仓数据
  async getPositionsData(): Promise<Position[]> {
    await this.delay()
    
    const symbols = ['000001', '000002', '000858', '600036', '600519']
    
    return symbols.map(symbol => {
      const quantity = Math.floor(Math.random() * 2000) + 100
      const avgCost = 10 + Math.random() * 100
      const { price: currentPrice } = this.generatePriceChange()
      const marketValue = quantity * currentPrice
      const cost = quantity * avgCost
      const unrealizedPnl = marketValue - cost
      
      return {
        symbol,
        name: this.getStockName(symbol),
        totalQuantity: quantity,
        availableQuantity: quantity - Math.floor(quantity * 0.1),
        avgCost: Number(avgCost.toFixed(2)),
        currentPrice: Number(currentPrice.toFixed(2)),
        marketValue: Number(marketValue.toFixed(2)),
        cost: Number(cost.toFixed(2)),
        unrealizedPnl: Number(unrealizedPnl.toFixed(2)),
        unrealizedPnlPercent: Number((unrealizedPnl / cost * 100).toFixed(2)),
        todayPnl: Number((unrealizedPnl * 0.3).toFixed(2)),
        weight: Number((marketValue / 100000 * 100).toFixed(2))
      }
    })
  }

  // 模拟订单数据
  async getOrdersData(): Promise<Order[]> {
    await this.delay()
    
    const symbols = ['000001', '000002', '000858', '600036', '600519']
    const statuses = ['pending', 'partial', 'filled', 'cancelled']
    const sides = ['buy', 'sell']
    const types = ['limit', 'market']
    
    return symbols.map((symbol, index) => {
      const quantity = Math.floor(Math.random() * 1000) + 100
      const price = 10 + Math.random() * 100
      const filledQuantity = Math.floor(quantity * Math.random())
      
      return {
        id: `order_${index + 1}`,
        symbol,
        name: this.getStockName(symbol),
        side: sides[Math.floor(Math.random() * sides.length)] as 'buy' | 'sell',
        type: types[Math.floor(Math.random() * types.length)] as 'limit' | 'market',
        status: statuses[Math.floor(Math.random() * statuses.length)] as any,
        quantity,
        price: Number(price.toFixed(2)),
        filledQuantity,
        avgFilledPrice: Number((price * (0.98 + Math.random() * 0.04)).toFixed(2)),
        amount: Number((quantity * price).toFixed(2)),
        commission: Number((quantity * price * 0.0003).toFixed(2)),
        createTime: Date.now() - Math.random() * 86400000,
        updateTime: Date.now() - Math.random() * 3600000
      }
    })
  }

  // 模拟策略数据
  async getStrategiesData(): Promise<Strategy[]> {
    await this.delay()
    
    const strategies = [
      '均线策略',
      'MACD策略', 
      'RSI策略',
      '布林带策略',
      '网格策略'
    ]
    
    return strategies.map((name, index) => ({
      id: `strategy_${index + 1}`,
      name,
      description: `${name}的详细描述和实现逻辑`,
      code: `# ${name}示例代码\ndef strategy():\n    pass`,
      status: Math.random() > 0.5 ? 'running' : 'stopped',
      createTime: Date.now() - Math.random() * 2592000000,
      updateTime: Date.now() - Math.random() * 86400000,
      performance: {
        totalReturn: Number((Math.random() * 50 - 10).toFixed(2)),
        annualizedReturn: Number((Math.random() * 30 - 5).toFixed(2)),
        maxDrawdown: Number((Math.random() * 20).toFixed(2)),
        sharpeRatio: Number((Math.random() * 3).toFixed(2)),
        winRate: Number((50 + Math.random() * 40).toFixed(2)),
        profitFactor: Number((1 + Math.random() * 2).toFixed(2))
      }
    }))
  }

  // 辅助方法
  private getStockName(symbol: string): string {
    const names: Record<string, string> = {
      '000001': '平安银行',
      '000002': '万科A',
      '000858': '五粮液',
      '600036': '招商银行',
      '600519': '贵州茅台',
      '000063': '中兴通讯',
      '002415': '海康威视',
      '300059': '东方财富'
    }
    return names[symbol] || `股票${symbol}`
  }

  private getIndexName(symbol: string): string {
    const names: Record<string, string> = {
      'SH000001': '上证指数',
      'SZ399001': '深证成指',
      'SZ399006': '创业板指',
      'SH000688': '科创50'
    }
    return names[symbol] || symbol
  }

  private getPeriodMs(period: string): number {
    const periods: Record<string, number> = {
      '1m': 60 * 1000,
      '5m': 5 * 60 * 1000,
      '15m': 15 * 60 * 1000,
      '30m': 30 * 60 * 1000,
      '1h': 60 * 60 * 1000,
      '4h': 4 * 60 * 60 * 1000,
      '1d': 24 * 60 * 60 * 1000,
      '1w': 7 * 24 * 60 * 60 * 1000,
      '1M': 30 * 24 * 60 * 60 * 1000
    }
    return periods[period] || periods['1d']
  }

  private generateMockStocks(count: number): any[] {
    const symbols = [
      '000001', '000002', '000858', '600036', '600519',
      '000063', '002415', '300059', '002594', '000725'
    ]
    
    return Array.from({ length: count }, (_, index) => {
      const symbol = symbols[index % symbols.length] + (index > 9 ? index : '')
      const { price, change, changePercent } = this.generatePriceChange()
      const volume = Math.floor(Math.random() * 100000000)
      
      return {
        symbol,
        name: this.getStockName(symbol),
        currentPrice: price,
        change,
        changePercent,
        volume,
        amount: volume * price,
        industry: ['科技', '金融', '医疗', '能源', '消费'][Math.floor(Math.random() * 5)]
      }
    })
  }
}

// 导出单例
export const mockService = MockService.getInstance()
export default mockService 