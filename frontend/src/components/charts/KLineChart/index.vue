<template>
  <div class="kline-chart">
    <div class="chart-header">
      <div class="chart-title">
        <h3>{{ symbol }} - {{ symbolName }}</h3>
        <span class="chart-subtitle">{{ currentPeriodLabel }}</span>
      </div>
      
      <div class="chart-toolbar">
        <!-- 时间周期选择 -->
        <el-button-group class="period-selector">
          <el-button
            v-for="period in timePeriods"
            :key="period.value"
            :type="selectedPeriod === period.value ? 'primary' : 'default'"
            size="small"
            @click="changePeriod(period.value)"
          >
            {{ period.label }}
          </el-button>
        </el-button-group>
        
        <!-- 指标选择 -->
        <el-dropdown @command="addIndicator">
          <el-button size="small">
            添加指标 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item 
                v-for="indicator in availableIndicators"
                :key="indicator.value"
                :command="indicator.value"
                :disabled="activeIndicators.includes(indicator.value)"
              >
                {{ indicator.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <!-- 全屏切换 -->
        <el-button 
          size="small" 
          :icon="fullscreen ? 'FullScreen' : 'FullScreen'" 
          @click="toggleFullscreen"
        />
      </div>
    </div>
    
    <div 
      ref="chartContainer" 
      class="chart-container"
      :class="{ 'fullscreen': fullscreen }"
    />
    
    <!-- 指标配置面板 -->
    <div v-if="showIndicatorPanel" class="indicator-panel">
      <div class="panel-header">
        <span>指标设置</span>
        <el-button text @click="showIndicatorPanel = false">
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      
      <div class="panel-content">
        <div 
          v-for="indicator in activeIndicators" 
          :key="indicator"
          class="indicator-item"
        >
          <div class="indicator-name">{{ getIndicatorLabel(indicator) }}</div>
          <div class="indicator-controls">
            <el-button 
              size="small" 
              text 
              type="danger"
              @click="removeIndicator(indicator)"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="KLineChart">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { ArrowDown, Close } from '@element-plus/icons-vue'
import { useChart } from '@/composables/chart/useChart'
import { useKLineData } from '@/composables/chart/useKLineData'
import { useIndicators } from '@/composables/chart/useIndicators'
import { useFullscreen } from '@/composables/core/useFullscreen'
import type { TimePeriod, KLineData, IndicatorType } from '@/types/chart'

interface Props {
  symbol: string
  symbolName?: string
  height?: string
  autoResize?: boolean
  showToolbar?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  symbolName: '',
  height: '400px',
  autoResize: true,
  showToolbar: true
})

const emit = defineEmits<{
  (e: 'period-change', period: TimePeriod): void
  (e: 'data-update', data: KLineData[]): void
  (e: 'indicator-add', indicator: IndicatorType): void
  (e: 'indicator-remove', indicator: IndicatorType): void
}>()

// 图表容器引用
const chartContainer = ref<HTMLElement>()

// 图表相关
const { 
  chart, 
  initChart, 
  updateChart, 
  showLoading, 
  hideLoading 
} = useChart(chartContainer)

// K线数据相关
const {
  klineData,
  selectedPeriod,
  timePeriods,
  currentPeriodLabel,
  fetchKLineData,
  subscribeRealtime,
  unsubscribeRealtime
} = useKLineData()

// 技术指标相关
const {
  availableIndicators,
  activeIndicators,
  addIndicator,
  removeIndicator,
  getIndicatorLabel
} = useIndicators()

// 全屏相关
const { isFullscreen, toggle: toggleFullscreen } = useFullscreen(chartContainer)
const fullscreen = computed(() => isFullscreen.value)

// UI状态
const showIndicatorPanel = ref(false)

// 计算属性
const chartOption = computed(() => {
  if (!klineData.value.length) return null

  const baseOption = {
    animation: false,
    grid: [
      {
        left: '10%',
        right: '8%',
        height: activeIndicators.value.length > 0 ? '50%' : '70%'
      },
      // 成交量网格
      {
        left: '10%',
        right: '8%',
        top: activeIndicators.value.length > 0 ? '65%' : '75%',
        height: '16%'
      }
    ],
    xAxis: [
      // 主图X轴
      {
        type: 'category',
        data: klineData.value.map(item => item.timestamp),
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: false },
        min: 'dataMin',
        max: 'dataMax',
        axisPointer: {
          z: 100
        }
      },
      // 成交量X轴
      {
        type: 'category',
        gridIndex: 1,
        data: klineData.value.map(item => item.timestamp),
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        min: 'dataMin',
        max: 'dataMax'
      }
    ],
    yAxis: [
      // 主图Y轴
      {
        scale: true,
        splitArea: { show: true }
      },
      // 成交量Y轴
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 70,
        end: 100
      },
      {
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        top: '90%',
        start: 70,
        end: 100
      }
    ],
    series: [
      // K线图
      {
        name: 'K线',
        type: 'candlestick',
        data: klineData.value.map(item => [item.open, item.close, item.low, item.high]),
        itemStyle: {
          color: '#ec0000',
          color0: '#00da3c',
          borderColor: '#8A0000',
          borderColor0: '#008F28'
        }
      },
      // 成交量
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: klineData.value.map(item => item.volume),
        itemStyle: {
          color: function(params: { dataIndex: number }) {
            const dataIndex = params.dataIndex
            const klineItem = klineData.value[dataIndex]
            return klineItem.close > klineItem.open ? '#ec0000' : '#00da3c'
          }
        }
      }
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      backgroundColor: 'rgba(245, 245, 245, 0.8)',
      borderWidth: 1,
      borderColor: '#ccc',
      padding: 10,
      textStyle: {
        color: '#000'
      },
      formatter: function (params: Array<{ axisValue: string; seriesName: string; data: number[] | number }>) {
        let result = `时间：${params[0].axisValue}<br/>`
        
        params.forEach((param) => {
          if (param.seriesName === 'K线') {
            const data = param.data
            result += `开盘：${data[1]}<br/>`
            result += `最高：${data[4]}<br/>`
            result += `最低：${data[3]}<br/>`
            result += `收盘：${data[2]}<br/>`
          } else if (param.seriesName === '成交量') {
            result += `成交量：${param.data}<br/>`
          }
        })
        
        return result
      }
    }
  }

  return baseOption
})

// 切换时间周期
const changePeriod = async (period: TimePeriod) => {
  if (period === selectedPeriod.value) return
  
  showLoading('加载K线数据...')
  
  try {
    await fetchKLineData(props.symbol, period)
    emit('period-change', period)
    emit('data-update', klineData.value)
  } catch (error) {
    console.error('切换周期失败:', error)
  } finally {
    hideLoading()
  }
}

// 初始化
onMounted(async () => {
  await nextTick()
  await initChart()
  
  // 加载初始数据
  showLoading('加载K线数据...')
  
  try {
    await fetchKLineData(props.symbol, selectedPeriod.value)
    subscribeRealtime(props.symbol)
  } catch (error) {
    console.error('初始化数据加载失败:', error)
  } finally {
    hideLoading()
  }
})

// 清理
onUnmounted(() => {
  unsubscribeRealtime(props.symbol)
})

// 监听数据变化更新图表
watch(
  chartOption,
  (newOption) => {
    if (newOption && chart.value) {
      updateChart(newOption)
    }
  },
  { deep: true }
)

// 监听符号变化
watch(
  () => props.symbol,
  async (newSymbol, oldSymbol) => {
    if (newSymbol !== oldSymbol) {
      unsubscribeRealtime(oldSymbol)
      
      showLoading('加载K线数据...')
      
      try {
        await fetchKLineData(newSymbol, selectedPeriod.value)
        subscribeRealtime(newSymbol)
        emit('data-update', klineData.value)
      } catch (error) {
        console.error('切换股票失败:', error)
      } finally {
        hideLoading()
      }
    }
  }
)
</script>

<style scoped>
.kline-chart {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.chart-title h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.chart-subtitle {
  font-size: 14px;
  color: #666;
  margin-left: 8px;
}

.chart-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.period-selector {
  display: flex;
}

.chart-container {
  flex: 1;
  min-height: 0;
  padding: 16px;
}

.chart-container.fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: white;
  padding: 20px;
}

.indicator-panel {
  position: absolute;
  top: 60px;
  right: 16px;
  width: 300px;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  font-weight: 600;
}

.panel-content {
  padding: 16px;
}

.indicator-item {
  margin-bottom: 16px;
}

.indicator-item:last-child {
  margin-bottom: 0;
}

.indicator-name {
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.indicator-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .chart-toolbar {
    width: 100%;
    justify-content: space-between;
  }
  
  .period-selector {
    flex-wrap: wrap;
  }
  
  .indicator-panel {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 90%;
    max-width: 400px;
  }
}
</style>