// src/composables/risk/useRiskManagement.ts
import { ref, computed, watch } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import type { 
  RiskAlert, 
  RiskRule, 
  RiskMetric, 
  PortfolioRisk, 
  RiskLimit,
  RiskMonitoringConfig,
  RiskAlertLevel,
  RiskRuleType
} from '@/types/risk'

// 风险指标接口
export interface RiskIndicator {
  name: string
  value: number
  threshold: number
  status: 'safe' | 'warning' | 'danger'
  description: string
  unit?: string
}

// 风险事件接口
export interface RiskEvent {
  id: string
  type: 'position' | 'market' | 'liquidity' | 'credit' | 'operational'
  level: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  timestamp: number
  resolved: boolean
  actions?: string[]
}

// 风险配置接口
export interface RiskConfig {
  maxDrawdown: number          // 最大回撤限制
  maxPositionRatio: number     // 单股最大持仓比例
  maxLeverage: number          // 最大杠杆倍数
  stopLossRatio: number        // 止损比例
  dailyLossLimit: number       // 日亏损限额
  concentrationLimit: number   // 集中度限制
  liquidityThreshold: number   // 流动性阈值
  varThreshold: number         // VaR阈值
}

export function useRiskManagement() {
  // ============ 状态管理 ============
  
  const alerts = ref<RiskAlert[]>([])
  const riskRules = ref<RiskRule[]>([])
  const riskMetrics = ref<RiskMetric[]>([])
  const portfolioRisk = ref<PortfolioRisk | null>(null)
  const riskLimits = ref<RiskLimit[]>([])
  
  // 系统配置
  const systemEnabled = ref(true)
  const systemSettings = ref<RiskMonitoringConfig>({
    enabled: true,
    checkInterval: '10s',
    historyRetentionDays: 30,
    maxAlerts: 100,
    alertChannels: {
      popup: true,
      email: false,
      sms: false,
      webhook: false
    },
    thresholds: {
      var: 0.05,
      maxDrawdown: 0.1,
      concentration: 0.3,
      leverage: 2.0,
      volatility: 0.25
    }
  })
  
  // 监控状态
  const isMonitoring = ref(false)
  const monitoringInterval = ref<NodeJS.Timeout | null>(null)
  
  // ============ 计算属性 ============
  
  const activeAlerts = computed(() => 
    alerts.value.filter(alert => !alert.acknowledged)
  )
  
  const criticalAlertsCount = computed(() =>
    activeAlerts.value.filter(alert => alert.level === 'critical').length
  )
  
  const warningAlertsCount = computed(() =>
    activeAlerts.value.filter(alert => alert.level === 'warning').length
  )
  
  const infoAlertsCount = computed(() =>
    activeAlerts.value.filter(alert => alert.level === 'info').length
  )
  
  const activeRulesCount = computed(() =>
    riskRules.value.filter(rule => rule.enabled).length
  )
  
  // ============ 核心方法 ============
  
  // 创建风险规则
  const createRule = async (ruleData: Partial<RiskRule>): Promise<RiskRule> => {
    const rule: RiskRule = {
      id: `rule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: ruleData.name || '',
      description: ruleData.description,
      type: ruleData.type || 'concentration',
      level: ruleData.level || 'warning',
      threshold: ruleData.threshold || 0,
      frequency: ruleData.frequency || 'realtime',
      notificationMethods: ruleData.notificationMethods || ['popup'],
      enabled: ruleData.enabled !== false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      triggerCount: 0
    }
    
    riskRules.value.push(rule)
    
    // 实际项目中应该调用API保存
    // await riskApi.createRule(rule)
    
    return rule
  }
  
  // 更新风险规则
  const updateRule = async (ruleId: string, updates: Partial<RiskRule>): Promise<void> => {
    const index = riskRules.value.findIndex(rule => rule.id === ruleId)
    if (index === -1) {
      throw new Error('规则不存在')
    }
    
    riskRules.value[index] = {
      ...riskRules.value[index],
      ...updates,
      updatedAt: new Date().toISOString()
    }
    
    // 实际项目中应该调用API更新
    // await riskApi.updateRule(ruleId, updates)
  }
  
  // 删除风险规则
  const deleteRule = async (ruleId: string): Promise<void> => {
    const index = riskRules.value.findIndex(rule => rule.id === ruleId)
    if (index === -1) {
      throw new Error('规则不存在')
    }
    
    riskRules.value.splice(index, 1)
    
    // 实际项目中应该调用API删除
    // await riskApi.deleteRule(ruleId)
  }
  
  // 切换规则启用状态
  const toggleRule = async (rule: RiskRule): Promise<void> => {
    await updateRule(rule.id, { enabled: !rule.enabled })
  }
  
  // 创建风险预警
  const createAlert = (
    title: string,
    message: string,
    level: RiskAlertLevel,
    source: string,
    data?: any
  ): RiskAlert => {
    const alert: RiskAlert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      title,
      message,
      level,
      source,
      timestamp: new Date().toISOString(),
      data,
      acknowledged: false
    }
    
    alerts.value.unshift(alert)
    
    // 限制预警数量
    if (alerts.value.length > systemSettings.value.maxAlerts) {
      alerts.value = alerts.value.slice(0, systemSettings.value.maxAlerts)
    }
    
    // 发送通知
    sendNotification(alert)
    
    return alert
  }
  
  // 发送通知
  const sendNotification = (alert: RiskAlert): void => {
    const { alertChannels } = systemSettings.value
    
    // 弹窗通知
    if (alertChannels.popup) {
      const notificationType = alert.level === 'critical' ? 'error' : 
                              alert.level === 'warning' ? 'warning' : 'info'
      
      ElNotification({
        title: alert.title,
        message: alert.message,
        type: notificationType,
        duration: alert.level === 'critical' ? 0 : 6000,
        position: 'top-right'
      })
    }
    
    // 邮件通知（实际项目中实现）
    if (alertChannels.email) {
      // await emailService.sendAlert(alert)
    }
    
    // 短信通知（实际项目中实现）
    if (alertChannels.sms) {
      // await smsService.sendAlert(alert)
    }
    
    // Webhook通知（实际项目中实现）
    if (alertChannels.webhook) {
      // await webhookService.sendAlert(alert)
    }
  }
  
  // 确认预警
  const acknowledgeAlert = (alertId: string, acknowledgedBy?: string): void => {
    const alert = alerts.value.find(a => a.id === alertId)
    if (alert) {
      alert.acknowledged = true
      alert.acknowledgedAt = new Date().toISOString()
      alert.acknowledgedBy = acknowledgedBy
    }
  }
  
  // 清除单个预警
  const clearAlert = (alertId: string): void => {
    const index = alerts.value.findIndex(a => a.id === alertId)
    if (index !== -1) {
      alerts.value.splice(index, 1)
    }
  }
  
  // 清除所有预警
  const clearAllAlerts = (): void => {
    alerts.value = []
  }
  
  // 计算风险等级
  const calculateRiskLevel = (): number => {
    if (!portfolioRisk.value) return 0
    
    const risk = portfolioRisk.value
    let riskScore = 0
    
    // VaR风险评分 (0-25分)
    const varScore = Math.min(25, (risk.var / systemSettings.value.thresholds.var) * 25)
    riskScore += varScore
    
    // 最大回撤评分 (0-25分)
    const drawdownScore = Math.min(25, (Math.abs(risk.maxDrawdown) / systemSettings.value.thresholds.maxDrawdown) * 25)
    riskScore += drawdownScore
    
    // 持仓集中度评分 (0-25分)
    const concentrationScore = Math.min(25, (risk.concentration.topHoldings / systemSettings.value.thresholds.concentration) * 25)
    riskScore += concentrationScore
    
    // 杠杆比例评分 (0-25分)
    const leverageScore = Math.min(25, (risk.leverage / systemSettings.value.thresholds.leverage) * 25)
    riskScore += leverageScore
    
    return Math.min(100, riskScore)
  }
  
  // 检查风险规则
  const checkRiskRules = async (): Promise<void> => {
    if (!portfolioRisk.value) return
    
    const enabledRules = riskRules.value.filter(rule => rule.enabled)
    
    for (const rule of enabledRules) {
      const shouldTrigger = await evaluateRule(rule, portfolioRisk.value)
      
      if (shouldTrigger) {
        // 更新规则触发信息
        rule.lastTriggered = new Date().toISOString()
        rule.triggerCount++
        
        // 创建预警
        const alertTitle = getRuleAlertTitle(rule)
        const alertMessage = getRuleAlertMessage(rule, portfolioRisk.value)
        
        createAlert(
          alertTitle,
          alertMessage,
          rule.level,
          `风险规则: ${rule.name}`,
          {
            ruleId: rule.id,
            ruleName: rule.name,
            threshold: rule.threshold,
            currentValue: getCurrentRuleValue(rule, portfolioRisk.value)
          }
        )
      }
    }
  }
  
  // 评估规则是否应该触发
  const evaluateRule = async (rule: RiskRule, risk: PortfolioRisk): Promise<boolean> => {
    const currentValue = getCurrentRuleValue(rule, risk)
    
    switch (rule.type) {
      case 'concentration':
        return risk.concentration.topHoldings > rule.threshold / 100
      
      case 'daily_loss':
        // 这里需要实际的日收益数据
        return false // 暂时返回false，实际项目中需要计算日收益
      
      case 'max_drawdown':
        return Math.abs(risk.maxDrawdown) > rule.threshold / 100
      
      case 'leverage':
        return risk.leverage > rule.threshold
      
      case 'volatility':
        return risk.volatility > rule.threshold / 100
      
      case 'beta':
        return Math.abs(risk.beta) > rule.threshold
      
      case 'var':
        return risk.var > rule.threshold / 100
      
      default:
        return false
    }
  }
  
  // 获取规则当前值
  const getCurrentRuleValue = (rule: RiskRule, risk: PortfolioRisk): number => {
    switch (rule.type) {
      case 'concentration':
        return risk.concentration.topHoldings * 100
      case 'max_drawdown':
        return Math.abs(risk.maxDrawdown) * 100
      case 'leverage':
        return risk.leverage
      case 'volatility':
        return risk.volatility * 100
      case 'beta':
        return risk.beta
      case 'var':
        return risk.var * 100
      default:
        return 0
    }
  }
  
  // 获取规则预警标题
  const getRuleAlertTitle = (rule: RiskRule): string => {
    const typeLabels = {
      concentration: '持仓集中度超限',
      daily_loss: '单日亏损超限',
      max_drawdown: '最大回撤超限',
      leverage: '杠杆比例超限',
      volatility: '波动率超限',
      beta: 'Beta值超限',
      var: 'VaR风险超限'
    }
    
    return typeLabels[rule.type] || '风险规则触发'
  }
  
  // 获取规则预警消息
  const getRuleAlertMessage = (rule: RiskRule, risk: PortfolioRisk): string => {
    const currentValue = getCurrentRuleValue(rule, risk)
    const unit = getThresholdUnit(rule.type)
    
    return `${rule.name}: 当前值 ${currentValue.toFixed(2)}${unit}，超过阈值 ${rule.threshold}${unit}`
  }
  
  // 获取阈值单位
  const getThresholdUnit = (type: RiskRuleType): string => {
    const unitMap = {
      concentration: '%',
      daily_loss: '%',
      max_drawdown: '%',
      leverage: '倍',
      volatility: '%',
      beta: '',
      var: '%'
    }
    return unitMap[type] || ''
  }
  
  // 开始监控
  const startMonitoring = (): void => {
    if (isMonitoring.value) return
    
    isMonitoring.value = true
    systemEnabled.value = true
    
    // 设置定时检查
    const intervalMs = parseInterval(systemSettings.value.checkInterval)
    monitoringInterval.value = setInterval(async () => {
      try {
        await checkRiskRules()
      } catch (error) {
        console.error('风险检查失败:', error)
      }
    }, intervalMs)
    
    ElMessage.success('风险监控系统已启动')
  }
  
  // 停止监控
  const stopMonitoring = (): void => {
    if (!isMonitoring.value) return
    
    isMonitoring.value = false
    systemEnabled.value = false
    
    if (monitoringInterval.value) {
      clearInterval(monitoringInterval.value)
      monitoringInterval.value = null
    }
    
    ElMessage.success('风险监控系统已停止')
  }
  
  // 解析时间间隔
  const parseInterval = (interval: string): number => {
    const intervalMap = {
      '1s': 1000,
      '5s': 5000,
      '10s': 10000,
      '30s': 30000,
      '1min': 60000,
      '5min': 300000,
      '1hour': 3600000,
      'daily': 86400000
    }
    
    return intervalMap[interval] || 10000
  }
  
  // 更新投资组合风险数据
  const updatePortfolioRisk = (risk: PortfolioRisk): void => {
    portfolioRisk.value = risk
  }
  
  // 初始化默认规则
  const initializeDefaultRules = async (): Promise<void> => {
    const defaultRules = [
      {
        name: '持仓集中度预警',
        type: 'concentration' as RiskRuleType,
        level: 'warning' as RiskAlertLevel,
        threshold: 30,
        frequency: 'realtime' as const,
        notificationMethods: ['popup' as const],
        description: '当单一持仓占比超过30%时触发预警'
      },
      {
        name: '最大回撤预警',
        type: 'max_drawdown' as RiskRuleType,
        level: 'critical' as RiskAlertLevel,
        threshold: 10,
        frequency: 'realtime' as const,
        notificationMethods: ['popup' as const, 'email' as const],
        description: '当最大回撤超过10%时触发严重预警'
      },
      {
        name: '杠杆比例预警',
        type: 'leverage' as RiskRuleType,
        level: 'warning' as RiskAlertLevel,
        threshold: 2,
        frequency: 'realtime' as const,
        notificationMethods: ['popup' as const],
        description: '当杠杆比例超过2倍时触发预警'
      }
    ]
    
    for (const ruleData of defaultRules) {
      await createRule(ruleData)
    }
  }
  
  // ============ 初始化 ============
  
  // 初始化模拟数据
  const initializeMockData = (): void => {
    // 模拟投资组合风险数据
    portfolioRisk.value = {
      totalValue: 1000000,
      var: 0.03,
      cvar: 0.045,
      maxDrawdown: -0.08,
      sharpeRatio: 1.2,
      beta: 1.1,
      volatility: 0.18,
      concentration: {
        topHoldings: 0.25,
        sectors: {
          '科技': 0.35,
          '金融': 0.25,
          '消费': 0.20,
          '医疗': 0.15,
          '其他': 0.05
        },
        regions: {
          '国内': 0.80,
          '美国': 0.15,
          '其他': 0.05
        }
      },
      leverage: 1.5,
      liquidityRisk: 0.02
    }
    
    // 初始化默认规则
    initializeDefaultRules()
  }
  
  // 在组合函数初始化时调用
  initializeMockData()
  
  return {
    // 状态
    alerts,
    riskRules,
    riskMetrics,
    portfolioRisk,
    riskLimits,
    systemEnabled,
    systemSettings,
    isMonitoring,
    
    // 计算属性
    activeAlerts,
    criticalAlertsCount,
    warningAlertsCount,
    infoAlertsCount,
    activeRulesCount,
    
    // 方法
    createRule,
    updateRule,
    deleteRule,
    toggleRule,
    createAlert,
    acknowledgeAlert,
    clearAlert,
    clearAllAlerts,
    calculateRiskLevel,
    checkRiskRules,
    startMonitoring,
    stopMonitoring,
    updatePortfolioRisk,
    initializeDefaultRules
  }
}