<template>
  <div class="strategy-monitor-page">
    <div class="container mx-auto p-6">
      <!-- 页面头部 -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">策略监控</h1>
          <p class="text-gray-600 mt-1">实时监控策略运行状态和性能表现</p>
        </div>
        <div class="flex gap-2">
          <el-button @click="refreshData" :loading="loading" type="primary" size="small">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
          <el-button @click="showLogDialog = true" type="info" size="small">
            <el-icon><Document /></el-icon>
            查看日志
          </el-button>
          <el-button @click="exportReport" type="success" size="small">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
        </div>
      </div>

      <!-- 策略选择器 -->
      <div class="bg-white rounded-lg shadow-md p-4 mb-6">
        <div class="flex items-center gap-4">
          <span class="text-gray-700 font-medium">当前策略:</span>
          <el-select
            v-model="selectedStrategyId"
            placeholder="选择要监控的策略"
            style="width: 300px"
            @change="onStrategyChange"
          >
            <el-option
              v-for="strategy in runningStrategies"
              :key="strategy.id"
              :label="`${strategy.name} (${strategy.status})`"
              :value="strategy.id"
            >
              <div class="flex justify-between items-center">
                <span>{{ strategy.name }}</span>
                <el-tag :type="getStatusTagType(strategy.status)" size="small">
                  {{ getStatusLabel(strategy.status) }}
                </el-tag>
              </div>
            </el-option>
          </el-select>
          <div v-if="currentStrategy" class="flex items-center gap-2">
            <el-tag :type="getStatusTagType(currentStrategy.status)">
              {{ getStatusLabel(currentStrategy.status) }}
            </el-tag>
            <span class="text-sm text-gray-600">
              运行时长: {{ formatDuration(currentStrategy.runningTime) }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="currentStrategy" class="space-y-6">
        <!-- 关键指标卡片 -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600">当前净值</p>
                <p class="text-2xl font-bold text-gray-900">
                  {{ performance.currentNav.toFixed(4) }}
                </p>
                <p class="text-xs text-gray-500 mt-1">
                  更新时间: {{ formatTime(performance.lastUpdate) }}
                </p>
              </div>
              <div class="p-3 bg-blue-100 rounded-full">
                <el-icon class="text-blue-600" size="24"><TrendCharts /></el-icon>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow-md p-6 border-l-4" 
               :class="performance.totalReturn >= 0 ? 'border-red-500' : 'border-green-500'">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600">总收益率</p>
                <p class="text-2xl font-bold" 
                   :class="performance.totalReturn >= 0 ? 'text-red-600' : 'text-green-600'">
                  {{ formatPercent(performance.totalReturn) }}
                </p>
                <p class="text-xs text-gray-500 mt-1">
                  年化: {{ formatPercent(performance.annualizedReturn) }}
                </p>
              </div>
              <div class="p-3 rounded-full"
                   :class="performance.totalReturn >= 0 ? 'bg-red-100' : 'bg-green-100'">
                <el-icon :class="performance.totalReturn >= 0 ? 'text-red-600' : 'text-green-600'" size="24">
                  <DataAnalysis />
                </el-icon>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-yellow-500">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600">最大回撤</p>
                <p class="text-2xl font-bold text-yellow-600">
                  {{ formatPercent(performance.maxDrawdown) }}
                </p>
                <p class="text-xs text-gray-500 mt-1">
                  夏普比率: {{ performance.sharpeRatio.toFixed(2) }}
                </p>
              </div>
              <div class="p-3 bg-yellow-100 rounded-full">
                <el-icon class="text-yellow-600" size="24"><Warning /></el-icon>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-medium text-gray-600">今日盈亏</p>
                <p class="text-2xl font-bold" 
                   :class="performance.todayPnl >= 0 ? 'text-red-600' : 'text-green-600'">
                  {{ formatPnl(performance.todayPnl) }}
                </p>
                <p class="text-xs text-gray-500 mt-1">
                  胜率: {{ formatPercent(performance.winRate) }}
                </p>
              </div>
              <div class="p-3 bg-green-100 rounded-full">
                <el-icon class="text-green-600" size="24"><Money /></el-icon>
              </div>
            </div>
          </div>
        </div>

        <!-- 图表区域 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 净值曲线 -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-semibold text-gray-800">净值曲线</h3>
              <el-select v-model="navPeriod" size="small" style="width: 120px">
                <el-option label="今日" value="1d" />
                <el-option label="本周" value="1w" />
                <el-option label="本月" value="1m" />
                <el-option label="全部" value="all" />
              </el-select>
            </div>
            <div ref="navChartRef" class="h-80"></div>
          </div>

          <!-- 收益分布 -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <h3 class="text-lg font-semibold text-gray-800 mb-4">收益分布</h3>
            <div ref="returnDistChartRef" class="h-80"></div>
          </div>
        </div>

        <!-- 持仓信息和交易记录 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 当前持仓 -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-semibold text-gray-800">当前持仓</h3>
              <el-button @click="refreshPositions" size="small" text>
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
            
            <div v-loading="positionsLoading" class="min-h-48">
              <el-table :data="currentPositions" size="small" stripe>
                <el-table-column prop="symbol" label="代码" width="80" />
                <el-table-column prop="name" label="名称" show-overflow-tooltip />
                <el-table-column prop="quantity" label="数量" width="80" align="right">
                  <template #default="{ row }">
                    {{ formatNumber(row.quantity) }}
                  </template>
                </el-table-column>
                <el-table-column prop="price" label="价格" width="80" align="right">
                  <template #default="{ row }">
                    {{ formatPrice(row.price) }}
                  </template>
                </el-table-column>
                <el-table-column prop="pnl" label="盈亏" width="80" align="right">
                  <template #default="{ row }">
                    <span :class="getPnlClass(row.pnl)">
                      {{ formatPnl(row.pnl) }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>

              <div v-if="currentPositions.length === 0" class="text-center py-8 text-gray-500">
                暂无持仓
              </div>
            </div>
          </div>

          <!-- 最近交易 -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-semibold text-gray-800">最近交易</h3>
              <el-button @click="showAllTrades" size="small" text>
                查看全部
              </el-button>
            </div>
            
            <div v-loading="tradesLoading" class="min-h-48">
              <el-table :data="recentTrades" size="small" stripe>
                <el-table-column prop="time" label="时间" width="80">
                  <template #default="{ row }">
                    {{ formatTime(row.time, 'HH:mm:ss') }}
                  </template>
                </el-table-column>
                <el-table-column prop="symbol" label="代码" width="70" />
                <el-table-column prop="side" label="方向" width="50">
                  <template #default="{ row }">
                    <el-tag :type="row.side === 'buy' ? 'danger' : 'success'" size="small">
                      {{ row.side === 'buy' ? '买' : '卖' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="quantity" label="数量" width="70" align="right">
                  <template #default="{ row }">
                    {{ formatNumber(row.quantity) }}
                  </template>
                </el-table-column>
                <el-table-column prop="price" label="价格" width="70" align="right">
                  <template #default="{ row }">
                    {{ formatPrice(row.price) }}
                  </template>
                </el-table-column>
                <el-table-column prop="pnl" label="盈亏" width="70" align="right">
                  <template #default="{ row }">
                    <span :class="getPnlClass(row.pnl)">
                      {{ formatPnl(row.pnl) }}
                    </span>
                  </template>
                </el-table-column>
              </el-table>

              <div v-if="recentTrades.length === 0" class="text-center py-8 text-gray-500">
                暂无交易记录
              </div>
            </div>
          </div>
        </div>

        <!-- 风险监控 -->
        <div class="bg-white rounded-lg shadow-md p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <el-icon><Warning /></el-icon>
            风险监控
          </h3>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="border rounded-lg p-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-600">回撤风险</span>
                <el-tag :type="getRiskLevel(performance.maxDrawdown, -0.1)" size="small">
                  {{ getRiskLevelText(performance.maxDrawdown, -0.1) }}
                </el-tag>
              </div>
              <div class="text-lg font-bold text-gray-800">
                {{ formatPercent(performance.maxDrawdown) }}
              </div>
              <div class="text-xs text-gray-500 mt-1">
                阈值: -10%
              </div>
            </div>

            <div class="border rounded-lg p-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-600">持仓集中度</span>
                <el-tag :type="getRiskLevel(performance.concentration, 0.3)" size="small">
                  {{ getRiskLevelText(performance.concentration, 0.3) }}
                </el-tag>
              </div>
              <div class="text-lg font-bold text-gray-800">
                {{ formatPercent(performance.concentration) }}
              </div>
              <div class="text-xs text-gray-500 mt-1">
                阈值: 30%
              </div>
            </div>

            <div class="border rounded-lg p-4">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-600">波动率</span>
                <el-tag :type="getRiskLevel(performance.volatility, 0.25)" size="small">
                  {{ getRiskLevelText(performance.volatility, 0.25) }}
                </el-tag>
              </div>
              <div class="text-lg font-bold text-gray-800">
                {{ formatPercent(performance.volatility) }}
              </div>
              <div class="text-xs text-gray-500 mt-1">
                阈值: 25%
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 未选择策略的提示 -->
      <div v-else class="text-center py-12">
        <el-empty description="请选择要监控的策略">
          <el-button type="primary" @click="$router.push('/strategy/list')">
            查看策略列表
          </el-button>
        </el-empty>
      </div>
    </div>

    <!-- 日志查看弹窗 -->
    <el-dialog v-model="showLogDialog" title="策略运行日志" width="900px">
      <div class="space-y-4">
        <div class="flex justify-between items-center">
          <el-select v-model="logLevel" size="small" style="width: 120px">
            <el-option label="全部" value="all" />
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="错误" value="error" />
          </el-select>
          <el-button @click="refreshLogs" size="small">
            <el-icon><Refresh /></el-icon>
            刷新日志
          </el-button>
        </div>
        
        <div class="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
          <div v-for="log in filteredLogs" :key="log.id" class="mb-1">
            <span :class="getLogLevelClass(log.level)">[{{ log.level }}]</span>
            <span class="text-gray-400">{{ formatTime(log.timestamp, 'YYYY-MM-DD HH:mm:ss') }}</span>
            <span class="ml-2">{{ log.message }}</span>
          </div>
          
          <div v-if="filteredLogs.length === 0" class="text-center text-gray-500 py-4">
            暂无日志记录
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  Refresh,
  Document,
  Download,
  TrendCharts,
  DataAnalysis,
  Warning,
  Money
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useStrategy } from '@/composables/strategy/useStrategy'
import { formatPercent, formatTime, formatPrice, formatNumber, formatDuration } from '@/utils/formatters'
import type { Strategy, StrategyPerformance } from '@/types/strategy'

const router = useRouter()
const { strategies, fetchStrategies, getStrategyPerformance } = useStrategy()

// 状态管理
const loading = ref(false)
const selectedStrategyId = ref('')
const currentStrategy = ref<Strategy | null>(null)
const performance = ref<StrategyPerformance>({
  currentNav: 1.0,
  totalReturn: 0,
  annualizedReturn: 0,
  maxDrawdown: 0,
  sharpeRatio: 0,
  todayPnl: 0,
  winRate: 0,
  volatility: 0,
  concentration: 0,
  lastUpdate: new Date()
})

// 图表相关
const navChartRef = ref()
const returnDistChartRef = ref()
const navPeriod = ref('1d')
let navChart: echarts.ECharts | null = null
let returnDistChart: echarts.ECharts | null = null

// 持仓和交易
const positionsLoading = ref(false)
const tradesLoading = ref(false)
const currentPositions = ref([])
const recentTrades = ref([])

// 日志相关
const showLogDialog = ref(false)
const logLevel = ref('all')
const logs = ref([])

// 定时器
let refreshTimer: number | null = null

// 计算属性
const runningStrategies = computed(() => {
  return strategies.value.filter(s => ['running', 'paused'].includes(s.status))
})

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') return logs.value
  return logs.value.filter(log => log.level === logLevel.value)
})

// 方法
const formatPnl = (value: number) => {
  const sign = value >= 0 ? '+' : ''
  return `${sign}¥${Math.abs(value).toFixed(2)}`
}

const getPnlClass = (pnl: number) => {
  if (pnl > 0) return 'text-red-600 font-medium'
  if (pnl < 0) return 'text-green-600 font-medium'
  return 'text-gray-600'
}

const getStatusTagType = (status: string) => {
  const statusMap = {
    running: 'success',
    paused: 'warning',
    stopped: 'danger',
    error: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const statusMap = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    error: '错误'
  }
  return statusMap[status] || status
}

const getRiskLevel = (value: number, threshold: number) => {
  if (Math.abs(value) < Math.abs(threshold) * 0.5) return 'success'
  if (Math.abs(value) < Math.abs(threshold)) return 'warning'
  return 'danger'
}

const getRiskLevelText = (value: number, threshold: number) => {
  if (Math.abs(value) < Math.abs(threshold) * 0.5) return '低风险'
  if (Math.abs(value) < Math.abs(threshold)) return '中风险'
  return '高风险'
}

const getLogLevelClass = (level: string) => {
  const levelMap = {
    info: 'text-blue-400',
    warning: 'text-yellow-400',
    error: 'text-red-400'
  }
  return levelMap[level] || 'text-green-400'
}

const onStrategyChange = async (strategyId: string) => {
  const strategy = strategies.value.find(s => s.id === strategyId)
  if (strategy) {
    currentStrategy.value = strategy
    await loadStrategyData()
  }
}

const loadStrategyData = async () => {
  if (!currentStrategy.value) return
  
  try {
    loading.value = true
    
    // 获取策略性能数据
    const perfData = await getStrategyPerformance(currentStrategy.value.id)
    performance.value = perfData
    
    // 加载其他数据
    await Promise.all([
      loadPositions(),
      loadTrades(),
      loadLogs()
    ])
    
    // 初始化图表
    await nextTick()
    initCharts()
    
  } catch (error) {
    console.error('加载策略数据失败:', error)
  } finally {
    loading.value = false
  }
}

const loadPositions = async () => {
  positionsLoading.value = true
  try {
    // 模拟数据
    currentPositions.value = [
      { symbol: '000001', name: '平安银行', quantity: 1000, price: 13.20, pnl: 700 },
      { symbol: '000002', name: '万科A', quantity: 500, price: 17.50, pnl: -650 }
    ]
  } finally {
    positionsLoading.value = false
  }
}

const loadTrades = async () => {
  tradesLoading.value = true
  try {
    // 模拟数据
    recentTrades.value = [
      { time: new Date(), symbol: '000001', side: 'buy', quantity: 1000, price: 13.20, pnl: 700 },
      { time: new Date(Date.now() - 3600000), symbol: '000002', side: 'sell', quantity: 500, price: 17.50, pnl: -650 }
    ]
  } finally {
    tradesLoading.value = false
  }
}

const loadLogs = async () => {
  // 模拟日志数据
  logs.value = [
    { id: 1, level: 'info', timestamp: new Date(), message: '策略启动成功' },
    { id: 2, level: 'info', timestamp: new Date(Date.now() - 60000), message: '买入信号触发: 000001' },
    { id: 3, level: 'warning', timestamp: new Date(Date.now() - 120000), message: '持仓集中度较高，请注意风险' }
  ]
}

const initCharts = () => {
  // 初始化净值曲线图
  if (navChartRef.value) {
    navChart = echarts.init(navChartRef.value)
    updateNavChart()
  }
  
  // 初始化收益分布图
  if (returnDistChartRef.value) {
    returnDistChart = echarts.init(returnDistChartRef.value)
    updateReturnDistChart()
  }
}

const updateNavChart = () => {
  if (!navChart) return
  
  // 生成模拟净值数据
  const dates = []
  const navData = []
  const benchmarkData = []
  
  for (let i = 30; i >= 0; i--) {
    const date = new Date(Date.now() - i * 24 * 60 * 60 * 1000)
    dates.push(date.toISOString().split('T')[0])
    
    const nav = 1.0 + (Math.random() - 0.3) * 0.2 + (30 - i) * 0.005
    const benchmark = 1.0 + (Math.random() - 0.4) * 0.15 + (30 - i) * 0.003
    
    navData.push(nav.toFixed(4))
    benchmarkData.push(benchmark.toFixed(4))
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['策略净值', '基准净值']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      scale: true
    },
    series: [
      {
        name: '策略净值',
        type: 'line',
        data: navData,
        itemStyle: { color: '#3b82f6' },
        smooth: true
      },
      {
        name: '基准净值',
        type: 'line',
        data: benchmarkData,
        itemStyle: { color: '#6b7280' },
        smooth: true
      }
    ]
  }
  
  navChart.setOption(option)
}

const updateReturnDistChart = () => {
  if (!returnDistChart) return
  
  // 生成模拟收益分布数据
  const returns = []
  for (let i = 0; i < 100; i++) {
    returns.push((Math.random() - 0.5) * 0.1)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'value',
      name: '日收益率'
    },
    yAxis: {
      type: 'value',
      name: '频次'
    },
    series: [
      {
        type: 'histogram',
        data: returns,
        itemStyle: { color: '#10b981' }
      }
    ]
  }
  
  returnDistChart.setOption(option)
}

const refreshData = async () => {
  await loadStrategyData()
}

const refreshPositions = async () => {
  await loadPositions()
}

const refreshLogs = async () => {
  await loadLogs()
}

const showAllTrades = () => {
  router.push('/trading/orders')
}

const exportReport = () => {
  ElMessage.info('报告导出功能开发中...')
}

const startAutoRefresh = () => {
  refreshTimer = window.setInterval(async () => {
    if (currentStrategy.value) {
      await loadStrategyData()
    }
  }, 30000) // 30秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 生命周期
onMounted(async () => {
  await fetchStrategies()
  
  // 如果有运行中的策略，默认选择第一个
  if (runningStrategies.value.length > 0) {
    selectedStrategyId.value = runningStrategies.value[0].id
    await onStrategyChange(selectedStrategyId.value)
  }
  
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  
  if (navChart) {
    navChart.dispose()
  }
  if (returnDistChart) {
    returnDistChart.dispose()
  }
})

// 监听净值周期变化
watch(navPeriod, () => {
  updateNavChart()
})
</script>

<style scoped>
.strategy-monitor-page {
  min-height: calc(100vh - 64px);
  background-color: #f5f5f5;
}

:deep(.el-table) {
  font-size: 13px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  color: #606266;
  font-weight: 600;
}

:deep(.el-dialog) {
  border-radius: 8px;
}

:deep(.el-empty) {
  padding: 60px 0;
}

.code-log {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  line-height: 1.4;
}
</style> 