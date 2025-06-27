import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  RiskMetrics,
  RiskAlert,
  RiskLimit,
  RiskAssessment,
  VaRCalculation,
  StressTestResult
} from '@/types/risk'

export const useRiskStore = defineStore('risk', () => {
  // State
  const riskMetrics = ref<RiskMetrics | null>(null)
  const alerts = ref<RiskAlert[]>([])
  const limits = ref<RiskLimit[]>([])
  const assessment = ref<RiskAssessment | null>(null)
  const varCalculations = ref<VaRCalculation[]>([])
  const stressTestResults = ref<StressTestResult[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Risk monitoring settings
  const monitoringEnabled = ref(true)
  const alertThresholds = ref({
    portfolioVaR: 0.05, // 5%
    positionConcentration: 0.20, // 20%
    sectorConcentration: 0.30, // 30%
    leverage: 2.0,
    drawdown: 0.10 // 10%
  })

  // Getters
  const activeAlerts = computed(() =>
    alerts.value.filter(alert => alert.status === 'active')
  )

  const criticalAlerts = computed(() =>
    activeAlerts.value.filter(alert => alert.severity === 'critical')
  )

  const riskScore = computed(() => {
    if (!riskMetrics.value) return 0

    // Calculate composite risk score (0-100)
    const factors = [
      riskMetrics.value.portfolioVaR * 100,
      riskMetrics.value.maxDrawdown * 100,
      riskMetrics.value.volatility * 50,
      riskMetrics.value.beta * 25
    ]

    return Math.min(100, factors.reduce((sum, factor) => sum + factor, 0) / factors.length)
  })

  const riskLevel = computed(() => {
    const score = riskScore.value
    if (score >= 80) return 'high'
    if (score >= 60) return 'medium'
    if (score >= 40) return 'low'
    return 'very-low'
  })

  const exceededLimits = computed(() =>
    limits.value.filter(limit => limit.currentValue > limit.limitValue)
  )

  // Actions
  const fetchRiskMetrics = async (portfolioId?: string) => {
    try {
      isLoading.value = true
      error.value = null

      // TODO: Replace with actual API call
      // const response = await riskService.getRiskMetrics(portfolioId)
      // riskMetrics.value = response.data

      // Mock data for now
      riskMetrics.value = {
        portfolioVaR: 0.023,
        conditionalVaR: 0.035,
        maxDrawdown: 0.08,
        volatility: 0.15,
        sharpeRatio: 1.2,
        beta: 0.85,
        alpha: 0.02,
        trackingError: 0.03,
        informationRatio: 0.67,
        updatedAt: new Date().toISOString()
      }
    } catch (err: any) {
      error.value = err.message || '获取风险指标失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const fetchAlerts = async () => {
    try {
      // TODO: Replace with actual API call
      // const response = await riskService.getAlerts()
      // alerts.value = response.data

      // Mock data for now
      alerts.value = []
    } catch (err: any) {
      error.value = err.message || '获取风险警报失败'
      throw err
    }
  }

  const fetchLimits = async () => {
    try {
      // TODO: Replace with actual API call
      // const response = await riskService.getLimits()
      // limits.value = response.data

      // Mock data for now
      limits.value = []
    } catch (err: any) {
      error.value = err.message || '获取风险限额失败'
      throw err
    }
  }

  const calculateVaR = async (params: {
    portfolioId: string
    confidenceLevel: number
    timeHorizon: number
    method: 'historical' | 'parametric' | 'monteCarlo'
  }) => {
    try {
      isLoading.value = true

      // TODO: Replace with actual API call
      // const response = await riskService.calculateVaR(params)
      // const calculation = response.data

      // Mock calculation
      const calculation: VaRCalculation = {
        id: Date.now().toString(),
        portfolioId: params.portfolioId,
        method: params.method,
        confidenceLevel: params.confidenceLevel,
        timeHorizon: params.timeHorizon,
        value: Math.random() * 0.05, // Random VaR between 0-5%
        currency: 'CNY',
        calculatedAt: new Date().toISOString()
      }

      varCalculations.value.unshift(calculation)
      return calculation

    } catch (err: any) {
      error.value = err.message || 'VaR计算失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const runStressTest = async (params: {
    portfolioId: string
    scenario: string
    shockMagnitude: number
  }) => {
    try {
      isLoading.value = true

      // TODO: Replace with actual API call
      // const response = await riskService.runStressTest(params)
      // const result = response.data

      // Mock stress test result
      const result: StressTestResult = {
        id: Date.now().toString(),
        portfolioId: params.portfolioId,
        scenario: params.scenario,
        shockMagnitude: params.shockMagnitude,
        portfolioImpact: Math.random() * -0.20, // Random loss between 0-20%
        worstPosition: 'AAPL',
        worstPositionImpact: Math.random() * -0.30,
        runAt: new Date().toISOString()
      }

      stressTestResults.value.unshift(result)
      return result

    } catch (err: any) {
      error.value = err.message || '压力测试失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const createAlert = async (alert: Omit<RiskAlert, 'id' | 'createdAt'>) => {
    try {
      // TODO: Replace with actual API call
      // const response = await riskService.createAlert(alert)
      // const newAlert = response.data

      // Mock implementation
      const newAlert: RiskAlert = {
        ...alert,
        id: Date.now().toString(),
        createdAt: new Date().toISOString()
      }

      alerts.value.unshift(newAlert)
      return newAlert

    } catch (err: any) {
      error.value = err.message || '创建警报失败'
      throw err
    }
  }

  const updateAlert = async (alertId: string, updates: Partial<RiskAlert>) => {
    try {
      // TODO: Replace with actual API call
      // const response = await riskService.updateAlert(alertId, updates)

      // Mock implementation
      const index = alerts.value.findIndex(alert => alert.id === alertId)
      if (index !== -1) {
        alerts.value[index] = { ...alerts.value[index], ...updates }
      }

    } catch (err: any) {
      error.value = err.message || '更新警报失败'
      throw err
    }
  }

  const dismissAlert = async (alertId: string) => {
    await updateAlert(alertId, { status: 'dismissed' })
  }

  const acknowledgeAlert = async (alertId: string) => {
    await updateAlert(alertId, { status: 'acknowledged' })
  }

  const createLimit = async (limit: Omit<RiskLimit, 'id' | 'createdAt'>) => {
    try {
      // TODO: Replace with actual API call
      // const response = await riskService.createLimit(limit)
      // const newLimit = response.data

      // Mock implementation
      const newLimit: RiskLimit = {
        ...limit,
        id: Date.now().toString(),
        createdAt: new Date().toISOString()
      }

      limits.value.push(newLimit)
      return newLimit

    } catch (err: any) {
      error.value = err.message || '创建限额失败'
      throw err
    }
  }

  const updateLimit = async (limitId: string, updates: Partial<RiskLimit>) => {
    try {
      // TODO: Replace with actual API call
      // const response = await riskService.updateLimit(limitId, updates)

      // Mock implementation
      const index = limits.value.findIndex(limit => limit.id === limitId)
      if (index !== -1) {
        limits.value[index] = { ...limits.value[index], ...updates }
      }

    } catch (err: any) {
      error.value = err.message || '更新限额失败'
      throw err
    }
  }

  const deleteLimit = async (limitId: string) => {
    try {
      // TODO: Replace with actual API call
      // await riskService.deleteLimit(limitId)

      // Mock implementation
      limits.value = limits.value.filter(limit => limit.id !== limitId)

    } catch (err: any) {
      error.value = err.message || '删除限额失败'
      throw err
    }
  }

  const generateAssessment = async (portfolioId: string) => {
    try {
      isLoading.value = true

      // TODO: Replace with actual API call
      // const response = await riskService.generateAssessment(portfolioId)
      // assessment.value = response.data

      // Mock assessment
      assessment.value = {
        portfolioId,
        overallRisk: riskLevel.value,
        riskScore: riskScore.value,
        keyRisks: [
          'Market risk exposure elevated',
          'Concentration risk in technology sector',
          'Currency exposure to USD'
        ],
        recommendations: [
          'Consider diversifying sector allocation',
          'Implement currency hedging strategy',
          'Review position sizing limits'
        ],
        generatedAt: new Date().toISOString()
      }

    } catch (err: any) {
      error.value = err.message || '生成风险评估失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const updateThresholds = (newThresholds: Partial<typeof alertThresholds.value>) => {
    alertThresholds.value = { ...alertThresholds.value, ...newThresholds }
  }

  const toggleMonitoring = () => {
    monitoringEnabled.value = !monitoringEnabled.value
  }

  const refreshAll = async (portfolioId?: string) => {
    await Promise.all([
      fetchRiskMetrics(portfolioId),
      fetchAlerts(),
      fetchLimits()
    ])
  }

  const clearError = () => {
    error.value = null
  }

  const reset = () => {
    riskMetrics.value = null
    alerts.value = []
    limits.value = []
    assessment.value = null
    varCalculations.value = []
    stressTestResults.value = []
    error.value = null
  }

  return {
    // State
    riskMetrics,
    alerts,
    limits,
    assessment,
    varCalculations,
    stressTestResults,
    isLoading,
    error,
    monitoringEnabled,
    alertThresholds,

    // Getters
    activeAlerts,
    criticalAlerts,
    riskScore,
    riskLevel,
    exceededLimits,

    // Actions
    fetchRiskMetrics,
    fetchAlerts,
    fetchLimits,
    calculateVaR,
    runStressTest,
    createAlert,
    updateAlert,
    dismissAlert,
    acknowledgeAlert,
    createLimit,
    updateLimit,
    deleteLimit,
    generateAssessment,
    updateThresholds,
    toggleMonitoring,
    refreshAll,
    clearError,
    reset
  }
}, {
  persist: {
    key: 'risk-store',
    storage: localStorage,
    paths: ['alertThresholds', 'monitoringEnabled']
  }
})
