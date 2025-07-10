<!--
  风险趋势图表组件
  展示风险指标的时间序列变化
-->
<template>
  <div class="risk-trend-chart">
    <div class="chart-header">
      <h3 class="chart-title">{{ title }}</h3>
      
      <div class="chart-controls">
        <!-- 时间范围选择 -->
        <el-button-group class="time-range-selector">
          <el-button
            v-for="range in timeRanges"
            :key="range.value"
            :type="selectedTimeRange === range.value ? 'primary' : 'default'"
            size="small"
            @click="handleTimeRangeChange(range.value)"
          >
            {{ range.label }}
          </el-button>
        </el-button-group>
        
        <!-- 指标选择 -->
        <el-select
          v-model="selectedMetrics"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择风险指标"
          size="small"
          style="width: 200px"
          @change="handleMetricsChange"
        >
          <el-option
            v-for="metric in availableMetrics"
            :key="metric.value"
            :label="metric.label"
            :value="metric.value"
          />
        </el-select>
        
        <!-- 操作按钮 -->
        <el-button
          size="small"
          :icon="Refresh"
          @click="refreshData"
          :loading="loading"
        >
          刷新
        </el-button>
        
        <el-button
          size="small"
          :icon="Download"
          @click="exportChart"
        >
          导出
        </el-button>
      </div>
    </div>
    
    <div 
      ref="chartContainer"
      class="chart-container"
      :style="{ height: `${height}px` }"
    />
    
    <!-- 图例说明 -->
    <div class="chart-legend">
      <div class="legend-section">
        <span class="legend-title">风险等级:</span>
        <div class="legend-items">
          <div class="legend-item">
            <span class="legend-color low-risk"></span>
            <span>低风险 (< 5%)</span>
          </div>
          <div class="legend-item">
            <span class="legend-color medium-risk"></span>
            <span>中风险 (5% - 15%)</span>
          </div>
          <div class="legend-item">
            <span class="legend-color high-risk"></span>
            <span>高风险 (> 15%)</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 统计信息 -->
    <div v-if="showStats" class="chart-stats">
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">平均VaR:</span>
          <span class="stat-value">{{ formatPercent(stats.avgVar) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">最大回撤:</span>
          <span class="stat-value risk-high">{{ formatPercent(stats.maxDrawdown) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">波动率:</span>
          <span class="stat-value">{{ formatPercent(stats.volatility) }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">风险调整收益:</span>
          <span class="stat-value" :class="stats.sharpeRatio > 1 ? 'risk-low' : 'risk-medium'">
            {{ formatNumber(stats.sharpeRatio, 2) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { formatPercent, formatNumber, formatDate } from '@/utils/formatters'
import { useChart } from '@/composables/chart/useChart'

interface RiskTrendData {
  date: number
  var: number           // 风险价值
  volatility: number    // 波动率
  drawdown: number      // 回撤
  sharpeRatio: number   // 夏普比率
  beta: number          // 贝塔值
}

interface Props {
  title?: string
  height?: number
  data?: RiskTrendData[]
  loading?: boolean
  showStats?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: '风险趋势分析',
  height: 400,
  data: () => [],
  loading: false,
  showStats: true,
  autoRefresh: false,
  refreshInterval: 30000
})

const emit = defineEmits<{
  (e: 'time-range-change', range: string): void
  (e: 'metrics-change', metrics: string[]): void
  (e: 'refresh'): void
  (e: 'export'): void
}>()

// 图表容器
const chartContainer = ref<HTMLElement>()

// 图表实例
const { chart, initChart, updateChart, showLoading, hideLoading } = useChart(chartContainer)

// 状态管理
const selectedTimeRange = ref('1M')
const selectedMetrics = ref(['var', 'volatility', 'drawdown'])

// 时间范围选项
const timeRanges = [
  { label: '1周', value: '1W' },
  { label: '1月', value: '1M' },
  { label: '3月', value: '3M' },
  { label: '6月', value: '6M' },
  { label: '1年', value: '1Y' }
]

// 可用指标
const availableMetrics = [
  { label: '风险价值(VaR)', value: 'var' },
  { label: '波动率', value: 'volatility' },
  { label: '回撤', value: 'drawdown' },
  { label: '夏普比率', value: 'sharpeRatio' },
  { label: '贝塔值', value: 'beta' }
]

// 自动刷新定时器
let refreshTimer: NodeJS.Timeout | null = null

// 计算统计信息
const stats = computed(() => {
  if (!props.data.length) {
    return {
      avgVar: 0,
      maxDrawdown: 0,
      volatility: 0,
      sharpeRatio: 0
    }
  }

  const data = props.data
  const avgVar = data.reduce((sum, item) => sum + item.var, 0) / data.length
  const maxDrawdown = Math.max(...data.map(item => item.drawdown))
  const volatility = data.reduce((sum, item) => sum + item.volatility, 0) / data.length
  const sharpeRatio = data.reduce((sum, item) => sum + item.sharpeRatio, 0) / data.length

  return {
    avgVar,
    maxDrawdown,
    volatility,
    sharpeRatio
  }
})

// 图表配置
const chartOption = computed(() => {
  if (!props.data.length) return null

  const dates = props.data.map(item => formatDate(item.date, 'MM-DD'))
  
  // 构建系列数据
  const series: any[] = []
  
  selectedMetrics.value.forEach((metric, index) => {
    const colors = ['#ff4757', '#ffa502', '#2ed573', '#3742fa', '#5f27cd']
    const data = props.data.map(item => {
      const value = item[metric as keyof RiskTrendData] as number
      return metric === 'var' || metric === 'volatility' || metric === 'drawdown' 
        ? value * 100 // 转换为百分比
        : value
    })

    series.push({
      name: availableMetrics.find(m => m.value === metric)?.label || metric,
      type: 'line',
      data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: {
        width: 2,
        color: colors[index % colors.length]
      },
      itemStyle: {
        color: colors[index % colors.length]
      },
      areaStyle: metric === 'drawdown' ? {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(255, 71, 87, 0.3)' },
            { offset: 1, color: 'rgba(255, 71, 87, 0.1)' }
          ]
        }
      } : undefined
    })
  })

  return {
    title: {
      show: false
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      },
      formatter: (params: any[]) => {
        let result = `<div style="margin-bottom: 8px; font-weight: bold;">${params[0].axisValue}</div>`
        
        params.forEach(param => {
          const value = param.value
          const unit = ['var', 'volatility', 'drawdown'].includes(
            availableMetrics.find(m => m.label === param.seriesName)?.value || ''
          ) ? '%' : ''
          
          result += `
            <div style="margin: 4px 0;">
              ${param.marker} ${param.seriesName}: 
              <span style="font-weight: bold; color: ${param.color};">
                ${formatNumber(value, 2)}${unit}
              </span>
            </div>
          `
        })
        
        return result
      }
    },
    legend: {
      top: 0,
      right: 0,
      orient: 'horizontal',
      data: series.map(s => s.name)
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '8%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates,
      axisLine: {
        lineStyle: {
          color: '#e8e8e8'
        }
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: '#666',
        fontSize: 12
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '百分比 (%)',
        nameTextStyle: {
          color: '#666',
          fontSize: 12
        },
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: '#666',
          fontSize: 12,
          formatter: (value: number) => `${value}%`
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0',
            type: 'dashed'
          }
        }
      }
    ],
    series,
    dataZoom: [
      {
        type: 'inside',
        start: 70,
        end: 100
      },
      {
        type: 'slider',
        show: true,
        start: 70,
        end: 100,
        height: 20,
        bottom: 20
      }
    ]
  }
})

// 处理时间范围变化
const handleTimeRangeChange = (range: string) => {
  selectedTimeRange.value = range
  emit('time-range-change', range)
}

// 处理指标变化
const handleMetricsChange = (metrics: string[]) => {
  if (metrics.length === 0) {
    ElMessage.warning('至少选择一个风险指标')
    selectedMetrics.value = ['var']
    return
  }
  emit('metrics-change', metrics)
}

// 刷新数据
const refreshData = () => {
  emit('refresh')
}

// 导出图表
const exportChart = () => {
  if (!chart.value) return
  
  try {
    const dataURL = chart.value.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff'
    })
    
    const link = document.createElement('a')
    link.download = `risk-trend-${Date.now()}.png`
    link.href = dataURL
    link.click()
    
    ElMessage.success('图表导出成功')
  } catch (error) {
    ElMessage.error('图表导出失败')
  }
  
  emit('export')
}

// 启动自动刷新
const startAutoRefresh = () => {
  if (props.autoRefresh && props.refreshInterval > 0) {
    refreshTimer = setInterval(() => {
      refreshData()
    }, props.refreshInterval)
  }
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 初始化图表
onMounted(async () => {
  await nextTick()
  await initChart()
  startAutoRefresh()
})

// 清理
onUnmounted(() => {
  stopAutoRefresh()
})

// 监听数据变化
watch(
  [() => props.data, chartOption],
  () => {
    if (chartOption.value && chart.value) {
      updateChart(chartOption.value)
    }
  },
  { deep: true, immediate: true }
)

// 监听加载状态
watch(
  () => props.loading,
  (loading) => {
    if (loading) {
      showLoading('加载风险数据...')
    } else {
      hideLoading()
    }
  }
)

// 监听自动刷新配置变化
watch(
  [() => props.autoRefresh, () => props.refreshInterval],
  () => {
    stopAutoRefresh()
    startAutoRefresh()
  }
)
</script>

<style scoped>
.risk-trend-chart {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 16px;
}

.chart-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.chart-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.time-range-selector {
  display: flex;
}

.chart-container {
  width: 100%;
  min-height: 300px;
}

.chart-legend {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;
}

.legend-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.legend-title {
  font-weight: 500;
  color: #666;
}

.legend-items {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-color.low-risk {
  background: #52c41a;
}

.legend-color.medium-risk {
  background: #faad14;
}

.legend-color.high-risk {
  background: #ff4d4f;
}

.chart-stats {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.stat-value {
  font-weight: 600;
  font-size: 14px;
}

.stat-value.risk-low {
  color: #52c41a;
}

.stat-value.risk-medium {
  color: #faad14;
}

.stat-value.risk-high {
  color: #ff4d4f;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .risk-trend-chart {
    padding: 16px;
  }
  
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .chart-controls {
    width: 100%;
    justify-content: space-between;
  }
  
  .time-range-selector {
    flex-wrap: wrap;
  }
  
  .legend-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style> 