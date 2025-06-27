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
                <div class="metric-value">¥100,000.00</div>
                <div class="metric-label">总资产</div>
                <div class="metric-change positive">+5.2%</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon">💰</div>
              <div class="metric-info">
                <div class="metric-value">+¥2,500.00</div>
                <div class="metric-label">今日盈亏</div>
                <div class="metric-change positive">+2.5%</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon">📊</div>
              <div class="metric-info">
                <div class="metric-value">+¥15,000.00</div>
                <div class="metric-label">总盈亏</div>
                <div class="metric-change positive">+15.0%</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-icon">🎯</div>
              <div class="metric-info">
                <div class="metric-value">8</div>
                <div class="metric-label">持仓股票</div>
                <div class="metric-change">活跃策略: 3</div>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { formatTime } from '@/utils/formatters'

const router = useRouter()

// 状态
const refreshing = ref(false)
const timeRange = ref<'today' | 'week' | 'month'>('today')
const chartTimeframe = ref('1D')

// 图表引用
const portfolioChartRef = ref<HTMLElement>()

// 模拟数据
const mockPositions = ref([
  { symbol: '000001', name: '平安银行', quantity: 1000, avgCost: 12.50, currentPrice: 13.20, marketValue: 13200, pnl: 700 },
  { symbol: '000002', name: '万科A', quantity: 500, avgCost: 24.00, currentPrice: 23.50, marketValue: 11750, pnl: -250 },
  { symbol: '000858', name: '五粮液', quantity: 100, avgCost: 150.00, currentPrice: 158.00, marketValue: 15800, pnl: 800 }
])

const marketIndices = ref([
  { symbol: 'SH000001', name: '上证指数', value: 3245.67, change: 12.34, changePercent: 0.38 },
  { symbol: 'SZ399001', name: '深证成指', value: 12456.78, change: -23.45, changePercent: -0.19 },
  { symbol: 'SZ399006', name: '创业板指', value: 2345.67, change: 8.90, changePercent: 0.38 }
])

const hotStocks = ref([
  { symbol: '000001', name: '平安银行', currentPrice: 12.34, change: 0.56, changePercent: 4.76 },
  { symbol: '000002', name: '万科A', currentPrice: 23.45, change: -0.78, changePercent: -3.22 },
  { symbol: '000858', name: '五粮液', currentPrice: 156.78, change: 5.67, changePercent: 3.75 }
])

const latestNews = ref([
  {
    id: '1',
    title: '央行降准释放长期资金约1万亿元',
    source: '财经网',
    publishTime: Date.now() - 3600000
  },
  {
    id: '2', 
    title: '科技股集体上涨，芯片板块领涨',
    source: '证券时报',
    publishTime: Date.now() - 7200000
  }
])

// 方法
const setTimeRange = (range: 'today' | 'week' | 'month') => {
  timeRange.value = range
}

const refreshData = async () => {
  refreshing.value = true
  // 模拟刷新
  setTimeout(() => {
    refreshing.value = false
  }, 1000)
}

const viewMarketDetail = () => {
  router.push('/market')
}

onMounted(() => {
  // 初始化图表等
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