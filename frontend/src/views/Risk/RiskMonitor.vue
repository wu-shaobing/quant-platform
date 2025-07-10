<template>
  <div class="risk-monitor-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>风险监控</h1>
          <p>实时风险监控与预警系统</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="openRiskSettings">
            <el-icon><Setting /></el-icon>
            风险设置
          </el-button>
          <el-button @click="exportRiskReport">
            <el-icon><Download /></el-icon>
            风险报告
          </el-button>
          <el-button @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 风险概览仪表盘 -->
    <div class="risk-dashboard">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="risk-card" :class="getRiskLevelClass(overallRiskLevel)">
            <div class="card-header">
              <h3>整体风险等级</h3>
              <el-icon class="risk-icon"><Warning /></el-icon>
            </div>
            <div class="card-content">
              <div class="risk-level">{{ getRiskLevelText(overallRiskLevel) }}</div>
              <div class="risk-score">风险评分: {{ riskScore }}/100</div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="risk-card">
            <div class="card-header">
              <h3>VaR (95%)</h3>
              <el-icon class="risk-icon"><TrendCharts /></el-icon>
            </div>
            <div class="card-content">
              <div class="risk-value">{{ formatCurrency(var95) }}</div>
              <div class="risk-change" :class="getPriceClass(varChange)">
                较昨日 {{ formatPercent(varChange) }}
              </div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="risk-card">
            <div class="card-header">
              <h3>最大回撤</h3>
              <el-icon class="risk-icon"><Bottom /></el-icon>
            </div>
            <div class="card-content">
              <div class="risk-value price-down">{{ formatPercent(maxDrawdown) }}</div>
              <div class="risk-limit">限制: {{ formatPercent(drawdownLimit) }}</div>
            </div>
          </div>
        </el-col>
        
        <el-col :span="6">
          <div class="risk-card">
            <div class="card-header">
              <h3>杠杆比率</h3>
              <el-icon class="risk-icon"><ScaleToOriginal /></el-icon>
            </div>
            <div class="card-content">
              <div class="risk-value">{{ formatNumber(leverageRatio, 2) }}x</div>
              <div class="risk-limit">限制: {{ formatNumber(leverageLimit, 2) }}x</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 风险预警 -->
    <div class="risk-alerts" v-if="riskAlerts.length > 0">
      <div class="content-card">
        <div class="card-header">
          <h3>风险预警</h3>
          <el-badge :value="riskAlerts.length" type="danger">
            <el-button size="small" @click="clearAlerts">清除全部</el-button>
          </el-badge>
        </div>
        <div class="alerts-list">
          <el-alert
            v-for="alert in riskAlerts"
            :key="alert.id"
            :title="alert.title"
            :description="alert.description"
            :type="alert.type"
            :closable="true"
            @close="dismissAlert(alert.id)"
            class="alert-item"
          >
            <template #default>
              <div class="alert-content">
                <div class="alert-main">
                  <div class="alert-title">{{ alert.title }}</div>
                  <div class="alert-desc">{{ alert.description }}</div>
                </div>
                <div class="alert-actions">
                  <el-button size="small" @click="viewAlertDetail(alert)">
                    详情
                  </el-button>
                  <el-button size="small" type="primary" @click="handleAlert(alert)">
                    处理
                  </el-button>
                </div>
              </div>
            </template>
          </el-alert>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <el-row :gutter="16">
        <!-- 左侧：风险指标 -->
        <el-col :span="16">
          <div class="content-card">
            <div class="card-header">
              <h3>风险指标监控</h3>
              <div class="header-actions">
                <el-select v-model="timeRange" placeholder="时间范围" style="width: 120px">
                  <el-option label="1天" value="1D" />
                  <el-option label="1周" value="1W" />
                  <el-option label="1月" value="1M" />
                  <el-option label="3月" value="3M" />
                  <el-option label="6月" value="6M" />
                  <el-option label="1年" value="1Y" />
                </el-select>
              </div>
            </div>
            
            <div class="risk-metrics-table">
              <el-table :data="riskMetrics" v-loading="loading">
                <el-table-column prop="name" label="风险指标" width="150" />
                
                <el-table-column prop="current" label="当前值" width="120" align="right">
                  <template #default="{ row }">
                    <span :class="getRiskValueClass(row.current, row.threshold)">
                      {{ formatRiskValue(row.current, row.type) }}
                    </span>
                  </template>
                </el-table-column>
                
                <el-table-column prop="threshold" label="阈值" width="120" align="right">
                  <template #default="{ row }">
                    {{ formatRiskValue(row.threshold, row.type) }}
                  </template>
                </el-table-column>
                
                <el-table-column prop="status" label="状态" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag :type="getRiskStatusType(row.status)">
                      {{ getRiskStatusText(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column prop="trend" label="趋势" width="100" align="center">
                  <template #default="{ row }">
                    <el-icon :class="getTrendClass(row.trend)">
                      <component :is="getTrendIcon(row.trend)" />
                    </el-icon>
                  </template>
                </el-table-column>
                
                <el-table-column label="历史图表" min-width="200">
                  <template #default="{ row }">
                    <div class="mini-chart">
                      <RiskTrendChart 
                        :data="row.history"
                        :threshold="row.threshold"
                        height="40px"
                      />
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column label="操作" width="100" fixed="right">
                  <template #default="{ row }">
                    <el-button size="small" @click="viewRiskDetail(row)">
                      详情
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-col>
        
        <!-- 右侧：风险分布 -->
        <el-col :span="8">
          <!-- 风险分布图 -->
          <div class="content-card">
            <div class="card-header">
              <h3>风险分布</h3>
              <el-button size="small" @click="toggleRiskChartType">
                {{ riskChartType === 'pie' ? '柱状图' : '饼图' }}
              </el-button>
            </div>
            <div class="chart-container">
              <RiskDistributionChart 
                :data="riskDistributionData"
                :chart-type="riskChartType"
                height="300px"
              />
            </div>
          </div>
          
          <!-- 风险限额使用 -->
          <div class="content-card" style="margin-top: 16px;">
            <div class="card-header">
              <h3>风险限额使用</h3>
            </div>
            <div class="risk-limits">
              <div
                v-for="limit in riskLimits"
                :key="limit.name"
                class="limit-item"
              >
                <div class="limit-info">
                  <span class="limit-name">{{ limit.name }}</span>
                  <span class="limit-usage">{{ formatPercent(limit.usage) }}</span>
                </div>
                <div class="limit-bar">
                  <el-progress
                    :percentage="limit.usage * 100"
                    :color="getLimitColor(limit.usage)"
                    :stroke-width="8"
                    :show-text="false"
                  />
                </div>
                <div class="limit-values">
                  <span class="current">{{ formatRiskValue(limit.current, limit.type) }}</span>
                  <span class="total">/ {{ formatRiskValue(limit.total, limit.type) }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 压力测试结果 -->
          <div class="content-card" style="margin-top: 16px;">
            <div class="card-header">
              <h3>压力测试</h3>
              <el-button size="small" @click="runStressTest">
                运行测试
              </el-button>
            </div>
            <div class="stress-test-results">
              <div
                v-for="scenario in stressTestScenarios"
                :key="scenario.name"
                class="scenario-item"
              >
                <div class="scenario-header">
                  <span class="scenario-name">{{ scenario.name }}</span>
                  <span class="scenario-result" :class="getPriceClass(scenario.result)">
                    {{ formatPercent(scenario.result) }}
                  </span>
                </div>
                <div class="scenario-desc">{{ scenario.description }}</div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 风险设置对话框 -->
    <el-dialog
      v-model="riskSettingsVisible"
      title="风险控制设置"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="risk-settings">
        <el-form :model="riskConfig" label-width="120px">
          <el-form-item label="VaR置信度">
            <el-slider
              v-model="riskConfig.varConfidence"
              :min="90"
              :max="99"
              :step="1"
              :format-tooltip="(val) => `${val}%`"
            />
          </el-form-item>
          
          <el-form-item label="最大回撤限制">
            <el-input-number
              v-model="riskConfig.maxDrawdownLimit"
              :min="0"
              :max="1"
              :step="0.01"
              :precision="2"
              :formatter="(value) => `${(value * 100).toFixed(2)}%`"
            />
          </el-form-item>
          
          <el-form-item label="杠杆限制">
            <el-input-number
              v-model="riskConfig.leverageLimit"
              :min="1"
              :max="10"
              :step="0.1"
              :precision="1"
            />
          </el-form-item>
          
          <el-form-item label="集中度限制">
            <el-input-number
              v-model="riskConfig.concentrationLimit"
              :min="0"
              :max="1"
              :step="0.01"
              :precision="2"
              :formatter="(value) => `${(value * 100).toFixed(2)}%`"
            />
          </el-form-item>
          
          <el-form-item label="预警通知">
            <el-checkbox-group v-model="riskConfig.alertChannels">
              <el-checkbox value="email">邮件</el-checkbox>
              <el-checkbox value="sms">短信</el-checkbox>
              <el-checkbox value="push">推送</el-checkbox>
            </el-checkbox-group>
          </el-form-item>
        </el-form>
        
        <div class="dialog-actions">
          <el-button @click="riskSettingsVisible = false">取消</el-button>
          <el-button type="primary" @click="saveRiskSettings">
            保存设置
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  Setting,
  Download,
  Refresh,
  Warning,
  TrendCharts,
  Bottom,
  ScaleToOriginal,
  ArrowUp,
  ArrowDown,
  Minus
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatCurrency, formatPercent, formatNumber } from '@/utils/formatters'
import RiskTrendChart from '@/components/charts/RiskTrendChart.vue'
import RiskDistributionChart from '@/components/charts/RiskDistributionChart.vue'

// 响应式状态
const loading = ref(false)
const timeRange = ref('1M')
const riskChartType = ref<'pie' | 'bar'>('pie')
const riskSettingsVisible = ref(false)

// 风险数据
const overallRiskLevel = ref(2) // 1: 低, 2: 中, 3: 高
const riskScore = ref(72)
const var95 = ref(-125000)
const varChange = ref(-0.05)
const maxDrawdown = ref(-0.08)
const drawdownLimit = ref(-0.15)
const leverageRatio = ref(1.8)
const leverageLimit = ref(3.0)

// 风险预警
const riskAlerts = ref([
  {
    id: 1,
    title: '单一持仓集中度过高',
    description: '平安银行持仓占比达到15.2%，超过集中度限制10%',
    type: 'warning',
    timestamp: Date.now() - 1000 * 60 * 30,
    severity: 'medium'
  },
  {
    id: 2,
    title: 'VaR值接近限制',
    description: '当前VaR值-125,000，接近设定限制-150,000',
    type: 'error',
    timestamp: Date.now() - 1000 * 60 * 15,
    severity: 'high'
  }
])

// 风险指标
const riskMetrics = ref([
  {
    name: 'VaR (95%)',
    current: -125000,
    threshold: -150000,
    status: 'warning',
    trend: 'up',
    type: 'currency',
    history: generateRandomHistory()
  },
  {
    name: '波动率',
    current: 0.18,
    threshold: 0.25,
    status: 'normal',
    trend: 'down',
    type: 'percent',
    history: generateRandomHistory()
  },
  {
    name: '最大回撤',
    current: -0.08,
    threshold: -0.15,
    status: 'normal',
    trend: 'stable',
    type: 'percent',
    history: generateRandomHistory()
  },
  {
    name: 'Beta值',
    current: 1.05,
    threshold: 1.5,
    status: 'normal',
    trend: 'up',
    type: 'number',
    history: generateRandomHistory()
  },
  {
    name: '夏普比率',
    current: 1.42,
    threshold: 1.0,
    status: 'good',
    trend: 'up',
    type: 'number',
    history: generateRandomHistory()
  }
])

// 风险分布数据
const riskDistributionData = ref([
  { name: '市场风险', value: 65 },
  { name: '信用风险', value: 15 },
  { name: '流动性风险', value: 12 },
  { name: '操作风险', value: 8 }
])

// 风险限额
const riskLimits = ref([
  {
    name: '总风险敞口',
    current: 2500000,
    total: 5000000,
    usage: 0.5,
    type: 'currency'
  },
  {
    name: '单一股票',
    current: 0.15,
    total: 0.20,
    usage: 0.75,
    type: 'percent'
  },
  {
    name: '行业集中度',
    current: 0.35,
    total: 0.40,
    usage: 0.875,
    type: 'percent'
  },
  {
    name: '杠杆使用',
    current: 1.8,
    total: 3.0,
    usage: 0.6,
    type: 'number'
  }
])

// 压力测试场景
const stressTestScenarios = ref([
  {
    name: '市场暴跌',
    description: '主要指数下跌20%',
    result: -0.18
  },
  {
    name: '利率上升',
    description: '基准利率上升200bp',
    result: -0.12
  },
  {
    name: '流动性紧缩',
    description: '市场流动性大幅收紧',
    result: -0.08
  },
  {
    name: '信用事件',
    description: '重大信用违约事件',
    result: -0.06
  }
])

// 风险配置
const riskConfig = ref({
  varConfidence: 95,
  maxDrawdownLimit: 0.15,
  leverageLimit: 3.0,
  concentrationLimit: 0.10,
  alertChannels: ['email', 'push']
})

// 方法
function generateRandomHistory() {
  const data = []
  for (let i = 30; i >= 0; i--) {
    data.push({
      date: Date.now() - i * 24 * 60 * 60 * 1000,
      value: Math.random() * 100
    })
  }
  return data
}

const refreshData = async () => {
  try {
    loading.value = true
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('风险数据刷新成功')
  } catch {
    ElMessage.error('风险数据刷新失败')
  } finally {
    loading.value = false
  }
}

const getRiskLevelClass = (level: number) => {
  switch (level) {
    case 1: return 'risk-low'
    case 2: return 'risk-medium'
    case 3: return 'risk-high'
    default: return 'risk-medium'
  }
}

const getRiskLevelText = (level: number) => {
  switch (level) {
    case 1: return '低风险'
    case 2: return '中等风险'
    case 3: return '高风险'
    default: return '中等风险'
  }
}

const getPriceClass = (value: number) => {
  if (value > 0) return 'price-up'
  if (value < 0) return 'price-down'
  return 'price-neutral'
}

const formatRiskValue = (value: number, type: string) => {
  switch (type) {
    case 'currency': return formatCurrency(value)
    case 'percent': return formatPercent(value)
    case 'number': return formatNumber(value, 2)
    default: return value.toString()
  }
}

const getRiskValueClass = (current: number, threshold: number) => {
  if (Math.abs(current) > Math.abs(threshold) * 0.9) return 'risk-high'
  if (Math.abs(current) > Math.abs(threshold) * 0.7) return 'risk-medium'
  return 'risk-low'
}

const getRiskStatusType = (status: string) => {
  switch (status) {
    case 'good': return 'success'
    case 'normal': return 'info'
    case 'warning': return 'warning'
    case 'danger': return 'danger'
    default: return 'info'
  }
}

const getRiskStatusText = (status: string) => {
  switch (status) {
    case 'good': return '良好'
    case 'normal': return '正常'
    case 'warning': return '预警'
    case 'danger': return '危险'
    default: return '正常'
  }
}

const getTrendClass = (trend: string) => {
  switch (trend) {
    case 'up': return 'trend-up'
    case 'down': return 'trend-down'
    case 'stable': return 'trend-stable'
    default: return 'trend-stable'
  }
}

const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'up': return ArrowUp
    case 'down': return ArrowDown
    case 'stable': return Minus
    default: return Minus
  }
}

const getLimitColor = (usage: number) => {
  if (usage > 0.9) return '#f56c6c'
  if (usage > 0.7) return '#e6a23c'
  return '#67c23a'
}

const toggleRiskChartType = () => {
  riskChartType.value = riskChartType.value === 'pie' ? 'bar' : 'pie'
}

const openRiskSettings = () => {
  riskSettingsVisible.value = true
}

const saveRiskSettings = async () => {
  try {
    // 模拟保存设置
    await new Promise(resolve => setTimeout(resolve, 500))
    ElMessage.success('风险设置保存成功')
    riskSettingsVisible.value = false
  } catch {
    ElMessage.error('风险设置保存失败')
  }
}

const exportRiskReport = async () => {
  try {
    ElMessage.success('风险报告导出成功')
  } catch {
    ElMessage.error('风险报告导出失败')
  }
}

const dismissAlert = (alertId: number) => {
  const index = riskAlerts.value.findIndex(alert => alert.id === alertId)
  if (index !== -1) {
    riskAlerts.value.splice(index, 1)
  }
}

const clearAlerts = async () => {
  try {
    await ElMessageBox.confirm('确定要清除所有风险预警吗？', '确认清除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    riskAlerts.value = []
    ElMessage.success('已清除所有预警')
  } catch {
    // 用户取消
  }
}

const viewAlertDetail = (alert: { title: string; [key: string]: unknown }) => {
  ElMessage.info(`查看预警详情: ${alert.title}`)
}

const handleAlert = (alert: { title: string; [key: string]: unknown }) => {
  ElMessage.info(`处理预警: ${alert.title}`)
}

const viewRiskDetail = (metric: { name: string; [key: string]: unknown }) => {
  ElMessage.info(`查看风险指标详情: ${metric.name}`)
}

const runStressTest = async () => {
  try {
    loading.value = true
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟更新压力测试结果
    stressTestScenarios.value.forEach(scenario => {
      scenario.result = (Math.random() - 0.5) * 0.3
    })
    
    ElMessage.success('压力测试完成')
  } catch {
    ElMessage.error('压力测试失败')
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(async () => {
  await refreshData()
})
</script>

<style scoped>
.risk-monitor-page {
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

.risk-dashboard {
  margin-bottom: 20px;
}

.risk-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #409EFF;
}

.risk-card.risk-low {
  border-left-color: #67c23a;
}

.risk-card.risk-medium {
  border-left-color: #e6a23c;
}

.risk-card.risk-high {
  border-left-color: #f56c6c;
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

.risk-icon {
  font-size: 20px;
  color: #409EFF;
}

.card-content .risk-level {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.card-content .risk-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.card-content .risk-score,
.card-content .risk-change,
.card-content .risk-limit {
  font-size: 12px;
  color: #666;
}

.risk-alerts {
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
  margin: 0;
  font-size: 16px;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.alerts-list {
  padding: 16px 20px;
}

.alert-item {
  margin-bottom: 12px;
}

.alert-item:last-child {
  margin-bottom: 0;
}

.alert-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-main {
  flex: 1;
}

.alert-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.alert-desc {
  font-size: 12px;
  color: #666;
}

.alert-actions {
  display: flex;
  gap: 8px;
}

.main-content {
  margin-bottom: 20px;
}

.risk-metrics-table {
  padding: 0;
}

.mini-chart {
  height: 40px;
  width: 100%;
}

.chart-container {
  padding: 20px;
}

.risk-limits {
  padding: 20px;
}

.limit-item {
  margin-bottom: 20px;
}

.limit-item:last-child {
  margin-bottom: 0;
}

.limit-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.limit-name {
  color: #333;
  font-weight: 500;
}

.limit-usage {
  color: #666;
}

.limit-bar {
  margin-bottom: 8px;
}

.limit-values {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

.stress-test-results {
  padding: 20px;
}

.scenario-item {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.scenario-item:last-child {
  margin-bottom: 0;
  border-bottom: none;
}

.scenario-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.scenario-name {
  font-weight: 500;
  color: #333;
}

.scenario-result {
  font-weight: 600;
}

.scenario-desc {
  font-size: 12px;
  color: #666;
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

.risk-high {
  color: #f56c6c;
}

.risk-medium {
  color: #e6a23c;
}

.risk-low {
  color: #67c23a;
}

.trend-up {
  color: #f56c6c;
}

.trend-down {
  color: #67c23a;
}

.trend-stable {
  color: #909399;
}

.risk-settings {
  padding: 20px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .risk-monitor-page {
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
  
  .risk-dashboard .el-col {
    margin-bottom: 16px;
  }
  
  .main-content .el-col {
    margin-bottom: 16px;
  }
  
  .alert-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .alert-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>