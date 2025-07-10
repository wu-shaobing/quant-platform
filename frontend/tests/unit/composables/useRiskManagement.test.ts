/**
 * 风险管理组合函数测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ref } from 'vue'
import { useRiskManagement } from '@/composables/risk/useRiskManagement'
import type { RiskRule, RiskAlert, PortfolioRisk } from '@/types/risk'

// Mock API
vi.mock('@/api/risk', () => ({
  riskApi: {
    getRiskMetrics: vi.fn(),
    getRiskAlerts: vi.fn(),
    createRiskAlert: vi.fn(),
    updateRiskAlert: vi.fn(),
    deleteRiskAlert: vi.fn(),
    getRiskRules: vi.fn(),
    createRiskRule: vi.fn(),
    updateRiskRule: vi.fn(),
    deleteRiskRule: vi.fn(),
    runRiskMonitoring: vi.fn()
  }
}))

describe('useRiskManagement', () => {
  let riskManagement: ReturnType<typeof useRiskManagement>

  beforeEach(() => {
    riskManagement = useRiskManagement()
    // 重置状态
    riskManagement.alerts.value = []
    riskManagement.riskRules.value = []
    riskManagement.riskMetrics.value = []
    riskManagement.portfolioRisk.value = null
  })

  describe('状态管理', () => {
    it('应该正确初始化状态', () => {
      expect(riskManagement.alerts.value).toEqual([])
      expect(riskManagement.riskRules.value).toEqual([])
      expect(riskManagement.riskMetrics.value).toEqual([])
      expect(riskManagement.portfolioRisk.value).toBeNull()
      expect(riskManagement.systemEnabled.value).toBe(true)
    })

    it('应该正确设置系统配置', () => {
      const settings = riskManagement.systemSettings.value
      expect(settings.enabled).toBe(true)
      expect(settings.checkInterval).toBe('10s')
      expect(settings.historyRetentionDays).toBe(30)
      expect(settings.maxAlerts).toBe(100)
      expect(settings.thresholds.var).toBe(0.05)
      expect(settings.thresholds.maxDrawdown).toBe(0.1)
    })
  })

  describe('预警管理', () => {
    it('应该能够创建预警', async () => {
      const alertTitle = '持仓集中度超限'
      const alertMessage = '前5大持仓占比超过30%'
      const severity = 'high' as const
      const source = '风险监控系统'

      await riskManagement.createAlert(alertTitle, alertMessage, severity, source)

      expect(riskManagement.alerts.value).toHaveLength(1)
      const alert = riskManagement.alerts.value[0]
      expect(alert.title).toBe(alertTitle)
      expect(alert.message).toBe(alertMessage)
      expect(alert.severity).toBe(severity)
      expect(alert.source).toBe(source)
      expect(alert.status).toBe('active')
    })

    it('应该能够确认预警', async () => {
      // 先创建一个预警
      await riskManagement.createAlert('测试预警', '测试消息', 'medium', '测试')
      const alertId = riskManagement.alerts.value[0].id

      // 确认预警
      await riskManagement.acknowledgeAlert(alertId)

      const alert = riskManagement.alerts.value.find(a => a.id === alertId)
      expect(alert?.status).toBe('acknowledged')
      expect(alert?.acknowledgedAt).toBeDefined()
    })

    it('应该能够清除预警', async () => {
      // 先创建一个预警
      await riskManagement.createAlert('测试预警', '测试消息', 'low', '测试')
      const alertId = riskManagement.alerts.value[0].id

      // 清除预警
      await riskManagement.clearAlert(alertId)

      expect(riskManagement.alerts.value).toHaveLength(0)
    })

    it('应该能够清除所有预警', async () => {
      // 创建多个预警
      await riskManagement.createAlert('预警1', '消息1', 'high', '测试')
      await riskManagement.createAlert('预警2', '消息2', 'medium', '测试')
      await riskManagement.createAlert('预警3', '消息3', 'low', '测试')

      expect(riskManagement.alerts.value).toHaveLength(3)

      // 清除所有预警
      await riskManagement.clearAllAlerts()

      expect(riskManagement.alerts.value).toHaveLength(0)
    })

    it('应该正确计算活跃预警', async () => {
      // 创建不同状态的预警
      await riskManagement.createAlert('活跃预警1', '消息1', 'high', '测试')
      await riskManagement.createAlert('活跃预警2', '消息2', 'medium', '测试')
      
      // 确认一个预警
      const alertId = riskManagement.alerts.value[0].id
      await riskManagement.acknowledgeAlert(alertId)

      const activeAlerts = riskManagement.activeAlerts.value
      expect(activeAlerts).toHaveLength(1)
      expect(activeAlerts[0].title).toBe('活跃预警2')
    })

    it('应该正确计算不同严重程度的预警数量', async () => {
      // 创建不同严重程度的预警
      await riskManagement.createAlert('严重预警1', '消息1', 'critical', '测试')
      await riskManagement.createAlert('严重预警2', '消息2', 'critical', '测试')
      await riskManagement.createAlert('高风险预警', '消息3', 'high', '测试')
      await riskManagement.createAlert('中风险预警', '消息4', 'medium', '测试')
      await riskManagement.createAlert('低风险预警', '消息5', 'low', '测试')
      await riskManagement.createAlert('信息预警', '消息6', 'info', '测试')

      expect(riskManagement.criticalAlertsCount.value).toBe(2)
      expect(riskManagement.warningAlertsCount.value).toBe(2) // high + medium
      expect(riskManagement.infoAlertsCount.value).toBe(2) // low + info
    })
  })

  describe('风险规则管理', () => {
    it('应该能够创建风险规则', async () => {
      const ruleData = {
        name: '持仓集中度限制',
        type: 'concentration' as const,
        threshold: 30,
        level: 'high' as const,
        enabled: true,
        description: '前5大持仓占比不得超过30%'
      }

      await riskManagement.createRule(ruleData)

      expect(riskManagement.riskRules.value).toHaveLength(1)
      const rule = riskManagement.riskRules.value[0]
      expect(rule.name).toBe(ruleData.name)
      expect(rule.type).toBe(ruleData.type)
      expect(rule.threshold).toBe(ruleData.threshold)
      expect(rule.enabled).toBe(true)
    })

    it('应该能够更新风险规则', async () => {
      // 先创建一个规则
      await riskManagement.createRule({
        name: '测试规则',
        type: 'var',
        threshold: 5,
        level: 'medium',
        enabled: true,
        description: '测试描述'
      })

      const ruleId = riskManagement.riskRules.value[0].id
      const updateData = {
        threshold: 8,
        level: 'high' as const,
        description: '更新后的描述'
      }

      await riskManagement.updateRule(ruleId, updateData)

      const updatedRule = riskManagement.riskRules.value[0]
      expect(updatedRule.threshold).toBe(8)
      expect(updatedRule.level).toBe('high')
      expect(updatedRule.description).toBe('更新后的描述')
    })

    it('应该能够删除风险规则', async () => {
      // 先创建一个规则
      await riskManagement.createRule({
        name: '测试规则',
        type: 'leverage',
        threshold: 2,
        level: 'medium',
        enabled: true,
        description: '测试描述'
      })

      const ruleId = riskManagement.riskRules.value[0].id
      await riskManagement.deleteRule(ruleId)

      expect(riskManagement.riskRules.value).toHaveLength(0)
    })

    it('应该能够切换规则启用状态', async () => {
      // 先创建一个规则
      await riskManagement.createRule({
        name: '测试规则',
        type: 'volatility',
        threshold: 25,
        level: 'medium',
        enabled: true,
        description: '测试描述'
      })

      const ruleId = riskManagement.riskRules.value[0].id
      
      // 禁用规则
      await riskManagement.toggleRule(ruleId)
      expect(riskManagement.riskRules.value[0].enabled).toBe(false)

      // 启用规则
      await riskManagement.toggleRule(ruleId)
      expect(riskManagement.riskRules.value[0].enabled).toBe(true)
    })

    it('应该正确计算活跃规则数量', async () => {
      // 创建多个规则
      await riskManagement.createRule({
        name: '规则1',
        type: 'var',
        threshold: 5,
        level: 'medium',
        enabled: true,
        description: '描述1'
      })

      await riskManagement.createRule({
        name: '规则2',
        type: 'concentration',
        threshold: 30,
        level: 'high',
        enabled: false,
        description: '描述2'
      })

      await riskManagement.createRule({
        name: '规则3',
        type: 'leverage',
        threshold: 2,
        level: 'medium',
        enabled: true,
        description: '描述3'
      })

      expect(riskManagement.activeRulesCount.value).toBe(2)
    })
  })

  describe('风险计算', () => {
    beforeEach(() => {
      // 设置模拟的投资组合风险数据
      riskManagement.portfolioRisk.value = {
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
    })

    it('应该正确计算风险等级', () => {
      const riskLevel = riskManagement.calculateRiskLevel()
      
      // 基于模拟数据计算预期风险等级
      // VaR: 0.03/0.05 * 25 = 15
      // MaxDrawdown: 0.08/0.1 * 25 = 20
      // Concentration: 0.25/0.3 * 25 = 20.83
      // Leverage: 1.5/2.0 * 25 = 18.75
      // Total: 74.58
      expect(riskLevel).toBeCloseTo(74.58, 1)
    })

    it('应该能够更新投资组合风险数据', async () => {
      const newRiskData: PortfolioRisk = {
        totalValue: 1200000,
        var: 0.04,
        cvar: 0.06,
        maxDrawdown: -0.12,
        sharpeRatio: 1.0,
        beta: 1.3,
        volatility: 0.22,
        concentration: {
          topHoldings: 0.35,
          sectors: {
            '科技': 0.40,
            '金融': 0.30,
            '消费': 0.20,
            '其他': 0.10
          },
          regions: {
            '国内': 0.75,
            '美国': 0.20,
            '其他': 0.05
          }
        },
        leverage: 2.0,
        liquidityRisk: 0.03
      }

      await riskManagement.updatePortfolioRisk(newRiskData)

      expect(riskManagement.portfolioRisk.value).toEqual(newRiskData)
    })
  })

  describe('风险规则评估', () => {
    beforeEach(() => {
      // 设置投资组合风险数据
      riskManagement.portfolioRisk.value = {
        totalValue: 1000000,
        var: 0.06, // 超过默认阈值5%
        cvar: 0.08,
        maxDrawdown: -0.12, // 超过默认阈值10%
        sharpeRatio: 1.2,
        beta: 1.1,
        volatility: 0.18,
        concentration: {
          topHoldings: 0.35, // 超过默认阈值30%
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
        leverage: 2.5, // 超过默认阈值2.0
        liquidityRisk: 0.02
      }
    })

    it('应该能够检查风险规则并生成预警', async () => {
      // 创建一些风险规则
      await riskManagement.createRule({
        name: 'VaR限制',
        type: 'var',
        threshold: 5, // 5%
        level: 'high',
        enabled: true,
        description: 'VaR不得超过5%'
      })

      await riskManagement.createRule({
        name: '持仓集中度限制',
        type: 'concentration',
        threshold: 30, // 30%
        level: 'medium',
        enabled: true,
        description: '前5大持仓占比不得超过30%'
      })

      await riskManagement.createRule({
        name: '杠杆限制',
        type: 'leverage',
        threshold: 2, // 2倍
        level: 'high',
        enabled: true,
        description: '杠杆比例不得超过2倍'
      })

      // 检查风险规则
      await riskManagement.checkRiskRules()

      // 应该生成3个预警
      expect(riskManagement.alerts.value).toHaveLength(3)
      
      // 检查预警内容
      const varAlert = riskManagement.alerts.value.find(a => a.title.includes('VaR'))
      const concentrationAlert = riskManagement.alerts.value.find(a => a.title.includes('持仓集中度'))
      const leverageAlert = riskManagement.alerts.value.find(a => a.title.includes('杠杆'))

      expect(varAlert).toBeDefined()
      expect(concentrationAlert).toBeDefined()
      expect(leverageAlert).toBeDefined()
    })

    it('应该正确更新规则触发信息', async () => {
      // 创建一个规则
      await riskManagement.createRule({
        name: '最大回撤限制',
        type: 'max_drawdown',
        threshold: 10, // 10%
        level: 'high',
        enabled: true,
        description: '最大回撤不得超过10%'
      })

      const rule = riskManagement.riskRules.value[0]
      const initialTriggerCount = rule.triggerCount

      // 检查风险规则
      await riskManagement.checkRiskRules()

      // 规则应该被触发
      expect(rule.triggerCount).toBe(initialTriggerCount + 1)
      expect(rule.lastTriggered).toBeDefined()
    })
  })

  describe('风险监控', () => {
    it('应该能够启动风险监控', async () => {
      expect(riskManagement.isMonitoring.value).toBe(false)

      await riskManagement.startMonitoring()

      expect(riskManagement.isMonitoring.value).toBe(true)
    })

    it('应该能够停止风险监控', async () => {
      // 先启动监控
      await riskManagement.startMonitoring()
      expect(riskManagement.isMonitoring.value).toBe(true)

      // 停止监控
      await riskManagement.stopMonitoring()

      expect(riskManagement.isMonitoring.value).toBe(false)
    })
  })

  describe('默认规则初始化', () => {
    it('应该能够初始化默认风险规则', async () => {
      // 清空现有规则
      riskManagement.riskRules.value = []

      // 初始化默认规则
      await riskManagement.initializeDefaultRules()

      // 应该创建了默认规则
      expect(riskManagement.riskRules.value.length).toBeGreaterThan(0)
      
      // 检查是否包含基本的风险规则类型
      const ruleTypes = riskManagement.riskRules.value.map(rule => rule.type)
      expect(ruleTypes).toContain('concentration')
      expect(ruleTypes).toContain('daily_loss')
      expect(ruleTypes).toContain('max_drawdown')
      expect(ruleTypes).toContain('leverage')
      expect(ruleTypes).toContain('var')
    })
  })
})
