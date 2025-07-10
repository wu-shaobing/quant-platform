<template>
  <div class="dashboard-view">
    <!-- 页面头部 -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1 class="page-title">投资仪表盘</h1>
        <div class="header-actions">
          <el-button-group>
            <el-button 
              :type="timeRange === 'today' ? 'primary' : 'default'"
              size="small"
              @click="setTimeRange('today')"
            >
              今日
            </el-button>
            <el-button 
              :type="timeRange === 'week' ? 'primary' : 'default'"
              size="small"
              @click="setTimeRange('week')"
            >
              本周
            </el-button>
            <el-button 
              :type="timeRange === 'month' ? 'primary' : 'default'"
              size="small"
              @click="setTimeRange('month')"
            >
              本月
            </el-button>
          </el-button-group>
          
          <el-button 
            type="primary" 
            @click="refreshData"
            :loading="refreshing"
          >
            刷新数据
          </el-button>
        </div>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="metrics-grid">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon">📈</div>
              <div class="metric-info">
                <div class="metric-value">¥{{ accountMetrics.totalAssets.toLocaleString() }}</div>
                <div class="metric-label">总资产</div>
                <div class="metric-change positive">+{{ accountMetrics.totalProfitPercent.toFixed(2) }}%</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon">💰</div>
              <div class="metric-info">
                <div class="metric-value">+¥{{ accountMetrics.dailyProfit.toLocaleString() }}</div>
                <div class="metric-label">今日盈亏</div>
                <div class="metric-change positive">+{{ accountMetrics.dailyProfitPercent.toFixed(2) }}%</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon">📊</div>
              <div class="metric-info">
                <div class="metric-value">+¥{{ accountMetrics.totalProfit.toLocaleString() }}</div>
                <div class="metric-label">总盈亏</div>
                <div class="metric-change positive">+{{ accountMetrics.totalProfitPercent.toFixed(2) }}%</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon">🎯</div>
              <div class="metric-info">
                <div class="metric-value">{{ accountMetrics.positionCount }}</div>
                <div class="metric-label">持仓股票</div>
                <div class="metric-change">活跃策略: {{ accountMetrics.activeStrategies }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <el-row :gutter="20">
        <!-- 左侧区域 -->
        <el-col :span="16">
          <!-- 投资组合图表 -->
          <el-card class="dashboard-panel">
            <template #header>
              <div class="panel-header">
                <h3>投资组合趋势</h3>
                <div class="panel-actions">
                  <el-radio-group v-model="chartTimeframe" size="small">
                    <el-radio-button value="1D">1日</el-radio-button>
                    <el-radio-button value="1W">1周</el-radio-button>
                    <el-radio-button value="1M">1月</el-radio-button>
                    <el-radio-button value="3M">3月</el-radio-button>
                  </el-radio-group>
                </div>
              </div>
            </template>
            
            <div class="chart-container">
              <div ref="portfolioChartRef" style="height: 300px; width: 100%;"></div>
            </div>
          </el-card>

          <!-- 持仓列表 -->
          <el-card class="dashboard-panel" style="margin-top: 20px;">
            <template #header>
              <h3>持仓概览</h3>
            </template>
            
            <el-table :data="mockPositions" style="width: 100%">
              <el-table-column prop="symbol" label="股票代码" width="100" />
              <el-table-column prop="name" label="股票名称" width="120" />
              <el-table-column prop="quantity" label="数量" width="80" />
              <el-table-column prop="avgCost" label="成本价" width="80">
                <template #default="{ row }">
                  ¥{{ row.avgCost.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="currentPrice" label="现价" width="80">
                <template #default="{ row }">
                  ¥{{ row.currentPrice.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="marketValue" label="市值" width="100">
                <template #default="{ row }">
                  ¥{{ row.marketValue.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="pnl" label="盈亏" width="100">
                <template #default="{ row }">
                  <span :class="row.pnl >= 0 ? 'text-success' : 'text-danger'">
                    {{ row.pnl >= 0 ? '+' : '' }}¥{{ row.pnl.toFixed(2) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <!-- 右侧区域 -->
        <el-col :span="8">
          <!-- 市场概览 -->
          <el-card class="dashboard-panel">
            <template #header>
              <div class="panel-header">
                <h3>市场概览</h3>
                <el-button text size="small" @click="viewMarketDetail">
                  查看更多 →
                </el-button>
              </div>
            </template>
            
            <div class="market-indices">
              <div class="index-item" v-for="index in marketIndices" :key="index.symbol">
                <div class="index-info">
                  <span class="index-name">{{ index.name }}</span>
                  <span class="index-value">{{ index.value.toFixed(2) }}</span>
                </div>
                <div class="index-change" :class="index.change >= 0 ? 'text-success' : 'text-danger'">
                  {{ index.change >= 0 ? '+' : '' }}{{ index.change.toFixed(2) }} ({{ index.changePercent.toFixed(2) }}%)
                </div>
              </div>
            </div>
          </el-card>

          <!-- 热门股票 -->
          <el-card class="dashboard-panel" style="margin-top: 20px;">
            <template #header>
              <h3>今日热门</h3>
            </template>
            
            <div class="hot-stocks-list">
              <div class="hot-stock-item" v-for="stock in hotStocks" :key="stock.symbol">
                <div class="stock-info">
                  <span class="stock-symbol">{{ stock.symbol }}</span>
                  <span class="stock-name">{{ stock.name }}</span>
                </div>
                <div class="stock-price">
                  <span class="price">¥{{ stock.currentPrice.toFixed(2) }}</span>
                  <span class="change" :class="stock.change >= 0 ? 'text-success' : 'text-danger'">
                    {{ stock.change >= 0 ? '+' : '' }}{{ stock.changePercent.toFixed(2) }}%
                  </span>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 最新资讯 -->
          <el-card class="dashboard-panel" style="margin-top: 20px;">
            <template #header>
              <h3>最新资讯</h3>
            </template>
            
            <div class="news-list">
              <div class="news-item" v-for="news in latestNews" :key="news.id">
                <div class="news-title">{{ news.title }}</div>
                <div class="news-meta">
                  <span class="news-source">{{ news.source }}</span>
                  <span class="news-time">{{ formatTime(news.publishTime) }}</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { formatTime } from '@/utils/formatters'
import { useTradingStore } from '@/stores/modules/trading'
import { useMarketStore } from '@/stores/modules/market'
import { usePortfolioStore } from '@/stores/modules/portfolio'
import * as echarts from 'echarts'

const router = useRouter()

// Store引用
const tradingStore = useTradingStore()
const marketStore = useMarketStore()
const portfolioStore = usePortfolioStore()

// 状态
const refreshing = ref(false)
const timeRange = ref<'today' | 'week' | 'month'>('today')
const chartTimeframe = ref('1D')

// 图表引用
const portfolioChartRef = ref<HTMLElement>()
let portfolioChart: echarts.ECharts | null = null

// 计算属性 - 使用真实store数据
const accountMetrics = computed(() => ({
  totalAssets: tradingStore.account.totalAssets,
  dailyProfit: tradingStore.account.dailyProfit,
  dailyProfitPercent: tradingStore.account.dailyProfitPercent,
  totalProfit: tradingStore.account.totalProfit,
  totalProfitPercent: tradingStore.account.totalProfitPercent,
  positionCount: tradingStore.positions.length,
  activeStrategies: 3 // 这里需要从策略store获取
}))

const marketIndices = computed(() => {
  return Object.entries(marketStore.indices).map(([symbol, data]) => ({
    symbol,
    name: getIndexName(symbol),
    value: data.currentPrice,
    change: data.change,
    changePercent: data.changePercent
  }))
})

const hotStocks = computed(() => {
  return marketStore.hotStocks.slice(0, 5)
})

const latestNews = computed(() => {
  return marketStore.news.slice(0, 3)
})

// 模拟数据 - 保留作为后备
const mockPositions = ref([
  { symbol: '000001', name: '平安银行', quantity: 1000, avgCost: 12.50, currentPrice: 13.20, marketValue: 13200, pnl: 700 },
  { symbol: '000002', name: '万科A', quantity: 500, avgCost: 24.00, currentPrice: 23.50, marketValue: 11750, pnl: -250 },
  { symbol: '000858', name: '五粮液', quantity: 100, avgCost: 150.00, currentPrice: 158.00, marketValue: 15800, pnl: 800 }
])

// 方法
const getIndexName = (symbol: string): string => {
  const nameMap: Record<string, string> = {
    'SH000001': '上证指数',
    'SZ399001': '深证成指',
    'SZ399006': '创业板指',
    'SH000688': '科创50'
  }
  return nameMap[symbol] || symbol
}

const setTimeRange = (range: 'today' | 'week' | 'month') => {
  timeRange.value = range
  // 重新加载对应时间范围的数据
  loadPortfolioData(range)
}

const refreshData = async () => {
  refreshing.value = true
  try {
    await Promise.all([
      tradingStore.refresh(),
      marketStore.fetchMarketOverview(),
      marketStore.fetchHotStocks(),
      marketStore.fetchNews()
    ])
  } catch (error) {
    console.error('刷新数据失败:', error)
  } finally {
    refreshing.value = false
  }
}

const viewMarketDetail = () => {
  router.push('/market')
}

const loadPortfolioData = async (range: string) => {
  try {
    await portfolioStore.fetchPortfolioTrend({
      timeRange: range,
      symbol: 'portfolio'
    })
    updatePortfolioChart()
  } catch (error) {
    console.error('加载投资组合数据失败:', error)
  }
}

const initPortfolioChart = () => {
  if (!portfolioChartRef.value) return
  
  portfolioChart = echarts.init(portfolioChartRef.value)
  updatePortfolioChart()
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    portfolioChart?.resize()
  })
}

const updatePortfolioChart = () => {
  if (!portfolioChart) return
  
  const trendData = portfolioStore.portfolioTrend
  
  const option = {
    title: {
      text: '投资组合价值趋势',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `${data.name}<br/>总资产: ¥${data.value.toLocaleString()}`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: trendData.map(item => item.date),
      axisLine: {
        lineStyle: {
          color: '#e0e6ed'
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLine: {
        lineStyle: {
          color: '#e0e6ed'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0'
        }
      }
    },
    series: [
      {
        name: '总资产',
        type: 'line',
        smooth: true,
        data: trendData.map(item => item.totalAssets),
        lineStyle: {
          color: '#409eff',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.1)' }
            ]
          }
        }
      }
    ]
  }
  
  portfolioChart.setOption(option)
}

onMounted(async () => {
  try {
    // 初始化数据
    await Promise.allSettled([
      tradingStore.initialize(),
      marketStore.initialize(),
      portfolioStore.initialize()
    ])
    
    // 初始化图表
    initPortfolioChart()
    
    // 加载投资组合数据
    await loadPortfolioData(timeRange.value)
  } catch (error) {
    console.error('仪表盘初始化失败:', error)
    // 即使初始化失败，也要初始化图表
    initPortfolioChart()
  }
})
</script>

<style scoped>
.dashboard-view {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.dashboard-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.metrics-grid {
  margin-bottom: 24px;
}

.metric-card {
  height: 120px;
}

.metric-content {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 100%;
}

.metric-icon {
  font-size: 32px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f9ff;
  border-radius: 8px;
}

.metric-info {
  flex: 1;
}

.metric-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.metric-change {
  font-size: 12px;
  color: #999;
}

.metric-change.positive {
  color: #67c23a;
}

.dashboard-content {
  margin-top: 24px;
}

.dashboard-panel {
  margin-bottom: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.chart-container {
  padding: 16px 0;
}

.market-indices {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.index-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.index-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.index-name {
  font-size: 14px;
  color: #333;
}

.index-value {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.index-change {
  font-size: 14px;
  text-align: right;
}

.hot-stocks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hot-stock-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-symbol {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.stock-name {
  font-size: 12px;
  color: #666;
}

.stock-price {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: right;
}

.price {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.change {
  font-size: 12px;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.news-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.news-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
  line-height: 1.4;
}

.news-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}
</style>