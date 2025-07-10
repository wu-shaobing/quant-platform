/**
 * 风险管理相关类型定义
 */

// 风险预警级别
export type RiskAlertLevel = 'info' | 'warning' | 'critical'

// 风险预警
export interface RiskAlert {
  id: string
  title: string
  message: string
  level: RiskAlertLevel
  source: string
  timestamp: string
  data?: any
  acknowledged?: boolean
  acknowledgedAt?: string
  acknowledgedBy?: string
}

// 风险规则类型
export type RiskRuleType = 
  | 'concentration'    // 持仓集中度
  | 'daily_loss'       // 单日亏损
  | 'max_drawdown'     // 最大回撤
  | 'leverage'         // 杠杆比例
  | 'volatility'       // 波动率
  | 'beta'             // Beta值
  | 'var'              // VaR风险

// 通知方式
export type NotificationMethod = 'popup' | 'email' | 'sms' | 'webhook'

// 检查频率
export type CheckFrequency = 'realtime' | '1min' | '5min' | '1hour' | 'daily'

// 风险规则
export interface RiskRule {
  id: string
  name: string
  description?: string
  type: RiskRuleType
  level: RiskAlertLevel
  threshold: number
  frequency: CheckFrequency
  notificationMethods: NotificationMethod[]
  enabled: boolean
  createdAt: string
  updatedAt: string
  lastTriggered?: string
  triggerCount: number
}

// 风险指标
export interface RiskMetric {
  name: string
  value: number
  threshold?: number
  status: 'safe' | 'warning' | 'danger'
  description?: string
  unit?: string
}

// 风险报告
export interface RiskReport {
  id: string
  title: string
  generatedAt: string
  period: {
    start: string
    end: string
  }
  summary: {
    totalAlerts: number
    criticalAlerts: number
    warningAlerts: number
    infoAlerts: number
    riskLevel: number
  }
  metrics: RiskMetric[]
  alerts: RiskAlert[]
  recommendations: string[]
}

// 投资组合风险
export interface PortfolioRisk {
  totalValue: number
  var: number           // Value at Risk
  cvar: number          // Conditional VaR
  maxDrawdown: number   // 最大回撤
  sharpeRatio: number   // 夏普比率
  beta: number          // Beta值
  volatility: number    // 波动率
  concentration: {      // 持仓集中度
    topHoldings: number
    sectors: Record<string, number>
    regions: Record<string, number>
  }
  leverage: number      // 杠杆比例
  liquidityRisk: number // 流动性风险
}

// 风险限额
export interface RiskLimit {
  id: string
  name: string
  type: 'absolute' | 'percentage'
  value: number
  currentValue: number
  utilization: number   // 使用率 (0-1)
  status: 'safe' | 'warning' | 'exceeded'
  description?: string
}

// 风险归因
export interface RiskAttribution {
  factor: string
  contribution: number
  percentage: number
  description?: string
}

// 压力测试场景
export interface StressTestScenario {
  id: string
  name: string
  description: string
  parameters: {
    marketShock: number
    sectorShocks: Record<string, number>
    correlationShift: number
    volatilityMultiplier: number
  }
  results?: {
    portfolioImpact: number
    var: number
    expectedShortfall: number
    worstCaseScenario: number
  }
}

// 风险监控配置
export interface RiskMonitoringConfig {
  enabled: boolean
  checkInterval: string
  historyRetentionDays: number
  maxAlerts: number
  alertChannels: {
    popup: boolean
    email: boolean
    sms: boolean
    webhook: boolean
  }
  thresholds: {
    var: number
    maxDrawdown: number
    concentration: number
    leverage: number
    volatility: number
  }
}

// 风险事件
export interface RiskEvent {
  id: string
  type: 'breach' | 'alert' | 'recovery'
  title: string
  description: string
  severity: RiskAlertLevel
  timestamp: string
  source: string
  affectedAssets: string[]
  impact: {
    financial: number
    operational: string
  }
  resolution?: {
    action: string
    timestamp: string
    responsible: string
  }
}