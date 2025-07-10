<template>
  <div class="strategy-monitor">
    <!-- 监控概览 -->
    <div class="monitor-overview">
      <el-row :gutter="24">
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-value">{{ runningStrategies }}</div>
              <div class="metric-label">运行中策略</div>
            </div>
            <el-icon class="metric-icon running"><VideoPlay /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-value">{{ totalPnl >= 0 ? '+' : '' }}{{ formatNumber(totalPnl) }}</div>
              <div class="metric-label">总盈亏</div>
            </div>
            <el-icon class="metric-icon" :class="totalPnl >= 0 ? 'profit' : 'loss'">
              <TrendCharts />
            </el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-value">{{ formatPercent(winRate) }}</div>
              <div class="metric-label">胜率</div>
            </div>
            <el-icon class="metric-icon success"><Trophy /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="metric-card">
            <div class="metric-content">
              <div class="metric-value">{{ alertCount }}</div>
              <div class="metric-label">告警数量</div>
            </div>
            <el-icon class="metric-icon warning"><Warning /></el-icon>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 策略列表 -->
    <el-card class="strategy-list-card" header="策略监控">
      <template #header>
        <div class="card-header">
          <span>策略监控</span>
          <div class="header-actions">
            <el-button-group>
              <el-button 
                :type="statusFilter === 'all' ? 'primary' : 'default'"
                @click="statusFilter = 'all'"
              >
                全部
              </el-button>
              <el-button 
                :type="statusFilter === 'running' ? 'primary' : 'default'"
                @click="statusFilter = 'running'"
              >
                运行中
              </el-button>
              <el-button 
                :type="statusFilter === 'stopped' ? 'primary' : 'default'"
                @click="statusFilter = 'stopped'"
              >
                已停止
              </el-button>
              <el-button 
                :type="statusFilter === 'error' ? 'primary' : 'default'"
                @click="statusFilter = 'error'"
              >
                异常
              </el-button>
            </el-button-group>
            <el-button type="primary" @click="refreshData" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredStrategies" v-loading="loading">
        <el-table-column prop="name" label="策略名称" min-width="150">
          <template #default="{ row }">
            <div class="strategy-name">
              <span>{{ row.name }}</span>
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="symbol" label="交易品种" width="120" />
        
        <el-table-column prop="pnl" label="盈亏" width="120" align="right">
          <template #default="{ row }">
            <span :class="row.pnl >= 0 ? 'profit' : 'loss'">
              {{ row.pnl >= 0 ? '+' : '' }}{{ formatNumber(row.pnl) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="pnlPercent" label="盈亏率" width="100" align="right">
          <template #default="{ row }">
            <span :class="row.pnlPercent >= 0 ? 'profit' : 'loss'">
              {{ row.pnlPercent >= 0 ? '+' : '' }}{{ formatPercent(row.pnlPercent) }}
            </span>
          </template>
        </el-table-column>
        
        <el-table-column prop="trades" label="交易次数" width="100" align="right" />
        
        <el-table-column prop="winRate" label="胜率" width="100" align="right">
          <template #default="{ row }">
            {{ formatPercent(row.winRate) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="runTime" label="运行时间" width="120">
          <template #default="{ row }">
            {{ formatDuration(row.runTime) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button 
                v-if="row.status === 'stopped'"
                type="success" 
                size="small"
                @click="startStrategy(row)"
              >
                启动
              </el-button>
              <el-button 
                v-if="row.status === 'running'"
                type="warning" 
                size="small"
                @click="stopStrategy(row)"
              >
                停止
              </el-button>
              <el-button 
                type="primary" 
                size="small"
                @click="viewDetails(row)"
              >
                详情
              </el-button>
              <el-button 
                type="info" 
                size="small"
                @click="viewLogs(row)"
              >
                日志
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 策略详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="策略详情"
      width="80%"
      :before-close="closeDetailDialog"
    >
      <div v-if="selectedStrategy" class="strategy-detail">
        <!-- 基本信息 -->
        <el-descriptions title="基本信息" :column="2" border>
          <el-descriptions-item label="策略名称">{{ selectedStrategy.name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedStrategy.status)">
              {{ getStatusText(selectedStrategy.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="交易品种">{{ selectedStrategy.symbol }}</el-descriptions-item>
          <el-descriptions-item label="运行时间">{{ formatDuration(selectedStrategy.runTime) }}</el-descriptions-item>
          <el-descriptions-item label="总盈亏">
            <span :class="selectedStrategy.pnl >= 0 ? 'profit' : 'loss'">
              {{ selectedStrategy.pnl >= 0 ? '+' : '' }}{{ formatNumber(selectedStrategy.pnl) }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="盈亏率">
            <span :class="selectedStrategy.pnlPercent >= 0 ? 'profit' : 'loss'">
              {{ selectedStrategy.pnlPercent >= 0 ? '+' : '' }}{{ formatPercent(selectedStrategy.pnlPercent) }}
            </span>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 性能指标 -->
        <el-descriptions title="性能指标" :column="3" border style="margin-top: 20px;">
          <el-descriptions-item label="交易次数">{{ selectedStrategy.trades }}</el-descriptions-item>
          <el-descriptions-item label="胜率">{{ formatPercent(selectedStrategy.winRate) }}</el-descriptions-item>
          <el-descriptions-item label="最大回撤">{{ formatPercent(selectedStrategy.maxDrawdown) }}</el-descriptions-item>
          <el-descriptions-item label="夏普比率">{{ selectedStrategy.sharpeRatio.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="盈亏比">{{ selectedStrategy.profitLossRatio.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="年化收益">{{ formatPercent(selectedStrategy.annualReturn) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 实时图表 -->
        <div class="chart-container" style="margin-top: 20px;">
          <h4>收益曲线</h4>
          <div ref="chartRef" style="height: 300px;"></div>
        </div>
      </div>
    </el-dialog>

    <!-- 日志对话框 -->
    <el-dialog
      v-model="logDialogVisible"
      title="策略日志"
      width="70%"
      :before-close="closeLogDialog"
    >
      <div class="log-container">
        <div class="log-header">
          <el-button-group>
            <el-button 
              :type="logLevel === 'all' ? 'primary' : 'default'"
              size="small"
              @click="logLevel = 'all'"
            >
              全部
            </el-button>
            <el-button 
              :type="logLevel === 'info' ? 'primary' : 'default'"
              size="small"
              @click="logLevel = 'info'"
            >
              信息
            </el-button>
            <el-button 
              :type="logLevel === 'warning' ? 'primary' : 'default'"
              size="small"
              @click="logLevel = 'warning'"
            >
              警告
            </el-button>
            <el-button 
              :type="logLevel === 'error' ? 'primary' : 'default'"
              size="small"
              @click="logLevel = 'error'"
            >
              错误
            </el-button>
          </el-button-group>
          <el-button size="small" @click="refreshLogs">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        <div class="log-content">
          <div 
            v-for="log in filteredLogs" 
            :key="log.id"
            class="log-item"
            :class="log.level"
          >
            <span class="log-time">{{ formatTime(log.timestamp) }}</span>
            <span class="log-level">{{ log.level.toUpperCase() }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  VideoPlay, 
  TrendCharts, 
  Trophy, 
  Warning, 
  Refresh 
} from '@element-plus/icons-vue'

// 状态数据
const loading = ref(false)
const statusFilter = ref('all')
const detailDialogVisible = ref(false)
const logDialogVisible = ref(false)
const logLevel = ref('all')
const selectedStrategy = ref(null)
const chartRef = ref()

// 模拟数据
const strategies = ref([
  {
    id: 1,
    name: '双均线策略',
    symbol: 'IF2312',
    status: 'running',
    pnl: 15680,
    pnlPercent: 12.5,
    trades: 45,
    winRate: 0.67,
    runTime: 7200000, // 2小时
    maxDrawdown: 0.08,
    sharpeRatio: 1.85,
    profitLossRatio: 2.1,
    annualReturn: 0.35
  },
  {
    id: 2,
    name: 'RSI反转策略',
    symbol: 'IC2312',
    status: 'running',
    pnl: -3250,
    pnlPercent: -5.2,
    trades: 23,
    winRate: 0.43,
    runTime: 5400000, // 1.5小时
    maxDrawdown: 0.12,
    sharpeRatio: 0.95,
    profitLossRatio: 1.3,
    annualReturn: -0.15
  },
  {
    id: 3,
    name: '网格交易策略',
    symbol: 'IH2312',
    status: 'stopped',
    pnl: 8920,
    pnlPercent: 7.8,
    trades: 78,
    winRate: 0.72,
    runTime: 0,
    maxDrawdown: 0.05,
    sharpeRatio: 2.15,
    profitLossRatio: 1.8,
    annualReturn: 0.28
  }
])

const logs = ref([
  {
    id: 1,
    strategyId: 1,
    timestamp: Date.now() - 300000,
    level: 'info',
    message: '策略启动成功'
  },
  {
    id: 2,
    strategyId: 1,
    timestamp: Date.now() - 240000,
    level: 'info',
    message: '开仓信号：买入 IF2312 @ 4250'
  },
  {
    id: 3,
    strategyId: 1,
    timestamp: Date.now() - 180000,
    level: 'warning',
    message: '持仓风险提醒：当前亏损超过5%'
  },
  {
    id: 4,
    strategyId: 1,
    timestamp: Date.now() - 120000,
    level: 'info',
    message: '平仓信号：卖出 IF2312 @ 4280'
  }
])

// 计算属性
const runningStrategies = computed(() => {
  return strategies.value.filter(s => s.status === 'running').length
})

const totalPnl = computed(() => {
  return strategies.value.reduce((sum, s) => sum + s.pnl, 0)
})

const winRate = computed(() => {
  const totalTrades = strategies.value.reduce((sum, s) => sum + s.trades, 0)
  const totalWins = strategies.value.reduce((sum, s) => sum + (s.trades * s.winRate), 0)
  return totalTrades > 0 ? totalWins / totalTrades : 0
})

const alertCount = computed(() => {
  return logs.value.filter(log => log.level === 'warning' || log.level === 'error').length
})

const filteredStrategies = computed(() => {
  if (statusFilter.value === 'all') {
    return strategies.value
  }
  return strategies.value.filter(s => s.status === statusFilter.value)
})

const filteredLogs = computed(() => {
  let filtered = logs.value
  if (selectedStrategy.value) {
    filtered = filtered.filter(log => log.strategyId === selectedStrategy.value.id)
  }
  if (logLevel.value !== 'all') {
    filtered = filtered.filter(log => log.level === logLevel.value)
  }
  return filtered.sort((a, b) => b.timestamp - a.timestamp)
})

// 方法
const formatNumber = (value: number): string => {
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatPercent = (value: number): string => {
  return (value * 100).toFixed(2) + '%'
}

const formatDuration = (ms: number): string => {
  if (ms === 0) return '未运行'
  const hours = Math.floor(ms / 3600000)
  const minutes = Math.floor((ms % 3600000) / 60000)
  return `${hours}小时${minutes}分钟`
}

const formatTime = (timestamp: number): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

const getStatusType = (status: string): string => {
  const types = {
    running: 'success',
    stopped: 'info',
    error: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string): string => {
  const texts = {
    running: '运行中',
    stopped: '已停止',
    error: '异常'
  }
  return texts[status] || status
}

const refreshData = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('数据刷新成功')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const startStrategy = async (strategy: any) => {
  try {
    await ElMessageBox.confirm(`确定要启动策略"${strategy.name}"吗？`, '确认启动', {
      type: 'warning'
    })
    
    strategy.status = 'running'
    ElMessage.success('策略启动成功')
  } catch {
    // 用户取消
  }
}

const stopStrategy = async (strategy: any) => {
  try {
    await ElMessageBox.confirm(`确定要停止策略"${strategy.name}"吗？`, '确认停止', {
      type: 'warning'
    })
    
    strategy.status = 'stopped'
    strategy.runTime = 0
    ElMessage.success('策略停止成功')
  } catch {
    // 用户取消
  }
}

const viewDetails = (strategy: any) => {
  selectedStrategy.value = strategy
  detailDialogVisible.value = true
}

const viewLogs = (strategy: any) => {
  selectedStrategy.value = strategy
  logDialogVisible.value = true
}

const closeDetailDialog = () => {
  detailDialogVisible.value = false
  selectedStrategy.value = null
}

const closeLogDialog = () => {
  logDialogVisible.value = false
  selectedStrategy.value = null
}

const refreshLogs = async () => {
  // 模拟刷新日志
  ElMessage.success('日志刷新成功')
}

// 生命周期
onMounted(() => {
  refreshData()
})

onUnmounted(() => {
  // 清理资源
})
</script>

<style scoped>
.strategy-monitor {
  padding: 20px;
}

.monitor-overview {
  margin-bottom: 24px;
}

.metric-card {
  position: relative;
  overflow: hidden;
}

.metric-card .el-card__body {
  padding: 20px;
}

.metric-content {
  position: relative;
  z-index: 2;
}

.metric-value {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 8px;
}

.metric-label {
  font-size: 14px;
  color: #666;
}

.metric-icon {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 40px;
  opacity: 0.1;
}

.metric-icon.running {
  color: #67c23a;
}

.metric-icon.profit {
  color: #f56c6c;
}

.metric-icon.loss {
  color: #e6a23c;
}

.metric-icon.success {
  color: #409eff;
}

.metric-icon.warning {
  color: #e6a23c;
}

.strategy-list-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.strategy-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profit {
  color: #f56c6c;
}

.loss {
  color: #67c23a;
}

.strategy-detail .el-descriptions {
  margin-bottom: 20px;
}

.chart-container h4 {
  margin-bottom: 16px;
  color: #333;
}

.log-container {
  height: 400px;
  display: flex;
  flex-direction: column;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.log-content {
  flex: 1;
  overflow-y: auto;
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #666;
  font-size: 12px;
  min-width: 120px;
}

.log-level {
  font-weight: bold;
  min-width: 60px;
  text-align: center;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}

.log-item.info .log-level {
  background: #e1f3ff;
  color: #409eff;
}

.log-item.warning .log-level {
  background: #fdf6ec;
  color: #e6a23c;
}

.log-item.error .log-level {
  background: #fef0f0;
  color: #f56c6c;
}

.log-message {
  flex: 1;
  font-size: 14px;
}
</style> 