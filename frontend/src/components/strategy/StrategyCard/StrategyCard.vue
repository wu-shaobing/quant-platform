<template>
  <div 
    class="strategy-card"
    :class="[
      `strategy-card--${strategy.status}`,
      { 'strategy-card--selected': selected }
    ]"
  >
    <!-- 策略头部 -->
    <div class="strategy-header">
      <div class="strategy-info">
        <h3 class="strategy-name" :title="strategy.name">
          {{ strategy.name }}
        </h3>
        <div class="strategy-meta">
          <el-tag 
            :type="getStatusTagType(strategy.status)" 
            size="small"
          >
            {{ getStatusText(strategy.status) }}
          </el-tag>
          <span class="strategy-type">{{ strategy.type }}</span>
        </div>
      </div>
      
      <!-- 策略操作 -->
      <div class="strategy-actions">
        <el-dropdown @command="handleCommand">
          <el-button type="text" :icon="MoreFilled" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="start" :disabled="strategy.status === 'running'">
                <el-icon><VideoPlay /></el-icon>
                启动策略
              </el-dropdown-item>
              <el-dropdown-item command="stop" :disabled="strategy.status !== 'running'">
                <el-icon><VideoPause /></el-icon>
                停止策略
              </el-dropdown-item>
              <el-dropdown-item command="edit">
                <el-icon><Edit /></el-icon>
                编辑策略
              </el-dropdown-item>
              <el-dropdown-item command="clone">
                <el-icon><CopyDocument /></el-icon>
                克隆策略
              </el-dropdown-item>
              <el-dropdown-item command="delete" divided>
                <el-icon><Delete /></el-icon>
                删除策略
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 策略描述 -->
    <div v-if="strategy.description" class="strategy-description">
      {{ strategy.description }}
    </div>
    
    <!-- 绩效指标 -->
    <div class="strategy-performance">
      <div class="performance-grid">
        <div class="performance-item">
          <span class="performance-label">总收益率</span>
          <span 
            class="performance-value"
            :class="getPriceChangeClass(strategy.totalReturn)"
          >
            {{ formatPercent(strategy.totalReturn, 2, true) }}
          </span>
        </div>
        
        <div class="performance-item">
          <span class="performance-label">年化收益</span>
          <span 
            class="performance-value"
            :class="getPriceChangeClass(strategy.annualReturn)"
          >
            {{ formatPercent(strategy.annualReturn, 2, true) }}
          </span>
        </div>
        
        <div class="performance-item">
          <span class="performance-label">最大回撤</span>
          <span class="performance-value text-financial-down">
            {{ formatPercent(strategy.maxDrawdown, 2) }}
          </span>
        </div>
        
        <div class="performance-item">
          <span class="performance-label">夏普比率</span>
          <span class="performance-value">
            {{ formatRatio(strategy.sharpeRatio, 3) }}
          </span>
        </div>
        
        <div class="performance-item">
          <span class="performance-label">胜率</span>
          <span class="performance-value">
            {{ formatPercent(strategy.winRate, 1) }}
          </span>
        </div>
        
        <div class="performance-item">
          <span class="performance-label">运行天数</span>
          <span class="performance-value">
            {{ strategy.runningDays }}天
          </span>
        </div>
      </div>
    </div>
    
    <!-- 净值曲线图 -->
    <div v-if="showChart" class="strategy-chart">
      <div class="chart-header">
        <span class="chart-title">净值曲线</span>
        <div class="chart-controls">
          <el-button-group size="small">
            <el-button 
              v-for="period in chartPeriods"
              :key="period.value"
              :type="selectedPeriod === period.value ? 'primary' : 'default'"
              @click="changePeriod(period.value)"
            >
              {{ period.label }}
            </el-button>
          </el-button-group>
        </div>
      </div>
      
      <div class="chart-container">
        <AssetTrendChart 
          :data="chartData"
          :height="120"
          :show-grid="false"
          :show-tooltip="true"
        />
      </div>
    </div>
    
    <!-- 策略状态指示器 -->
    <div class="strategy-status">
      <div class="status-indicator">
        <div 
          class="status-dot"
          :class="`status-dot--${strategy.status}`"
        />
        <span class="status-text">
          {{ getDetailedStatusText(strategy.status) }}
        </span>
      </div>
      
      <div v-if="strategy.status === 'running'" class="running-info">
        <span class="running-time">
          运行时长: {{ formatRunningTime(strategy.startTime) }}
        </span>
      </div>
    </div>
    
    <!-- 风险提示 -->
    <div v-if="hasRiskWarning" class="strategy-warning">
      <el-alert
        :title="riskWarningText"
        type="warning"
        :closable="false"
        show-icon
        size="small"
      />
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="strategy-loading">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  MoreFilled, 
  VideoPlay, 
  VideoPause, 
  Edit, 
  CopyDocument, 
  Delete,
  Loading 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  formatPercent, 
  formatRatio, 
  getPriceChangeClass 
} from '@/utils/format/financial'
import type { Strategy, PerformanceData } from '@/types/strategy'
import AssetTrendChart from '@/components/charts/AssetTrendChart.vue'

interface Props {
  strategy: Strategy
  selected?: boolean
  showChart?: boolean
  loading?: boolean
}

interface Emits {
  (e: 'start', strategy: Strategy): void
  (e: 'stop', strategy: Strategy): void
  (e: 'edit', strategy: Strategy): void
  (e: 'clone', strategy: Strategy): void
  (e: 'delete', strategy: Strategy): void
  (e: 'click', strategy: Strategy): void
}

const props = withDefaults(defineProps<Props>(), {
  selected: false,
  showChart: true,
  loading: false
})

const emit = defineEmits<Emits>()

// 图表相关
const selectedPeriod = ref('1M')
const chartData = ref<PerformanceData[]>([])

const chartPeriods = [
  { label: '1周', value: '1W' },
  { label: '1月', value: '1M' },
  { label: '3月', value: '3M' },
  { label: '1年', value: '1Y' }
]

// 计算属性
const hasRiskWarning = computed(() => {
  return props.strategy.maxDrawdown < -0.2 || // 最大回撤超过20%
         props.strategy.sharpeRatio < 0.5 ||   // 夏普比率过低
         props.strategy.winRate < 0.3          // 胜率过低
})

const riskWarningText = computed(() => {
  const warnings = []
  
  if (props.strategy.maxDrawdown < -0.2) {
    warnings.push('最大回撤较大')
  }
  
  if (props.strategy.sharpeRatio < 0.5) {
    warnings.push('夏普比率偏低')
  }
  
  if (props.strategy.winRate < 0.3) {
    warnings.push('胜率较低')
  }
  
  return warnings.join('，') + '，请谨慎使用'
})

// 方法
const getStatusTagType = (status: string) => {
  const statusMap: Record<string, string> = {
    'running': 'success',
    'stopped': 'info',
    'error': 'danger',
    'paused': 'warning'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'running': '运行中',
    'stopped': '已停止',
    'error': '错误',
    'paused': '已暂停'
  }
  return statusMap[status] || '未知'
}

const getDetailedStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'running': '策略正在运行',
    'stopped': '策略已停止',
    'error': '策略运行出错',
    'paused': '策略已暂停'
  }
  return statusMap[status] || '状态未知'
}

const formatRunningTime = (startTime: string | Date) => {
  const start = new Date(startTime)
  const now = new Date()
  const diff = now.getTime() - start.getTime()
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  
  if (days > 0) {
    return `${days}天${hours}小时`
  } else if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else {
    return `${minutes}分钟`
  }
}

const handleCommand = async (command: string) => {
  switch (command) {
    case 'start':
      emit('start', props.strategy)
      break
      
    case 'stop':
      try {
        await ElMessageBox.confirm(
          '确定要停止该策略吗？',
          '停止策略',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        emit('stop', props.strategy)
      } catch {
        // 用户取消
      }
      break
      
    case 'edit':
      emit('edit', props.strategy)
      break
      
    case 'clone':
      emit('clone', props.strategy)
      ElMessage.success('策略克隆成功')
      break
      
    case 'delete':
      try {
        await ElMessageBox.confirm(
          '确定要删除该策略吗？此操作不可恢复。',
          '删除策略',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        emit('delete', props.strategy)
      } catch {
        // 用户取消
      }
      break
  }
}

const changePeriod = (period: string) => {
  selectedPeriod.value = period
  loadChartData()
}

const loadChartData = async () => {
  // 这里应该根据选择的时间周期加载图表数据
  // 暂时使用模拟数据
  const mockData: PerformanceData[] = []
  const startDate = new Date()
  startDate.setMonth(startDate.getMonth() - 1)
  
  for (let i = 0; i < 30; i++) {
    const date = new Date(startDate)
    date.setDate(date.getDate() + i)
    
    mockData.push({
      date: date.toISOString().split('T')[0],
      value: 1 + (Math.random() - 0.5) * 0.1 + i * 0.001,
      benchmark: 1 + (Math.random() - 0.5) * 0.05 + i * 0.0005
    })
  }
  
  chartData.value = mockData
}

onMounted(() => {
  if (props.showChart) {
    loadChartData()
  }
})
</script>

<style scoped lang="scss">
.strategy-card {
  @apply relative bg-white rounded-lg border border-gray-200 p-4 transition-all duration-200 hover:shadow-md;
  
  &--selected {
    @apply border-blue-500 shadow-md;
  }
  
  &--running {
    @apply border-l-4 border-l-green-500;
  }
  
  &--stopped {
    @apply border-l-4 border-l-gray-400;
  }
  
  &--error {
    @apply border-l-4 border-l-red-500;
  }
  
  &--paused {
    @apply border-l-4 border-l-yellow-500;
  }
}

.strategy-header {
  @apply flex items-start justify-between mb-3;
  
  .strategy-info {
    @apply flex-1 min-w-0;
    
    .strategy-name {
      @apply text-lg font-semibold text-gray-900 mb-2 truncate;
    }
    
    .strategy-meta {
      @apply flex items-center gap-2;
      
      .strategy-type {
        @apply text-sm text-gray-500;
      }
    }
  }
  
  .strategy-actions {
    @apply ml-2;
  }
}

.strategy-description {
  @apply text-sm text-gray-600 mb-4 line-clamp-2;
}

.strategy-performance {
  @apply mb-4;
  
  .performance-grid {
    @apply grid grid-cols-2 gap-3;
    
    .performance-item {
      @apply flex flex-col;
      
      .performance-label {
        @apply text-xs text-gray-500 mb-1;
      }
      
      .performance-value {
        @apply text-sm font-semibold;
      }
    }
  }
}

.strategy-chart {
  @apply mb-4;
  
  .chart-header {
    @apply flex items-center justify-between mb-2;
    
    .chart-title {
      @apply text-sm font-medium text-gray-700;
    }
    
    .chart-controls {
      .el-button-group {
        .el-button {
          @apply text-xs px-2 py-1;
        }
      }
    }
  }
  
  .chart-container {
    @apply bg-gray-50 rounded p-2;
  }
}

.strategy-status {
  @apply flex items-center justify-between text-sm;
  
  .status-indicator {
    @apply flex items-center gap-2;
    
    .status-dot {
      @apply w-2 h-2 rounded-full;
      
      &--running {
        @apply bg-green-500;
        animation: pulse 2s infinite;
      }
      
      &--stopped {
        @apply bg-gray-400;
      }
      
      &--error {
        @apply bg-red-500;
      }
      
      &--paused {
        @apply bg-yellow-500;
      }
    }
    
    .status-text {
      @apply text-gray-600;
    }
  }
  
  .running-info {
    .running-time {
      @apply text-xs text-gray-500;
    }
  }
}

.strategy-warning {
  @apply mt-3;
}

.strategy-loading {
  @apply absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 rounded-lg;
}

// 暗色主题适配
.dark .strategy-card {
  @apply bg-gray-800 border-gray-700;
  
  .strategy-header {
    .strategy-info {
      .strategy-name {
        @apply text-gray-100;
      }
      
      .strategy-meta {
        .strategy-type {
          @apply text-gray-400;
        }
      }
    }
  }
  
  .strategy-description {
    @apply text-gray-400;
  }
  
  .strategy-performance {
    .performance-grid {
      .performance-item {
        .performance-label {
          @apply text-gray-400;
        }
      }
    }
  }
  
  .strategy-chart {
    .chart-header {
      .chart-title {
        @apply text-gray-300;
      }
    }
    
    .chart-container {
      @apply bg-gray-700;
    }
  }
  
  .strategy-status {
    .status-indicator {
      .status-text {
        @apply text-gray-400;
      }
    }
    
    .running-info {
      .running-time {
        @apply text-gray-500;
      }
    }
  }
}

// 动画
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

// 响应式设计
@media (max-width: 640px) {
  .strategy-card {
    @apply p-3;
    
    .strategy-header {
      .strategy-info {
        .strategy-name {
          @apply text-base;
        }
      }
    }
    
    .strategy-performance {
      .performance-grid {
        @apply grid-cols-1 gap-2;
      }
    }
    
    .strategy-chart {
      .chart-header {
        @apply flex-col items-start gap-2;
      }
    }
  }
}

// 文本截断
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 