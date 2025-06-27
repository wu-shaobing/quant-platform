<template>
  <div class="dashboard-card" :class="`dashboard-card--${color}`">
    <div class="card-header">
      <div class="card-icon">
        <el-icon :size="24">
          <component :is="iconComponent" />
        </el-icon>
      </div>
      
      <div class="card-actions">
        <slot name="actions">
          <el-dropdown v-if="showMenu" @command="handleMenuCommand">
            <el-button text size="small" :icon="'MoreFilled'" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="detail">查看详情</el-dropdown-item>
                <el-dropdown-item command="refresh">刷新数据</el-dropdown-item>
                <el-dropdown-item command="export">导出数据</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </slot>
      </div>
    </div>
    
    <div class="card-content">
      <div class="card-title">{{ title }}</div>
      
      <div class="card-value">
        <span class="value-main">{{ value }}</span>
        <span v-if="unit" class="value-unit">{{ unit }}</span>
      </div>
      
      <div v-if="subValue" class="card-sub-value">
        {{ subValue }}
      </div>
      
      <div v-if="change !== undefined" class="card-change">
        <div class="change-value" :class="getChangeClass(change)">
          <el-icon size="14">
            <component :is="getChangeIcon(change)" />
          </el-icon>
          <span>{{ formatChange(change) }}</span>
        </div>
        
        <div v-if="changePercent !== undefined" class="change-percent" :class="getChangeClass(change)">
          ({{ formatPercent(changePercent) }})
        </div>
      </div>
      
      <!-- 趋势图 -->
      <div v-if="showTrend && trendData" class="card-trend">
        <div ref="trendChartRef" class="trend-chart"></div>
      </div>
      
      <!-- 进度条 -->
      <div v-if="showProgress && progressValue !== undefined" class="card-progress">
        <div class="progress-label">
          <span>{{ progressLabel || '进度' }}</span>
          <span>{{ formatPercent(progressValue) }}</span>
        </div>
        <el-progress 
          :percentage="progressValue" 
          :stroke-width="6"
          :color="getProgressColor(progressValue)"
          :show-text="false"
        />
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="card-loading">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { 
  TrendCharts, 
  Coin, 
  Money, 
  Grid, 
  ArrowUp, 
  ArrowDown, 
  Minus,
  MoreFilled,
  Loading
} from '@element-plus/icons-vue'
import { useChart } from '@/composables/chart/useChart'

interface Props {
  title: string
  value: string | number
  unit?: string
  subValue?: string
  change?: number
  changePercent?: number
  icon?: string
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  loading?: boolean
  showMenu?: boolean
  showTrend?: boolean
  trendData?: number[]
  showProgress?: boolean
  progressValue?: number
  progressLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  color: 'primary',
  loading: false,
  showMenu: false,
  showTrend: false,
  showProgress: false
})

const emit = defineEmits<{
  (e: 'menu-command', command: string): void
  (e: 'click'): void
}>()

// 图表引用
const trendChartRef = ref<HTMLElement>()

// 图表实例
const { chart: trendChart, initChart: initTrendChart, updateChart: updateTrendChart } = useChart(trendChartRef)

// 计算属性
const iconComponent = computed(() => {
  const iconMap: Record<string, any> = {
    TrendCharts,
    Coin,
    Money,
    Grid
  }
  
  return iconMap[props.icon || 'TrendCharts'] || TrendCharts
})

// 方法
const getChangeClass = (change: number) => {
  if (change > 0) return 'change-positive'
  if (change < 0) return 'change-negative'
  return 'change-neutral'
}

const getChangeIcon = (change: number) => {
  if (change > 0) return ArrowUp
  if (change < 0) return ArrowDown
  return Minus
}

const formatChange = (change: number) => {
  const prefix = change > 0 ? '+' : ''
  return `${prefix}${Math.abs(change).toLocaleString()}`
}

const formatPercent = (percent: number) => {
  const prefix = percent > 0 ? '+' : ''
  return `${prefix}${percent.toFixed(2)}%`
}

const getProgressColor = (value: number) => {
  if (value >= 80) return '#67c23a'
  if (value >= 60) return '#e6a23c'
  if (value >= 40) return '#f56c6c'
  return '#909399'
}

const handleMenuCommand = (command: string) => {
  emit('menu-command', command)
}

const handleClick = () => {
  emit('click')
}

// 初始化趋势图
const initializeTrendChart = async () => {
  if (!props.showTrend || !props.trendData || !trendChartRef.value) return
  
  await nextTick()
  await initTrendChart()
  
  const option = {
    grid: {
      left: 0,
      right: 0,
      top: 0,
      bottom: 0
    },
    xAxis: {
      type: 'category',
      show: false,
      data: props.trendData.map((_, index) => index)
    },
    yAxis: {
      type: 'value',
      show: false
    },
    series: [{
      type: 'line',
      data: props.trendData,
      smooth: true,
      symbol: 'none',
      lineStyle: {
        width: 2,
        color: props.change && props.change >= 0 ? '#67c23a' : '#f56c6c'
      },
      areaStyle: {
        opacity: 0.2,
        color: props.change && props.change >= 0 ? '#67c23a' : '#f56c6c'
      }
    }]
  }
  
  updateTrendChart(option)
}

onMounted(() => {
  if (props.showTrend) {
    initializeTrendChart()
  }
})
</script>

<style scoped>
.dashboard-card {
  position: relative;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;
  border: 1px solid transparent;
  overflow: hidden;
}

.dashboard-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.dashboard-card--primary {
  border-left: 4px solid #409eff;
}

.dashboard-card--primary .card-icon {
  background: linear-gradient(135deg, #409eff, #66b3ff);
  color: white;
}

.dashboard-card--success {
  border-left: 4px solid #67c23a;
}

.dashboard-card--success .card-icon {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  color: white;
}

.dashboard-card--warning {
  border-left: 4px solid #e6a23c;
}

.dashboard-card--warning .card-icon {
  background: linear-gradient(135deg, #e6a23c, #ebb563);
  color: white;
}

.dashboard-card--danger {
  border-left: 4px solid #f56c6c;
}

.dashboard-card--danger .card-icon {
  background: linear-gradient(135deg, #f56c6c, #f78989);
  color: white;
}

.dashboard-card--info {
  border-left: 4px solid #909399;
}

.dashboard-card--info .card-icon {
  background: linear-gradient(135deg, #909399, #a6a9ad);
  color: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  color: #909399;
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}

.card-value {
  display: flex;
  align-items: baseline;
  margin-bottom: 8px;
}

.value-main {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  font-family: 'JetBrains Mono', monospace;
}

.value-unit {
  font-size: 14px;
  color: #666;
  margin-left: 4px;
}

.card-sub-value {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
}

.card-change {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.change-value {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 600;
}

.change-percent {
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
}

.change-positive {
  color: #67c23a;
}

.change-negative {
  color: #f56c6c;
}

.change-neutral {
  color: #909399;
}

.card-trend {
  height: 60px;
  margin-top: 12px;
}

.trend-chart {
  width: 100%;
  height: 100%;
}

.card-progress {
  margin-top: 12px;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #666;
}

.card-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

@media (max-width: 768px) {
  .dashboard-card {
    padding: 16px;
  }
  
  .card-icon {
    width: 40px;
    height: 40px;
  }
  
  .value-main {
    font-size: 24px;
  }
  
  .card-change {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style> 