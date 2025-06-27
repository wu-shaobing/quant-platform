/**
 * 回测系统相关类型定义
 */

// 回测状态
export type BacktestStatus = 
  | 'pending'     // 等待中
  | 'running'     // 运行中
  | 'completed'   // 已完成
  | 'failed'      // 失败
  | 'cancelled'   // 已取消

// 回测频率
export type BacktestFrequency = 'daily' | 'weekly' | 'monthly'

// 策略类型
export type StrategyType = '趋势跟踪' | '技术指标' | '均值回归' | '超买超卖' | '套利' | '量化选股'

// 回测表单数据
export interface BacktestFormData {
  name: string                  // 回测名称
  strategyId: string            // 策略ID
  stockPool: string[]           // 股票池
  dateRange: [Date, Date]       // 时间区间
  frequency: BacktestFrequency  // 交易频率
  initialCapital: number        // 初始资金
  commission: number            // 手续费率
  stampTax: number              // 印花税率
  maxDrawdown: number           // 最大回撤限制
  maxPositionRatio: number      // 单股持仓上限
}

// 策略信息
export interface Strategy {
  id: string                    // 策略ID
  name: string                  // 策略名称
  type: StrategyType            // 策略类型
  description?: string          // 策略描述
  parameters?: Record<string, any> // 策略参数
  createTime?: number           // 创建时间
  updateTime?: number           // 更新时间
}

// 股票信息
export interface Stock {
  symbol: string                // 股票代码
  name: string                  // 股票名称
  market?: string               // 市场
  industry?: string             // 行业
  sector?: string               // 板块
}

// 回测任务
export interface BacktestTask {
  id: string                    // 任务ID
  name: string                  // 任务名称
  strategyId: string            // 策略ID
  strategyName: string          // 策略名称
  status: BacktestStatus        // 状态
  progress: number              // 进度 (0-100)
  config: BacktestConfig        // 配置
  result?: BacktestResult       // 结果
  createTime: number            // 创建时间
  startTime?: number            // 开始时间
  endTime?: number              // 结束时间
  errorMessage?: string         // 错误信息
}

// 回测配置
export interface BacktestConfig {
  stockPool: string[]           // 股票池
  startDate: string             // 开始日期
  endDate: string               // 结束日期
  frequency: BacktestFrequency  // 交易频率
  initialCapital: number        // 初始资金
  commission: number            // 手续费率
  stampTax: number              // 印花税率
  slippage: number              // 滑点
  maxDrawdown: number           // 最大回撤限制
  maxPositionRatio: number      // 单股持仓上限
  riskControl: {
    stopLoss?: number           // 止损比例
    takeProfit?: number         // 止盈比例
    maxLeverage: number         // 最大杠杆
  }
}

// 回测结果
export interface BacktestResult {
  summary: BacktestSummary      // 汇总指标
  performance: PerformanceMetrics // 绩效指标
  riskMetrics: RiskMetrics      // 风险指标
  trades: BacktestTrade[]       // 交易记录
  positions: BacktestPosition[] // 持仓记录
  equity: EquityPoint[]         // 净值曲线
  drawdown: DrawdownPoint[]     // 回撤曲线
  monthlyReturns: MonthlyReturn[] // 月度收益
  yearlyReturns: YearlyReturn[] // 年度收益
  benchmarkComparison?: BenchmarkComparison // 基准对比
}

// 回测汇总
export interface BacktestSummary {
  totalReturn: number           // 总收益率
  annualizedReturn: number      // 年化收益率
  volatility: number            // 波动率
  sharpeRatio: number           // 夏普比率
  maxDrawdown: number           // 最大回撤
  calmarRatio: number           // 卡玛比率
  winRate: number               // 胜率
  totalTrades: number           // 总交易次数
  avgHoldingDays: number        // 平均持仓天数
  turnoverRate: number          // 换手率
  finalValue: number            // 最终价值
}

// 绩效指标
export interface PerformanceMetrics {
  totalReturn: number           // 总收益率
  annualizedReturn: number      // 年化收益率
  excessReturn: number          // 超额收益率
  alpha: number                 // Alpha
  beta: number                  // Beta
  informationRatio: number      // 信息比率
  trackingError: number         // 跟踪误差
  treynorRatio: number          // 特雷诺比率
  jensenAlpha: number           // 詹森Alpha
}

// 风险指标
export interface RiskMetrics {
  volatility: number            // 波动率
  downSideDeviation: number     // 下行标准差
  maxDrawdown: number           // 最大回撤
  maxDrawdownDuration: number   // 最大回撤持续时间
  var95: number                 // 95% VaR
  var99: number                 // 99% VaR
  expectedShortfall: number     // 期望损失
  sharpeRatio: number           // 夏普比率
  sortinoRatio: number          // 索提诺比率
  calmarRatio: number           // 卡玛比率
  omegaRatio: number            // 欧米伽比率
}

// 回测交易记录
export interface BacktestTrade {
  id: string                    // 交易ID
  symbol: string                // 股票代码
  name: string                  // 股票名称
  side: 'buy' | 'sell'          // 买卖方向
  quantity: number              // 数量
  price: number                 // 价格
  amount: number                // 金额
  commission: number            // 手续费
  date: string                  // 交易日期
  timestamp: number             // 时间戳
  pnl?: number                  // 盈亏
  pnlPercent?: number           // 盈亏率
  holdingDays?: number          // 持仓天数
}

// 回测持仓记录
export interface BacktestPosition {
  date: string                  // 日期
  symbol: string                // 股票代码
  name: string                  // 股票名称
  quantity: number              // 持仓数量
  price: number                 // 持仓价格
  marketValue: number           // 市值
  weight: number                // 权重
  pnl: number                   // 盈亏
  pnlPercent: number            // 盈亏率
}

// 净值点
export interface EquityPoint {
  date: string                  // 日期
  timestamp: number             // 时间戳
  equity: number                // 净值
  benchmark?: number            // 基准净值
  cash: number                  // 现金
  positions: number             // 持仓市值
  totalValue: number            // 总价值
}

// 回撤点
export interface DrawdownPoint {
  date: string                  // 日期
  timestamp: number             // 时间戳
  drawdown: number              // 回撤幅度
  underwater: number            // 水下时间
  peak: number                  // 峰值
  valley: number                // 谷值
}

// 月度收益
export interface MonthlyReturn {
  year: number                  // 年份
  month: number                 // 月份
  return: number                // 收益率
  benchmark?: number            // 基准收益率
  excess?: number               // 超额收益率
}

// 年度收益
export interface YearlyReturn {
  year: number                  // 年份
  return: number                // 收益率
  volatility: number            // 波动率
  sharpe: number                // 夏普比率
  maxDrawdown: number           // 最大回撤
  benchmark?: number            // 基准收益率
}

// 基准对比
export interface BenchmarkComparison {
  benchmark: string             // 基准名称
  strategyReturn: number        // 策略收益率
  benchmarkReturn: number       // 基准收益率
  excessReturn: number          // 超额收益率
  trackingError: number         // 跟踪误差
  informationRatio: number      // 信息比率
  beta: number                  // Beta
  alpha: number                 // Alpha
  correlation: number           // 相关性
}

// 回测报告
export interface BacktestReport {
  id: string                    // 报告ID
  taskId: string                // 任务ID
  title: string                 // 报告标题
  summary: string               // 摘要
  result: BacktestResult        // 详细结果
  charts: ReportChart[]         // 图表
  tables: ReportTable[]         // 表格
  generateTime: number          // 生成时间
  format: 'html' | 'pdf' | 'excel' // 格式
}

// 报告图表
export interface ReportChart {
  id: string                    // 图表ID
  title: string                 // 标题
  type: 'line' | 'bar' | 'pie' | 'scatter' // 类型
  data: any                     // 数据
  config: any                   // 配置
}

// 报告表格
export interface ReportTable {
  id: string                    // 表格ID
  title: string                 // 标题
  headers: string[]             // 表头
  rows: any[][]                 // 数据行
}

// 参数优化
export interface ParameterOptimization {
  id: string                    // 优化ID
  strategyId: string            // 策略ID
  parameters: OptimizationParameter[] // 优化参数
  objective: 'return' | 'sharpe' | 'calmar' | 'custom' // 优化目标
  method: 'grid' | 'random' | 'genetic' | 'bayesian' // 优化方法
  results: OptimizationResult[] // 优化结果
  bestParameters: Record<string, any> // 最优参数
  status: 'pending' | 'running' | 'completed' | 'failed'
}

// 优化参数
export interface OptimizationParameter {
  name: string                  // 参数名
  type: 'int' | 'float' | 'choice' // 参数类型
  min?: number                  // 最小值
  max?: number                  // 最大值
  step?: number                 // 步长
  choices?: any[]               // 选择列表
  default: any                  // 默认值
}

// 优化结果
export interface OptimizationResult {
  parameters: Record<string, any> // 参数组合
  metrics: BacktestSummary      // 绩效指标
  rank: number                  // 排名
  score: number                 // 得分
}

// 策略对比
export interface StrategyComparison {
  strategies: StrategyComparisonItem[] // 策略列表
  metrics: string[]             // 对比指标
  period: {
    start: string               // 开始日期
    end: string                 // 结束日期
  }
  benchmark?: string            // 基准
}

// 策略对比项
export interface StrategyComparisonItem {
  id: string                    // 策略ID
  name: string                  // 策略名称
  result: BacktestResult        // 回测结果
  rank: number                  // 排名
  selected: boolean             // 是否选中
}

// 回测实体接口
export interface Backtest {
  id: string
  name: string
  description?: string
  strategy: StrategyConfig
  parameters: BacktestParameters
  status: BacktestStatus
  createTime: number
  updateTime: number
  startTime?: number
  endTime?: number
  progress?: number
  result?: BacktestResult
}

// 回测创建数据接口
export interface BacktestCreateData {
  name: string
  description?: string
  strategy: StrategyConfig
  parameters: BacktestParameters
}

// 回测进度接口
export interface BacktestProgress {
  backtestId: string
  progress: number
  currentDate?: string
  status: BacktestStatus
  message?: string
  estimatedTimeRemaining?: number
}

// 回测性能接口
export interface BacktestPerformance {
  totalReturn: number
  annualizedReturn: number
  volatility: number
  sharpeRatio: number
  maxDrawdown: number
  calmarRatio: number
  informationRatio?: number
  alpha?: number
  beta?: number
  winRate: number
  profitFactor: number
  avgWin: number
  avgLoss: number
  maxWin: number
  maxLoss: number
  consecutiveWins: number
  consecutiveLosses: number
}

// 回测统计数据接口
export interface BacktestStatistics {
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: number
  avgHoldingDays: number
  turnoverRate: number
  commission: number
  slippage: number
  finalValue: number
  maxCapitalUsage: number
  avgCapitalUsage: number
}