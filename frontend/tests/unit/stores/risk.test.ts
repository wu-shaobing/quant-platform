/**
 * 风险管理存储测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useRiskStore } from '@/stores/modules/risk'
import type { RiskMetrics, RiskAlert, RiskLimit } from '@/types/risk'

// Mock API
vi.mock('@/api/risk', () => ({
  riskApi: {
    getRiskMetrics: vi.fn(),
    getRiskAlerts: vi.fn(),
    createRiskAlert: vi.fn(),
    updateRiskAlert: vi.fn(),
    deleteRiskAlert: vi.fn(),
    getRiskLimits: vi.fn(),
    updateRiskLimits: vi.fn(),
    calculateVaR: vi.fn(),
    runStressTest: vi.fn(),
    generateRiskAssessment: vi.fn()
  }
}))

describe('useRiskStore', () => {
  let store: ReturnType<typeof useRiskStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useRiskStore()
  })

  describe('初始状态', () => {
    it('应该正确初始化状态', () => {
      expect(store.riskMetrics).toBeNull()
      expect(store.alerts).toEqual([])
      expect(store.limits).toEqual([])
      expect(store.assessment).toBeNull()
      expect(store.varCalculations).toEqual([])
      expect(store.stressTestResults).toEqual([])
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
      expect(store.monitoringEnabled).toBe(true)
    })

    it('应该正确设置预警阈值', () => {
      const thresholds = store.alertThresholds
      expect(thresholds.portfolioVaR).toBe(0.05)
      expect(thresholds.positionConcentration).toBe(0.20)
      expect(thresholds.sectorConcentration).toBe(0.30)
      expect(thresholds.leverage).toBe(2.0)
      expect(thresholds.drawdown).toBe(0.10)
    })
  })

  describe('计算属性', () => {
    beforeEach(() => {
      // 设置测试数据
      store.alerts = [
        {
          id: '1',
          type: 'position_limit',
          severity: 'critical',
          status: 'active',
          title: '严重预警1',
          message: '消息1',
          createdAt: new Date().toISOString(),
          acknowledgedAt: null,
          metadata: {}
        },
        {
          id: '2',
          type: 'daily_loss',
          severity: 'high',
          status: 'active',
          title: '高风险预警',
          message: '消息2',
          createdAt: new Date().toISOString(),
          acknowledgedAt: null,
          metadata: {}
        },
        {
          id: '3',
          type: 'concentration',
          severity: 'medium',
          status: 'acknowledged',
          title: '中风险预警',
          message: '消息3',
          createdAt: new Date().toISOString(),
          acknowledgedAt: new Date().toISOString(),
          metadata: {}
        }
      ]

      store.riskMetrics = {
        portfolioVaR: 0.06,
        maxDrawdown: -0.08,
        volatility: 0.18,
        beta: 1.2,
        sharpeRatio: 1.5,
        totalValue: 1000000,
        concentration: {
          topHoldings: 0.25,
          sectors: { '科技': 0.35, '金融': 0.25 },
          regions: { '国内': 0.80, '美国': 0.20 }
        },
        leverage: 1.8,
        liquidityRisk: 0.02
      }

      store.limits = [
        {
          id: '1',
          type: 'position',
          name: '单一持仓限制',
          limitValue: 0.20,
          currentValue: 0.25, // 超限
          unit: 'percentage',
          status: 'active'
        },
        {
          id: '2',
          type: 'sector',
          name: '行业集中度限制',
          limitValue: 0.30,
          currentValue: 0.25, // 正常
          unit: 'percentage',
          status: 'active'
        }
      ]
    })

    it('应该正确计算活跃预警', () => {
      const activeAlerts = store.activeAlerts
      expect(activeAlerts).toHaveLength(2)
      expect(activeAlerts.every(alert => alert.status === 'active')).toBe(true)
    })

    it('应该正确计算严重预警', () => {
      const criticalAlerts = store.criticalAlerts
      expect(criticalAlerts).toHaveLength(1)
      expect(criticalAlerts[0].severity).toBe('critical')
    })

    it('应该正确计算风险评分', () => {
      const score = store.riskScore
      // 基于测试数据计算: (6 + 8 + 9 + 30) / 4 = 13.25
      expect(score).toBeCloseTo(13.25, 1)
    })

    it('应该正确计算风险等级', () => {
      // 基于风险评分13.25，应该是very-low级别
      expect(store.riskLevel).toBe('very-low')
    })

    it('应该正确识别超限项目', () => {
      const exceededLimits = store.exceededLimits
      expect(exceededLimits).toHaveLength(1)
      expect(exceededLimits[0].name).toBe('单一持仓限制')
    })
  })

  describe('风险指标获取', () => {
    it('应该能够获取风险指标', async () => {
      const mockMetrics: RiskMetrics = {
        portfolioVaR: 0.04,
        maxDrawdown: -0.06,
        volatility: 0.15,
        beta: 1.1,
        sharpeRatio: 1.8,
        totalValue: 1200000,
        concentration: {
          topHoldings: 0.22,
          sectors: { '科技': 0.30, '金融': 0.28 },
          regions: { '国内': 0.75, '美国': 0.25 }
        },
        leverage: 1.6,
        liquidityRisk: 0.015
      }

      const { riskApi } = await import('@/api/risk')
      vi.mocked(riskApi.getRiskMetrics).mockResolvedValue(mockMetrics)

      await store.fetchRiskMetrics()

      expect(store.riskMetrics).toEqual(mockMetrics)
      expect(store.isLoading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('应该处理获取风险指标失败', async () => {
      const { riskApi } = await import('@/api/risk')
      vi.mocked(riskApi.getRiskMetrics).mockRejectedValue(new Error('网络错误'))

      await store.fetchRiskMetrics()

      expect(store.riskMetrics).toBeNull()
      expect(store.error).toBe('获取风险指标失败: 网络错误')
      expect(store.isLoading).toBe(false)
    })
  })

  describe('预警管理', () => {
    it('应该能够获取预警列表', async () => {
      const mockAlerts: RiskAlert[] = [
        {
          id: '1',
          type: 'position_limit',
          severity: 'high',
          status: 'active',
          title: '持仓超限',
          message: '单一持仓占比超过20%',
          createdAt: new Date().toISOString(),
          acknowledgedAt: null,
          metadata: { symbol: '000001', ratio: 0.25 }
        }
      ]

      const { riskApi } = await import('@/api/risk')
      vi.mocked(riskApi.getRiskAlerts).mockResolvedValue(mockAlerts)

      await store.fetchAlerts()

      expect(store.alerts).toEqual(mockAlerts)
      expect(store.isLoading).toBe(false)
    })

    it('应该能够创建预警', async () => {
      const newAlert: Omit<RiskAlert, 'id' | 'createdAt'> = {
        type: 'daily_loss',
        severity: 'medium',
        status: 'active',
        title: '日亏损预警',
        message: '今日亏损接近限额',
        acknowledgedAt: null,
        metadata: { loss: 8000, limit: 10000 }
      }

      const createdAlert: RiskAlert = {
        ...newAlert,
        id: '2',
        createdAt: new Date().toISOString()
      }

      const { riskApi } = await import('@/api/risk')
      vi.mocked(riskApi.createRiskAlert).mockResolvedValue(createdAlert)

      await store.createAlert(newAlert)

      expect(store.alerts).toContain(createdAlert)
    })

    it('应该能够更新预警', async () => {
      // 先添加一个预警
      store.alerts = [{
        id: '1',
        type: 'position_limit',
        severity: 'high',
        status: 'active',
        title: '原标题',
        message: '原消息',
        createdAt: new Date().toISOString(),
        acknowledgedAt: null,
        metadata: {}
      }]

      const updateData = {
        severity: 'critical' as const,
        title: '更新标题',
        message: '更新消息'
      }

      const updatedAlert: RiskAlert = {
        ...store.alerts[0],
        ...updateData
      }

      const { riskApi } = await import('@/api/risk')
      vi.mocked(riskApi.updateRiskAlert).mockResolvedValue(updatedAlert)

      await store.updateAlert('1', updateData)

      expect(store.alerts[0]).toEqual(updatedAlert)
    })

    it('应该能够确认预警', async () => {
      // 先添加一个预警
      store.alerts = [{
        id: '1',
        type: 'position_limit',
        severity: 'high',
        status: 'active',
        title: '测试预警',
        message: '测试消息',
        createdAt: new Date().toISOString(),
        acknowledgedAt: null,
        metadata: {}
      }]

      const acknowledgedAlert: RiskAlert = {
        ...store.alerts[0],
        status: 'acknowledged',
        acknowledgedAt: new Date().toISOString()
      }

      const { riskApi } = await import('@/api/risk')
      vi.mocked(riskApi.updateRiskAlert).mockResolvedValue(acknowledgedAlert)

      await store.acknowledgeAlert('1')

      expect(store.alerts[0].status).toBe('acknowledged')
      expect(store.alerts[0].acknowledgedAt).toBeDefined()
    })

    it('应该能够忽略预警', async () => {
      // 先添加一个预警
      store.alerts = [{
        id: '1',
        type: 'position_limit',
        severity: 'high',
        status: 'active',
        title: '测试预警',
        message: '测试消息',
        createdAt: new Date().toISOString(),
        acknowledgedAt: null,
        metadata: {}
      }]

      await store.dismissAlert('1')

      expect(store.alerts).toHaveLength(0)
    })
  })

  describe('限额管理', () => {
    it('应该能够获取限额列表', async () => {
      const mockLimits: RiskLimit[] = [
        {
          id: '1',
          type: 'position',
          name: '单一持仓限制',
          limitValue: 0.20,
          currentValue: 0.15,
          unit: 'percentage',
          status: 'active'
        }
      ]

      const { riskApi } = await import('@/api/risk')
      vi.mocked(riskApi.getRiskLimits).mockResolvedValue(mockLimits)

      await store.fetchLimits()

      expect(store.limits).toEqual(mockLimits)
    })

    it('应该能够创建限额', async () => {
      const newLimit: Omit<RiskLimit, 'id'> = {
        type: 'sector',
        name: '行业集中度限制',
        limitValue: 0.30,
        currentValue: 0.25,
        unit: 'percentage',
        status: 'active'
      }

      const createdLimit: RiskLimit = {
        ...newLimit,
        id: '2'
      }

      await store.createLimit(newLimit)

      expect(store.limits).toContain(createdLimit)
    })

    it('应该能够更新限额', async () => {
      // 先添加一个限额
      store.limits = [{
        id: '1',
        type: 'position',
        name: '单一持仓限制',
        limitValue: 0.20,
        currentValue: 0.15,
        unit: 'percentage',
        status: 'active'
      }]

      const updateData = {
        limitValue: 0.25,
        currentValue: 0.18
      }

      await store.updateLimit('1', updateData)

      expect(store.limits[0].limitValue).toBe(0.25)
      expect(store.limits[0].currentValue).toBe(0.18)
    })

    it('应该能够删除限额', async () => {
      // 先添加一个限额
      store.limits = [{
        id: '1',
        type: 'position',
        name: '单一持仓限制',
        limitValue: 0.20,
        currentValue: 0.15,
        unit: 'percentage',
        status: 'active'
      }]

      await store.deleteLimit('1')

      expect(store.limits).toHaveLength(0)
    })
  })

  describe('VaR计算', () => {
    it('应该能够计算VaR', async () => {
      const mockVaRResult = {
        id: '1',
        portfolioId: 'portfolio-1',
        confidenceLevel: 0.95,
        timeHorizon: 1,
        var: 0.045,
        expectedShortfall: 0.065,
        calculatedAt: new Date().toISOString(),
        method: 'historical' as const,
        parameters: { lookbackDays: 252 }
      }

      const { riskApi } = await import('@/api/risk')
      vi.mocked(riskApi.calculateVaR).mockResolvedValue(mockVaRResult)

      await store.calculateVaR('portfolio-1', 0.95, 1, 'historical')

      expect(store.varCalculations).toContain(mockVaRResult)
    })
  })

  describe('压力测试', () => {
    it('应该能够运行压力测试', async () => {
      const mockStressTestResult = {
        id: '1',
        portfolioId: 'portfolio-1',
        scenario: 'market_crash',
        scenarioName: '市场崩盘',
        portfolioValue: 1000000,
        stressedValue: 850000,
        loss: -150000,
        lossPercentage: -0.15,
        runAt: new Date().toISOString(),
        parameters: { marketDrop: 0.20 }
      }

      const { riskApi } = await import('@/api/risk')
      vi.mocked(riskApi.runStressTest).mockResolvedValue(mockStressTestResult)

      await store.runStressTest('portfolio-1', 'market_crash', { marketDrop: 0.20 })

      expect(store.stressTestResults).toContain(mockStressTestResult)
    })
  })

  describe('阈值管理', () => {
    it('应该能够更新阈值', async () => {
      const newThresholds = {
        portfolioVaR: 0.06,
        positionConcentration: 0.25,
        sectorConcentration: 0.35,
        leverage: 2.5,
        drawdown: 0.12
      }

      await store.updateThresholds(newThresholds)

      expect(store.alertThresholds).toEqual(newThresholds)
    })

    it('应该能够切换监控状态', async () => {
      expect(store.monitoringEnabled).toBe(true)

      await store.toggleMonitoring()

      expect(store.monitoringEnabled).toBe(false)

      await store.toggleMonitoring()

      expect(store.monitoringEnabled).toBe(true)
    })
  })

  describe('数据刷新', () => {
    it('应该能够刷新所有数据', async () => {
      const { riskApi } = await import('@/api/risk')
      vi.mocked(riskApi.getRiskMetrics).mockResolvedValue({} as RiskMetrics)
      vi.mocked(riskApi.getRiskAlerts).mockResolvedValue([])
      vi.mocked(riskApi.getRiskLimits).mockResolvedValue([])

      await store.refreshAll()

      expect(riskApi.getRiskMetrics).toHaveBeenCalled()
      expect(riskApi.getRiskAlerts).toHaveBeenCalled()
      expect(riskApi.getRiskLimits).toHaveBeenCalled()
    })
  })

  describe('错误处理', () => {
    it('应该能够清除错误', () => {
      store.error = '测试错误'
      
      store.clearError()
      
      expect(store.error).toBeNull()
    })
  })

  describe('状态重置', () => {
    it('应该能够重置所有状态', () => {
      // 设置一些数据
      store.riskMetrics = {} as RiskMetrics
      store.alerts = [{ id: '1' } as RiskAlert]
      store.limits = [{ id: '1' } as RiskLimit]
      store.error = '测试错误'

      store.reset()

      expect(store.riskMetrics).toBeNull()
      expect(store.alerts).toEqual([])
      expect(store.limits).toEqual([])
      expect(store.error).toBeNull()
    })
  })
})
