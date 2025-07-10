<template>
  <div class="portfolio-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>投资组合</h1>
          <p>资产配置与绩效分析</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="openRebalanceDialog">
            <el-icon><Setting /></el-icon>
            再平衡
          </el-button>
          <el-button @click="exportReport">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
          <el-button @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 投资组合概览 -->
    <div class="overview-section">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="overview-card">
            <div class="card-header">
              <h3>总资产</h3>
              <el-icon class="card-icon"><Wallet /></el-icon>
            </div>
            <div class="card-content">
              <div class="value">{{ formatCurrency(totalAssets) }}</div>
              <div class="change" :class="getPriceClass(totalChange)">
                {{ formatChange(totalChange, totalChangePercent) }}
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="overview-card">
            <div class="card-header">
              <h3>持仓市值</h3>
              <el-icon class="card-icon"><PieChart /></el-icon>
            </div>
            <div class="card-content">
              <div class="value">{{ formatCurrency(positionValue) }}</div>
              <div class="change" :class="getPriceClass(positionChange)">
                {{ formatChange(positionChange, positionChangePercent) }}
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="overview-card">
            <div class="card-header">
              <h3>可用资金</h3>
              <el-icon class="card-icon"><Money /></el-icon>
            </div>
            <div class="card-content">
              <div class="value">{{ formatCurrency(availableCash) }}</div>
              <div class="ratio">占比 {{ formatPercent(availableCash / totalAssets) }}</div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="overview-card">
            <div class="card-header">
              <h3>今日盈亏</h3>
              <el-icon class="card-icon"><TrendCharts /></el-icon>
            </div>
            <div class="card-content">
              <div class="value" :class="getPriceClass(todayPnl)">
                {{ formatCurrency(todayPnl) }}
              </div>
              <div class="change" :class="getPriceClass(todayPnlPercent)">
                {{ formatPercent(todayPnlPercent) }}
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <el-row :gutter="16">
        <!-- 左侧：持仓列表 -->
        <el-col :span="16">
          <div class="content-card">
            <div class="card-header">
              <h3>持仓明细</h3>
              <div class="header-actions">
                <el-input
                  v-model="searchQuery"
                  placeholder="搜索股票..."
                  style="width: 200px"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                
                <el-select v-model="sortBy" placeholder="排序方式" style="width: 120px">
                  <el-option label="市值" value="marketValue" />
                  <el-option label="盈亏" value="pnl" />
                  <el-option label="盈亏率" value="pnlPercent" />
                  <el-option label="持仓比例" value="weight" />
                </el-select>
              </div>
            </div>
            
            <div class="position-list">
              <el-table
                :data="filteredPositions"
                v-loading="loading"
                @row-click="handleRowClick"
                row-class-name="position-row"
                show-summary
                :summary-method="getSummaries"
              >
                <el-table-column prop="symbol" label="股票代码" width="100" />
                
                <el-table-column prop="name" label="股票名称" min-width="120" />
                
                <el-table-column prop="quantity" label="持仓数量" width="100" align="right">
                  <template #default="{ row }">
                    {{ formatNumber(row.quantity) }}
                  </template>
                </el-table-column>
                
                <el-table-column prop="avgPrice" label="成本价" width="100" align="right">
                  <template #default="{ row }">
                    {{ formatPrice(row.avgPrice) }}
                  </template>
                </el-table-column>
                
                <el-table-column prop="currentPrice" label="现价" width="100" align="right">
                  <template #default="{ row }">
                    <span :class="getPriceClass(row.changePercent)">
                      {{ formatPrice(row.currentPrice) }}
                    </span>
                  </template>
                </el-table-column>
                
                <el-table-column prop="marketValue" label="市值" width="120" align="right">
                  <template #default="{ row }">
                    {{ formatCurrency(row.marketValue) }}
                  </template>
                </el-table-column>
                
                <el-table-column prop="costValue" label="成本" width="120" align="right">
                  <template #default="{ row }">
                    {{ formatCurrency(row.costValue) }}
                  </template>
                </el-table-column>
                
                <el-table-column prop="pnl" label="盈亏" width="120" align="right">
                  <template #default="{ row }">
                    <div class="pnl-cell">
                      <div :class="getPriceClass(row.pnl)">
                        {{ formatCurrency(row.pnl) }}
                      </div>
                      <div :class="getPriceClass(row.pnlPercent)" class="pnl-percent">
                        {{ formatPercent(row.pnlPercent) }}
                      </div>
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column prop="weight" label="占比" width="80" align="right">
                  <template #default="{ row }">
                    {{ formatPercent(row.weight) }}
                  </template>
                </el-table-column>
                
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button-group>
                      <el-button size="small" @click.stop="buyStock(row)">
                        买入
                      </el-button>
                      <el-button size="small" @click.stop="sellStock(row)">
                        卖出
                      </el-button>
                    </el-button-group>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-col>
        
        <!-- 右侧：资产配置 -->
        <el-col :span="8">
          <!-- 资产配置饼图 -->
          <div class="content-card">
            <div class="card-header">
              <h3>资产配置</h3>
              <el-button size="small" @click="toggleChartType">
                {{ chartType === 'pie' ? '柱状图' : '饼图' }}
              </el-button>
            </div>
            <div class="chart-container">
              <PositionPieChart 
                :data="positionChartData"
                :chart-type="chartType"
                height="300px"
              />
            </div>
          </div>
          
          <!-- 行业分布 -->
          <div class="content-card" style="margin-top: 16px;">
            <div class="card-header">
              <h3>行业分布</h3>
            </div>
            <div class="industry-distribution">
              <div
                v-for="industry in industryDistribution"
                :key="industry.name"
                class="industry-item"
              >
                <div class="industry-info">
                  <span class="industry-name">{{ industry.name }}</span>
                  <span class="industry-weight">{{ formatPercent(industry.weight) }}</span>
                </div>
                <div class="industry-bar">
                  <div 
                    class="industry-progress"
                    :style="{ width: `${industry.weight * 100}%` }"
                  />
                </div>
                <div class="industry-value">
                  {{ formatCurrency(industry.value) }}
                </div>
              </div>
            </div>
          </div>
          
          <!-- 风险指标 -->
          <div class="content-card" style="margin-top: 16px;">
            <div class="card-header">
              <h3>风险指标</h3>
            </div>
            <div class="risk-metrics">
              <div class="metric-item">
                <div class="metric-label">组合波动率</div>
                <div class="metric-value">{{ formatPercent(portfolioVolatility) }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">夏普比率</div>
                <div class="metric-value">{{ formatNumber(sharpeRatio, 2) }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">最大回撤</div>
                <div class="metric-value price-down">{{ formatPercent(maxDrawdown) }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">Beta值</div>
                <div class="metric-value">{{ formatNumber(beta, 2) }}</div>
              </div>
              <div class="metric-item">
                <div class="metric-label">集中度风险</div>
                <div class="metric-value" :class="getConcentrationRiskClass()">
                  {{ getConcentrationRiskText() }}
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 绩效分析图表 -->
    <div class="performance-section">
      <div class="content-card">
        <div class="card-header">
          <h3>绩效走势</h3>
          <div class="header-actions">
            <el-radio-group v-model="performancePeriod" size="small">
              <el-radio-button value="1D">1日</el-radio-button>
              <el-radio-button value="1W">1周</el-radio-button>
              <el-radio-button value="1M">1月</el-radio-button>
              <el-radio-button value="3M">3月</el-radio-button>
              <el-radio-button value="6M">6月</el-radio-button>
              <el-radio-button value="1Y">1年</el-radio-button>
              <el-radio-button value="ALL">全部</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div class="performance-chart">
          <AssetTrendChart
            :data="performanceData"
            :period="performancePeriod"
            height="400px"
            :show-benchmark="true"
          />
        </div>
      </div>
    </div>

    <!-- 再平衡对话框 -->
    <el-dialog
      v-model="rebalanceDialogVisible"
      title="投资组合再平衡"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="rebalance-content">
        <div class="rebalance-info">
          <h4>当前配置偏离度</h4>
          <div class="deviation-list">
            <div
              v-for="deviation in deviations"
              :key="deviation.symbol"
              class="deviation-item"
            >
              <span class="symbol">{{ deviation.symbol }}</span>
              <span class="current">当前: {{ formatPercent(deviation.current) }}</span>
              <span class="target">目标: {{ formatPercent(deviation.target) }}</span>
              <span class="diff" :class="getPriceClass(deviation.diff)">
                偏离: {{ formatPercent(Math.abs(deviation.diff)) }}
              </span>
            </div>
          </div>
        </div>
        
        <div class="rebalance-actions">
          <el-button @click="rebalanceDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="executeRebalance">
            执行再平衡
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Setting,
  Download,
  Refresh,
  Search,
  Wallet,
  PieChart,
  Money,
  TrendCharts
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatCurrency, formatPrice, formatPercent, formatNumber, formatChange } from '@/utils/formatters'
import PositionPieChart from '@/components/charts/PositionPieChart.vue'
import AssetTrendChart from '@/components/charts/AssetTrendChart.vue'

// Router
const router = useRouter()

// 响应式状态
const loading = ref(false)
const searchQuery = ref('')
const sortBy = ref('marketValue')
const chartType = ref<'pie' | 'bar'>('pie')
const performancePeriod = ref('1M')
const rebalanceDialogVisible = ref(false)

// 投资组合数据
const totalAssets = ref(1250000)
const positionValue = ref(1100000)
const availableCash = ref(150000)
const totalChange = ref(25000)
const totalChangePercent = ref(0.0204)
const positionChange = ref(22000)
const positionChangePercent = ref(0.0204)
const todayPnl = ref(8500)
const todayPnlPercent = ref(0.0069)

// 风险指标
const portfolioVolatility = ref(0.15)
const sharpeRatio = ref(1.42)
const maxDrawdown = ref(-0.08)
const beta = ref(1.05)

// 模拟持仓数据
const positions = ref([
  {
    symbol: '000001',
    name: '平安银行',
    quantity: 10000,
    avgPrice: 12.50,
    currentPrice: 13.25,
    marketValue: 132500,
    costValue: 125000,
    pnl: 7500,
    pnlPercent: 0.06,
    weight: 0.106,
    changePercent: 0.015,
    industry: '银行'
  },
  {
    symbol: '000002',
    name: '万科A',
    quantity: 5000,
    avgPrice: 18.80,
    currentPrice: 17.95,
    marketValue: 89750,
    costValue: 94000,
    pnl: -4250,
    pnlPercent: -0.045,
    weight: 0.072,
    changePercent: -0.012,
    industry: '房地产'
  },
  {
    symbol: '600036',
    name: '招商银行',
    quantity: 3000,
    avgPrice: 35.60,
    currentPrice: 38.45,
    marketValue: 115350,
    costValue: 106800,
    pnl: 8550,
    pnlPercent: 0.08,
    weight: 0.092,
    changePercent: 0.022,
    industry: '银行'
  }
])

// 计算属性
const filteredPositions = computed(() => {
  let filtered = positions.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(position => 
      position.symbol.toLowerCase().includes(query) ||
      position.name.toLowerCase().includes(query)
    )
  }

  // 排序
  filtered.sort((a, b) => {
    const aValue = a[sortBy.value as keyof typeof a] as number
    const bValue = b[sortBy.value as keyof typeof b] as number
    return bValue - aValue
  })

  return filtered
})

const positionChartData = computed(() => {
  return positions.value.map(position => ({
    name: position.name,
    value: position.marketValue,
    symbol: position.symbol
  }))
})

const industryDistribution = computed(() => {
  const industries = new Map()
  
  positions.value.forEach(position => {
    const industry = position.industry
    if (industries.has(industry)) {
      const existing = industries.get(industry)
      existing.value += position.marketValue
    } else {
      industries.set(industry, {
        name: industry,
        value: position.marketValue
      })
    }
  })
  
  const result = Array.from(industries.values())
  result.forEach(industry => {
    industry.weight = industry.value / positionValue.value
  })
  
  return result.sort((a, b) => b.value - a.value)
})

const performanceData = computed(() => {
  // 模拟绩效数据
  const data = []
  const now = Date.now()
  const days = performancePeriod.value === '1D' ? 1 : 
                performancePeriod.value === '1W' ? 7 :
                performancePeriod.value === '1M' ? 30 :
                performancePeriod.value === '3M' ? 90 :
                performancePeriod.value === '6M' ? 180 :
                performancePeriod.value === '1Y' ? 365 : 365

  for (let i = days; i >= 0; i--) {
    const date = now - i * 24 * 60 * 60 * 1000
    const baseValue = 1000000
    const randomChange = (Math.random() - 0.5) * 0.02
    const value = baseValue * (1 + randomChange * (days - i) / days)
    
    data.push({
      date,
      value,
      benchmark: baseValue * (1 + 0.08 * (days - i) / 365) // 8%年化基准
    })
  }
  
  return data
})

const deviations = ref([
  { symbol: '000001', current: 0.106, target: 0.10, diff: 0.006 },
  { symbol: '000002', current: 0.072, target: 0.08, diff: -0.008 },
  { symbol: '600036', current: 0.092, target: 0.09, diff: 0.002 }
])

// 方法
const refreshData = async () => {
  try {
    loading.value = true
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('数据刷新成功')
  } catch {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const handleRowClick = (row: { symbol: string; [key: string]: unknown }) => {
  router.push(`/market/stock/${row.symbol}`)
}

const buyStock = (position: { symbol: string; [key: string]: unknown }) => {
  router.push(`/trading?symbol=${position.symbol}&side=buy`)
}

const sellStock = (position: { symbol: string; [key: string]: unknown }) => {
  router.push(`/trading?symbol=${position.symbol}&side=sell`)
}

const toggleChartType = () => {
  chartType.value = chartType.value === 'pie' ? 'bar' : 'pie'
}

const openRebalanceDialog = () => {
  rebalanceDialogVisible.value = true
}

const executeRebalance = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要执行投资组合再平衡吗？这将产生交易费用。',
      '再平衡确认',
      {
        confirmButtonText: '确定执行',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 模拟再平衡执行
    ElMessage.success('再平衡指令已提交')
    rebalanceDialogVisible.value = false
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('再平衡执行失败')
    }
  }
}

const exportReport = async () => {
  try {
    ElMessage.success('报告导出成功')
  } catch {
    ElMessage.error('报告导出失败')
  }
}

const getPriceClass = (value: number) => {
  if (value > 0) return 'price-up'
  if (value < 0) return 'price-down'
  return 'price-neutral'
}

const getConcentrationRiskClass = () => {
  const maxWeight = Math.max(...positions.value.map(p => p.weight))
  if (maxWeight > 0.3) return 'risk-high'
  if (maxWeight > 0.2) return 'risk-medium'
  return 'risk-low'
}

const getConcentrationRiskText = () => {
  const maxWeight = Math.max(...positions.value.map(p => p.weight))
  if (maxWeight > 0.3) return '高'
  if (maxWeight > 0.2) return '中'
  return '低'
}

const getSummaries = (param: { columns: Array<{ property?: string; [key: string]: unknown }>; [key: string]: unknown }) => {
  const { columns } = param
  const sums: (string | number)[] = []
  
  columns.forEach((column: { property?: string; [key: string]: unknown }, index: number) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }
    
    if (column.property === 'marketValue') {
      sums[index] = formatCurrency(positionValue.value)
    } else if (column.property === 'costValue') {
      const totalCost = positions.value.reduce((sum, position) => sum + position.costValue, 0)
      sums[index] = formatCurrency(totalCost)
    } else if (column.property === 'pnl') {
      const totalPnl = positions.value.reduce((sum, position) => sum + position.pnl, 0)
      sums[index] = formatCurrency(totalPnl)
    } else {
      sums[index] = ''
    }
  })
  
  return sums
}

// 生命周期
onMounted(async () => {
  await refreshData()
})
</script>

<style scoped>
.portfolio-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.title-section h1 {
  margin: 0 0 4px 0;
  font-size: 24px;
  color: #333;
}

.title-section p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.action-section {
  display: flex;
  gap: 12px;
}

.overview-section {
  margin-bottom: 20px;
}

.overview-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-header h3 {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.card-icon {
  font-size: 20px;
  color: #409EFF;
}

.card-content .value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.card-content .change {
  font-size: 14px;
}

.card-content .ratio {
  font-size: 12px;
  color: #666;
}

.main-content {
  margin-bottom: 20px;
}

.content-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.content-card .card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
}

.content-card .card-header h3 {
  font-size: 16px;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.position-list {
  padding: 0;
}

.position-row {
  cursor: pointer;
}

.position-row:hover {
  background-color: #f5f7fa;
}

.pnl-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.pnl-percent {
  font-size: 12px;
  margin-top: 2px;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.price-neutral {
  color: #909399;
}

.chart-container {
  padding: 20px;
}

.industry-distribution {
  padding: 20px;
}

.industry-item {
  margin-bottom: 16px;
}

.industry-item:last-child {
  margin-bottom: 0;
}

.industry-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 14px;
}

.industry-name {
  color: #333;
}

.industry-weight {
  color: #666;
}

.industry-bar {
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  margin-bottom: 4px;
}

.industry-progress {
  height: 100%;
  background: #409EFF;
  border-radius: 2px;
  transition: width 0.3s;
}

.industry-value {
  font-size: 12px;
  color: #666;
  text-align: right;
}

.risk-metrics {
  padding: 20px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
}

.metric-item:last-child {
  margin-bottom: 0;
}

.metric-label {
  color: #666;
}

.metric-value {
  font-weight: 500;
  color: #333;
}

.risk-high {
  color: #f56c6c;
}

.risk-medium {
  color: #e6a23c;
}

.risk-low {
  color: #67c23a;
}

.performance-section {
  margin-bottom: 20px;
}

.performance-chart {
  padding: 20px;
}

.rebalance-content {
  padding: 20px;
}

.rebalance-info h4 {
  margin: 0 0 16px 0;
  color: #333;
}

.deviation-list {
  margin-bottom: 20px;
}

.deviation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.deviation-item:last-child {
  border-bottom: none;
}

.symbol {
  font-weight: 500;
  color: #333;
}

.current, .target {
  color: #666;
}

.diff {
  font-weight: 500;
}

.rebalance-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .portfolio-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .action-section {
    width: 100%;
    justify-content: flex-end;
  }
  
  .overview-section .el-col {
    margin-bottom: 16px;
  }
  
  .main-content .el-col {
    margin-bottom: 16px;
  }
  
  .deviation-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>