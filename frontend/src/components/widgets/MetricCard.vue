<template>
  <div class="metric-card" :class="cardClass">
    <div class="card-header">
      <div class="title-section">
        <h3 class="card-title">{{ title }}</h3>
        <p v-if="subtitle" class="card-subtitle">{{ subtitle }}</p>
      </div>
      
      <div v-if="icon" class="icon-section">
        <el-icon :size="iconSize" :color="iconColor">
          <component :is="icon" />
        </el-icon>
      </div>
    </div>
    
    <div class="card-content">
      <div class="metric-value">
        <span class="value" :class="valueClass">{{ formattedValue }}</span>
        <span v-if="unit" class="unit">{{ unit }}</span>
      </div>
      
      <div v-if="showChange && change !== undefined" class="metric-change">
        <el-icon :size="16" :class="changeClass">
          <component :is="changeIcon" />
        </el-icon>
        <span :class="changeClass">{{ formattedChange }}</span>
        <span v-if="changePercent !== undefined" :class="changeClass">
          ({{ formattedChangePercent }})
        </span>
      </div>
      
      <div v-if="description" class="metric-description">
        {{ description }}
      </div>
    </div>
    
    <div v-if="showChart && chartData" class="card-chart">
      <div class="mini-chart" ref="chartContainer">
        <!-- 这里可以集成 ECharts 或其他图表库 -->
        <svg width="100%" height="40" class="trend-chart">
          <polyline
            :points="chartPoints"
            fill="none"
            :stroke="trendColor"
            stroke-width="2"
          />
        </svg>
      </div>
    </div>
    
    <div v-if="actions && actions.length > 0" class="card-actions">
      <el-button
        v-for="action in actions"
        :key="action.key"
        :type="action.type || 'default'"
        :size="action.size || 'small'"
        :icon="action.icon"
        @click="handleAction(action)"
      >
        {{ action.label }}
      </el-button>
    </div>
    
    <div v-if="loading" class="card-loading">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  ArrowUp, 
  ArrowDown, 
  Minus, 
  Loading 
} from '@element-plus/icons-vue'
import { formatNumber, formatPercent, formatCurrency } from '@/utils/formatters'

interface Action {
  key: string
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  size?: 'large' | 'default' | 'small'
  icon?: Component
  handler?: () => void
}

interface Props {
  title: string
  subtitle?: string
  value: number | string
  unit?: string
  change?: number
  changePercent?: number
  showChange?: boolean
  description?: string
  icon?: Component
  iconSize?: number
  iconColor?: string
  type?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info'
  formatter?: 'number' | 'currency' | 'percent' | 'custom'
  precision?: number
  showChart?: boolean
  chartData?: number[]
  actions?: Action[]
  loading?: boolean
  clickable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showChange: true,
  iconSize: 24,
  type: 'default',
  formatter: 'number',
  precision: 2,
  showChart: false,
  loading: false,
  clickable: false
})

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'action', action: Action): void
}>()

const chartContainer = ref<HTMLElement>()

// 计算属性
const cardClass = computed(() => {
  return [
    `metric-card--${props.type}`,
    {
      'metric-card--clickable': props.clickable,
      'metric-card--loading': props.loading
    }
  ]
})

const formattedValue = computed(() => {
  if (typeof props.value === 'string') {
    return props.value
  }

  switch (props.formatter) {
    case 'currency':
      return formatCurrency(props.value, props.precision)
    case 'percent':
      return formatPercent(props.value, props.precision)
    case 'number':
      return formatNumber(props.value, props.precision)
    default:
      return props.value.toString()
  }
})

const valueClass = computed(() => {
  if (props.change === undefined) return ''
  
  if (props.change > 0) return 'value--positive'
  if (props.change < 0) return 'value--negative'
  return 'value--neutral'
})

const changeClass = computed(() => {
  if (props.change === undefined) return ''
  
  if (props.change > 0) return 'change--positive'
  if (props.change < 0) return 'change--negative'
  return 'change--neutral'
})

const changeIcon = computed(() => {
  if (props.change === undefined) return Minus
  
  if (props.change > 0) return ArrowUp
  if (props.change < 0) return ArrowDown
  return Minus
})

const formattedChange = computed(() => {
  if (props.change === undefined) return ''
  
  const prefix = props.change > 0 ? '+' : ''
  
  switch (props.formatter) {
    case 'currency':
      return prefix + formatCurrency(Math.abs(props.change), props.precision)
    case 'percent':
      return prefix + formatPercent(Math.abs(props.change), props.precision)
    case 'number':
      return prefix + formatNumber(Math.abs(props.change), props.precision)
    default:
      return prefix + Math.abs(props.change).toString()
  }
})

const formattedChangePercent = computed(() => {
  if (props.changePercent === undefined) return ''
  
  const prefix = props.changePercent > 0 ? '+' : ''
  return prefix + formatPercent(props.changePercent, 2)
})

const trendColor = computed(() => {
  if (!props.chartData || props.chartData.length < 2) return '#409eff'
  
  const first = props.chartData[0]
  const last = props.chartData[props.chartData.length - 1]
  
  if (last > first) return '#67c23a'
  if (last < first) return '#f56c6c'
  return '#909399'
})

const chartPoints = computed(() => {
  if (!props.chartData || props.chartData.length === 0) return ''
  
  const width = 200 // 假设图表宽度
  const height = 40
  const padding = 4
  
  const dataMin = Math.min(...props.chartData)
  const dataMax = Math.max(...props.chartData)
  const dataRange = dataMax - dataMin || 1
  
  const points = props.chartData.map((value, index) => {
    const x = (index / (props.chartData!.length - 1)) * (width - padding * 2) + padding
    const y = height - padding - ((value - dataMin) / dataRange) * (height - padding * 2)
    return `${x},${y}`
  })
  
  return points.join(' ')
})

// 方法
const handleAction = (action: Action) => {
  if (action.handler) {
    action.handler()
  }
  emit('action', action)
}

const _handleCardClick = () => {
  if (props.clickable && !props.loading) {
    emit('click')
  }
}

// 添加类型导入
import type { Component } from 'vue'
</script>

<style scoped>
.metric-card {
  position: relative;
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  overflow: hidden;
}

.metric-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.metric-card--clickable {
  cursor: pointer;
}

.metric-card--clickable:hover {
  transform: translateY(-2px);
}

.metric-card--loading {
  pointer-events: none;
}

.metric-card--primary {
  border-left: 4px solid #409eff;
}

.metric-card--success {
  border-left: 4px solid #67c23a;
}

.metric-card--warning {
  border-left: 4px solid #e6a23c;
}

.metric-card--danger {
  border-left: 4px solid #f56c6c;
}

.metric-card--info {
  border-left: 4px solid #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.title-section {
  flex: 1;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  line-height: 1.4;
}

.card-subtitle {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.icon-section {
  margin-left: 12px;
  opacity: 0.7;
}

.card-content {
  margin-bottom: 16px;
}

.metric-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  color: #333;
}

.value--positive {
  color: #67c23a;
}

.value--negative {
  color: #f56c6c;
}

.value--neutral {
  color: #909399;
}

.unit {
  font-size: 14px;
  color: #666;
  font-weight: normal;
}

.metric-change {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  margin-bottom: 8px;
}

.change--positive {
  color: #67c23a;
}

.change--negative {
  color: #f56c6c;
}

.change--neutral {
  color: #909399;
}

.metric-description {
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.card-chart {
  margin-bottom: 16px;
}

.mini-chart {
  height: 40px;
  overflow: hidden;
}

.trend-chart {
  width: 100%;
  height: 100%;
}

.card-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.card-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(2px);
}

@media (max-width: 768px) {
  .metric-card {
    padding: 16px;
  }
  
  .card-header {
    margin-bottom: 12px;
  }
  
  .card-title {
    font-size: 14px;
  }
  
  .value {
    font-size: 24px;
  }
  
  .card-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .metric-card {
    padding: 12px;
  }
  
  .value {
    font-size: 20px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 8px;
  }
  
  .icon-section {
    margin-left: 0;
  }
}
</style>