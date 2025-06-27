// Portfolio related types
export interface Portfolio {
  id: string
  name: string
  description?: string
  type: 'stock' | 'fund' | 'mixed'
  currency: string
  totalValue: number
  cashBalance: number
  availableCash: number
  createdAt: string
  updatedAt: string
}

export interface PortfolioPosition {
  id: string
  portfolioId: string
  symbol: string
  name: string
  quantity: number
  avgCost: number
  currentPrice: number
  marketValue: number
  costBasis: number
  unrealizedPnL: number
  unrealizedPnLPercent: number
  weight: number
  sector?: string
  industry?: string
  updatedAt: string
}

export interface PortfolioPerformance {
  portfolioId: string
  period: 'day' | 'week' | 'month' | 'quarter' | 'year' | 'ytd' | 'all'
  totalReturn: number
  totalReturnPercent: number
  benchmark?: string
  benchmarkReturn?: number
  alpha?: number
  beta?: number
  sharpeRatio?: number
  maxDrawdown?: number
  volatility?: number
  winRate?: number
  profitFactor?: number
  calmarRatio?: number
  sortinoRatio?: number
  calculatedAt: string
}

export interface PortfolioAllocation {
  type: 'sector' | 'industry' | 'region' | 'currency' | 'asset_class'
  name: string
  value: number
  percentage: number
  color?: string
}

export interface PortfolioSummary {
  totalValue: number
  totalPnL: number
  totalPnLPercent: number
  positionCount: number
  cashBalance: number
  availableCash: number
}

export interface PortfolioTransaction {
  id: string
  portfolioId: string
  type: 'buy' | 'sell' | 'dividend' | 'split' | 'deposit' | 'withdrawal'
  symbol?: string
  quantity?: number
  price?: number
  amount: number
  fee?: number
  description?: string
  executedAt: string
  createdAt: string
}

export interface PortfolioAnalysis {
  portfolioId: string
  riskMetrics: {
    var95: number
    var99: number
    expectedShortfall: number
    maxDrawdown: number
    volatility: number
  }
  performanceMetrics: {
    totalReturn: number
    annualizedReturn: number
    sharpeRatio: number
    sortinoRatio: number
    calmarRatio: number
  }
  attribution: {
    assetAllocation: number
    stockSelection: number
    interaction: number
    total: number
  }
  recommendations: string[]
  generatedAt: string
}
