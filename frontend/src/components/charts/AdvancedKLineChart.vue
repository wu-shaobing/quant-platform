<template>
  <div class="advanced-kline-chart">
    <!-- 工具栏 -->
    <div class="chart-toolbar">
      <div class="toolbar-left">
        <!-- 时间周期 -->
        <el-button-group class="period-group">
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

        <!-- 图表类型 -->
        <el-dropdown @command="changeChartType">
          <el-button size="small">
            {{ chartTypeLabel }} <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="candle">蜡烛图</el-dropdown-item>
              <el-dropdown-item command="line">线图</el-dropdown-item>
              <el-dropdown-item command="bar">柱状图</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div class="toolbar-center">
        <!-- 绘图工具 -->
        <el-button-group class="drawing-tools">
          <el-button
            v-for="tool in drawingTools"
            :key="tool.id"
            :type="currentTool?.id === tool.id ? 'primary' : 'default'"
            size="small"
            @click="selectTool(tool)"
          >
            <el-icon><component :is="tool.icon" /></el-icon>
          </el-button>
        </el-button-group>

        <!-- 操作按钮 -->
        <el-button-group class="action-buttons">
          <el-button
            size="small"
            :disabled="!canUndo"
            @click="undo"
            title="撤销 (Ctrl+Z)"
          >
            <el-icon><RefreshLeft /></el-icon>
          </el-button>
          <el-button
            size="small"
            :disabled="!canRedo"
            @click="redo"
            title="重做 (Ctrl+Y)"
          >
            <el-icon><RefreshRight /></el-icon>
          </el-button>
          <el-button
            size="small"
            :disabled="!hasSelection"
            @click="deleteSelectedElements"
            title="删除 (Delete)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </el-button-group>
      </div>

      <div class="toolbar-right">
        <!-- 技术指标 -->
        <el-dropdown @command="addIndicator">
          <el-button size="small">
            指标 <el-icon><ArrowDown /></el-icon>
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

        <!-- 设置 -->
        <el-button size="small" @click="showSettings = true">
          <el-icon><Setting /></el-icon>
        </el-button>

        <!-- 全屏 -->
        <el-button size="small" @click="toggleFullscreen">
          <el-icon><FullScreen /></el-icon>
        </el-button>

        <!-- 导出 -->
        <el-dropdown @command="exportChart">
          <el-button size="small">
            <el-icon><Download /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="png">导出PNG</el-dropdown-item>
              <el-dropdown-item command="jpeg">导出JPEG</el-dropdown-item>
              <el-dropdown-item command="svg">导出SVG</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主图表区域 -->
    <div
      ref="chartContainer"
      class="chart-container"
      :class="{ 'fullscreen': isFullscreen }"
    />

    <!-- 指标面板 -->
    <div v-if="activeIndicators.length > 0" class="indicators-panel">
      <div
        v-for="(indicator, index) in activeIndicators"
        :key="indicator"
        class="indicator-item"
      >
        <span class="indicator-name">{{ getIndicatorLabel(indicator) }}</span>
        <el-button
          size="small"
          text
          type="danger"
          @click="removeIndicator(indicator)"
        >
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 价格提醒面板 -->
    <div v-if="alertLevels.length > 0" class="alerts-panel">
      <div class="panel-header">
        <span>价格提醒</span>
      </div>
      <div class="alert-list">
        <div
          v-for="alert in alertLevels"
          :key="alert.id"
          class="alert-item"
          :class="{ 'triggered': alert.triggered }"
        >
          <span class="alert-price">{{ alert.price }}</span>
          <span class="alert-type">{{ alert.type }}</span>
          <el-button
            size="small"
            text
            type="danger"
            @click="removeAlertLevel(alert.id)"
          >
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 设置对话框 -->
    <el-dialog v-model="showSettings" title="图表设置" width="600px">
      <div class="settings-content">
        <!-- 主题设置 -->
        <div class="setting-group">
          <h4>主题</h4>
          <el-radio-group v-model="chartSettings.theme">
            <el-radio label="light">浅色</el-radio>
            <el-radio label="dark">深色</el-radio>
          </el-radio-group>
        </div>

        <!-- 图表设置 -->
        <div class="setting-group">
          <h4>图表显示</h4>
          <el-checkbox v-model="chartSettings.gridLines">网格线</el-checkbox>
          <el-checkbox v-model="chartSettings.crosshair">十字线</el-checkbox>
          <el-checkbox v-model="chartSettings.priceLabels">价格标签</el-checkbox>
          <el-checkbox v-model="chartSettings.volumeChart">成交量图</el-checkbox>
        </div>

        <!-- 颜色设置 -->
        <div class="setting-group">
          <h4>颜色配置</h4>
          <div class="color-settings">
            <div class="color-item">
              <label>上涨色:</label>
              <el-color-picker v-model="chartSettings.colors.up" />
            </div>
            <div class="color-item">
              <label>下跌色:</label>
              <el-color-picker v-model="chartSettings.colors.down" />
            </div>
            <div class="color-item">
              <label>背景色:</label>
              <el-color-picker v-model="chartSettings.colors.background" />
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="applySettings">应用</el-button>
      </template>
    </el-dialog>

    <!-- 添加提醒对话框 -->
    <el-dialog v-model="showAddAlert" title="添加价格提醒" width="400px">
      <el-form :model="alertForm" label-width="80px">
        <el-form-item label="价格">
          <el-input-number
            v-model="alertForm.price"
            :precision="2"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="alertForm.type" style="width: 100%">
            <el-option label="支撑位" value="support" />
            <el-option label="阻力位" value="resistance" />
            <el-option label="目标价" value="target" />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="alertForm.message" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddAlert = false">取消</el-button>
        <el-button type="primary" @click="addAlert">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts" name="AdvancedKLineChart">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import {
  ArrowDown, Close, Setting, FullScreen, Download,
  RefreshLeft, RefreshRight, Delete
} from '@element-plus/icons-vue'
import { useAdvancedChart } from '@/composables/chart/useAdvancedChart'
import { useKLineData } from '@/composables/chart/useKLineData'
import { useIndicators } from '@/composables/chart/useIndicators'
import { useFullscreen } from '@/composables/core/useFullscreen'
import { useNotification } from '@/composables/useNotification'
import {
  calculateSMA,
  calculateEMA,
  calculateMACD,
  calculateRSI,
  calculateBollingerBands,
  calculateKDJ,
  type KLinePoint
} from '@/utils/indicators/technical'

interface Props {
  symbol: string
  symbolName?: string
  height?: string
  autoResize?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  symbolName: '',
  height: '600px',
  autoResize: true
})

const emit = defineEmits<{
  (e: 'period-change', period: string): void
  (e: 'chart-type-change', type: string): void
  (e: 'indicator-add', indicator: string): void
  (e: 'indicator-remove', indicator: string): void
}>()

// 图表容器引用
const chartContainer = ref<HTMLElement>()

// 高级图表功能
const {
  chart,
  isInitialized,
  isLoading,
  currentTool,
  drawingTools,
  drawingElements,
  selectedElements,
  alertLevels,
  chartSettings,
  canUndo,
  canRedo,
  hasSelection,
  initChart,
  updateChart,
  selectTool,
  undo,
  redo,
  deleteSelectedElements,
  exportChart,
  addAlertLevel,
  removeAlertLevel,
  applyChartSettings
} = useAdvancedChart(chartContainer)

// K线数据
const {
  klineData,
  selectedPeriod,
  timePeriods,
  fetchKLineData,
  subscribeRealtime,
  unsubscribeRealtime
} = useKLineData()

// 技术指标
const {
  availableIndicators,
  activeIndicators,
  addIndicator,
  removeIndicator,
  getIndicatorLabel
} = useIndicators()

// 全屏功能
const { isFullscreen, toggle: toggleFullscreen } = useFullscreen(chartContainer)

// 通知功能
const { showNotification } = useNotification()

// UI状态
const showSettings = ref(false)
const showAddAlert = ref(false)
const chartType = ref<'candle' | 'line' | 'bar'>('candle')

// 表单数据
const alertForm = ref({
  price: 0,
  type: 'support' as 'support' | 'resistance' | 'target',
  message: ''
})

// 计算属性
const chartTypeLabel = computed(() => {
  const labels = {
    candle: '蜡烛图',
    line: '线图',
    bar: '柱状图'
  }
  return labels[chartType.value]
})

// 构建完整的图表配置
const buildCompleteChartOption = () => {
  if (!klineData.value.length) return null

  const baseOption = {
    animation: false,
    backgroundColor: chartSettings.value.colors.background,
    textStyle: {
      color: chartSettings.value.colors.text
    },
    grid: [
      // 主图
      {
        left: '8%',
        right: '8%',
        top: '10%',
        height: chartSettings.value.volumeChart ? '50%' : '70%'
      },
      // 成交量图
      ...(chartSettings.value.volumeChart ? [{
        left: '8%',
        right: '8%',
        top: '65%',
        height: '16%'
      }] : []),
      // 指标图
      ...activeIndicators.value.map((_, index) => ({
        left: '8%',
        right: '8%',
        top: `${85 + index * 15}%`,
        height: '12%'
      }))
    ],
    xAxis: [
      // 主图X轴
      {
        type: 'category',
        data: klineData.value.map(item => formatTime(item.timestamp)),
        scale: true,
        boundaryGap: false,
        axisLine: { onZero: false },
        splitLine: { show: chartSettings.value.gridLines },
        min: 'dataMin',
        max: 'dataMax'
      },
      // 其他图表的X轴
      ...Array(activeIndicators.value.length + (chartSettings.value.volumeChart ? 1 : 0))
        .fill(null)
        .map((_, index) => ({
          type: 'category',
          gridIndex: index + 1,
          data: klineData.value.map(item => formatTime(item.timestamp)),
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          min: 'dataMin',
          max: 'dataMax'
        }))
    ],
    yAxis: [
      // 主图Y轴
      {
        scale: true,
        splitArea: { show: chartSettings.value.gridLines },
        axisLabel: {
          inside: true,
          formatter: '{value}'
        }
      },
      // 其他图表的Y轴
      ...Array(activeIndicators.value.length + (chartSettings.value.volumeChart ? 1 : 0))
        .fill(null)
        .map((_, index) => ({
          scale: true,
          gridIndex: index + 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false }
        }))
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: 'all',
        start: 70,
        end: 100
      },
      {
        show: true,
        xAxisIndex: 'all',
        type: 'slider',
        bottom: '5%',
        start: 70,
        end: 100
      }
    ],
    series: buildSeriesConfig(),
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: chartSettings.value.crosshair ? 'cross' : 'line'
      },
      backgroundColor: 'rgba(245, 245, 245, 0.9)',
      borderWidth: 1,
      borderColor: '#ccc',
      textStyle: {
        color: '#000'
      },
      formatter: buildTooltipFormatter()
    }
  }

  return baseOption
}

// 构建系列配置
const buildSeriesConfig = () => {
  const series: any[] = []
  let seriesIndex = 0

  // 主图 - K线或线图
  if (chartType.value === 'candle') {
    series.push({
      name: 'K线',
      type: 'candlestick',
      data: klineData.value.map(item => [item.open, item.close, item.low, item.high]),
      itemStyle: {
        color: chartSettings.value.colors.up,
        color0: chartSettings.value.colors.down,
        borderColor: chartSettings.value.colors.up,
        borderColor0: chartSettings.value.colors.down
      }
    })
  } else if (chartType.value === 'line') {
    series.push({
      name: '收盘价',
      type: 'line',
      data: klineData.value.map(item => item.close),
      lineStyle: {
        color: chartSettings.value.colors.up
      }
    })
  }

  seriesIndex++

  // 成交量图
  if (chartSettings.value.volumeChart) {
    series.push({
      name: '成交量',
      type: 'bar',
      xAxisIndex: seriesIndex,
      yAxisIndex: seriesIndex,
      data: klineData.value.map(item => item.volume),
      itemStyle: {
        color: function(params: { dataIndex: number }) {
          const dataIndex = params.dataIndex
          const klineItem = klineData.value[dataIndex]
          return klineItem.close > klineItem.open ?
            chartSettings.value.colors.up :
            chartSettings.value.colors.down
        }
      }
    })
    seriesIndex++
  }

  // 技术指标
  for (const indicatorType of activeIndicators.value) {
    const indicatorSeries = buildIndicatorSeries(indicatorType, seriesIndex)
    series.push(...indicatorSeries)
    seriesIndex++
  }

  return series
}

// 构建指标系列
const buildIndicatorSeries = (indicatorType: string, seriesIndex: number) => {
  const klinePoints: KLinePoint[] = klineData.value.map(item => ({
    timestamp: item.timestamp,
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
    volume: item.volume
  }))

  switch (indicatorType) {
    case 'MA5':
      const ma5 = calculateSMA(klinePoints, 5)
      return [{
        name: 'MA5',
        type: 'line',
        data: ma5.data.map(d => d.value),
        lineStyle: { color: ma5.color }
      }]

    case 'MA10':
      const ma10 = calculateSMA(klinePoints, 10)
      return [{
        name: 'MA10',
        type: 'line',
        data: ma10.data.map(d => d.value),
        lineStyle: { color: ma10.color }
      }]

    case 'MA20':
      const ma20 = calculateSMA(klinePoints, 20)
      return [{
        name: 'MA20',
        type: 'line',
        data: ma20.data.map(d => d.value),
        lineStyle: { color: ma20.color }
      }]

    case 'MACD':
      const macd = calculateMACD(klinePoints)
      return [
        {
          name: 'DIF',
          type: 'line',
          xAxisIndex: seriesIndex,
          yAxisIndex: seriesIndex,
          data: macd.dif.data.map(d => d.value),
          lineStyle: { color: macd.dif.color }
        },
        {
          name: 'DEA',
          type: 'line',
          xAxisIndex: seriesIndex,
          yAxisIndex: seriesIndex,
          data: macd.dea.data.map(d => d.value),
          lineStyle: { color: macd.dea.color }
        },
        {
          name: 'MACD',
          type: 'bar',
          xAxisIndex: seriesIndex,
          yAxisIndex: seriesIndex,
          data: macd.macd.data.map(d => d.value),
          itemStyle: { color: macd.macd.color }
        }
      ]

    case 'RSI':
      const rsi = calculateRSI(klinePoints)
      return [{
        name: 'RSI',
        type: 'line',
        xAxisIndex: seriesIndex,
        yAxisIndex: seriesIndex,
        data: rsi.data.map(d => d.value),
        lineStyle: { color: rsi.color }
      }]

    case 'BOLL':
      const boll = calculateBollingerBands(klinePoints)
      return [
        {
          name: '布林上轨',
          type: 'line',
          data: boll.upper.data.map(d => d.value),
          lineStyle: { color: boll.upper.color }
        },
        {
          name: '布林中轨',
          type: 'line',
          data: boll.middle.data.map(d => d.value),
          lineStyle: { color: boll.middle.color }
        },
        {
          name: '布林下轨',
          type: 'line',
          data: boll.lower.data.map(d => d.value),
          lineStyle: { color: boll.lower.color }
        }
      ]

    case 'KDJ':
      const kdj = calculateKDJ(klinePoints)
      return [
        {
          name: 'K',
          type: 'line',
          xAxisIndex: seriesIndex,
          yAxisIndex: seriesIndex,
          data: kdj.k.data.map(d => d.value),
          lineStyle: { color: kdj.k.color }
        },
        {
          name: 'D',
          type: 'line',
          xAxisIndex: seriesIndex,
          yAxisIndex: seriesIndex,
          data: kdj.d.data.map(d => d.value),
          lineStyle: { color: kdj.d.color }
        },
        {
          name: 'J',
          type: 'line',
          xAxisIndex: seriesIndex,
          yAxisIndex: seriesIndex,
          data: kdj.j.data.map(d => d.value),
          lineStyle: { color: kdj.j.color }
        }
      ]

    default:
      return []
  }
}

// 构建提示框格式化器
const buildTooltipFormatter = () => {
  return function (params: any[]) {
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
      } else if (param.data !== null && param.data !== undefined) {
        result += `${param.seriesName}：${param.data.toFixed(2)}<br/>`
      }
    })

    return result
  }
}

// 格式化时间
const formatTime = (timestamp: number) => {
  const date = new Date(timestamp)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 切换时间周期
const changePeriod = async (period: string) => {
  try {
    await fetchKLineData(props.symbol, period)
    emit('period-change', period)
    updateChart()
  } catch (error) {
    showNotification('切换周期失败', 'error')
  }
}

// 切换图表类型
const changeChartType = (type: 'candle' | 'line' | 'bar') => {
  chartType.value = type
  emit('chart-type-change', type)
  updateChart()
}

// 添加指标
const handleAddIndicator = (indicator: string) => {
  addIndicator(indicator)
  emit('indicator-add', indicator)
  updateChart()
}

// 移除指标
const handleRemoveIndicator = (indicator: string) => {
  removeIndicator(indicator)
  emit('indicator-remove', indicator)
  updateChart()
}

// 应用设置
const applySettings = () => {
  applyChartSettings()
  showSettings.value = false
  updateChart()
}

// 添加价格提醒
const addAlert = () => {
  if (alertForm.value.price <= 0) {
    showNotification('请输入有效价格', 'warning')
    return
  }

  addAlertLevel(
    alertForm.value.price,
    alertForm.value.type,
    alertForm.value.message || `${alertForm.value.type}位 ${alertForm.value.price}`
  )

  showAddAlert.value = false
  alertForm.value = {
    price: 0,
    type: 'support',
    message: ''
  }

  showNotification('价格提醒添加成功', 'success')
}

// 监听数据变化
watch(
  () => klineData.value,
  () => {
    if (chart.value && klineData.value.length > 0) {
      const option = buildCompleteChartOption()
      if (option) {
        chart.value.setOption(option, true)
      }
    }
  },
  { deep: true }
)

// 监听图表设置变化
watch(
  () => chartSettings.value,
  () => {
    updateChart()
  },
  { deep: true }
)

// 初始化
onMounted(async () => {
  await nextTick()
  await initChart()

  try {
    await fetchKLineData(props.symbol, selectedPeriod.value)
    subscribeRealtime(props.symbol)
  } catch (error) {
    showNotification('数据加载失败', 'error')
  }
})

// 清理
onUnmounted(() => {
  unsubscribeRealtime(props.symbol)
})

// 监听符号变化
watch(
  () => props.symbol,
  async (newSymbol, oldSymbol) => {
    if (newSymbol !== oldSymbol) {
      unsubscribeRealtime(oldSymbol)

      try {
        await fetchKLineData(newSymbol, selectedPeriod.value)
        subscribeRealtime(newSymbol)
      } catch (error) {
        showNotification('切换股票失败', 'error')
      }
    }
  }
)

// 右键菜单 - 添加价格提醒
const handleContextMenu = (event: MouseEvent) => {
  event.preventDefault()

  if (!chart.value) return

  const point = chart.value.convertFromPixel('grid', [event.offsetX, event.offsetY])
  if (point && point[1]) {
    alertForm.value.price = Number(point[1].toFixed(2))
    showAddAlert.value = true
  }
}

// 绑定右键菜单
onMounted(() => {
  if (chartContainer.value) {
    chartContainer.value.addEventListener('contextmenu', handleContextMenu)
  }
})

onUnmounted(() => {
  if (chartContainer.value) {
    chartContainer.value.removeEventListener('contextmenu', handleContextMenu)
  }
})
</script>

<style scoped>
.advanced-kline-chart {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.toolbar-left,
.toolbar-center,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.period-group,
.drawing-tools,
.action-buttons {
  display: flex;
  gap: 4px;
}

.chart-container {
  flex: 1;
  min-height: 0;
  padding: 8px;
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

.indicators-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 16px;
  border-top: 1px solid #e8e8e8;
  background: #f9f9f9;
}

.indicator-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 12px;
}

.indicator-name {
  font-weight: 500;
  color: #333;
}

.alerts-panel {
  border-top: 1px solid #e8e8e8;
  background: #f9f9f9;
}

.panel-header {
  padding: 8px 16px;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #e8e8e8;
}

.alert-list {
  max-height: 120px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.alert-item.triggered {
  background: #fff3cd;
  color: #856404;
}

.alert-price {
  font-weight: 600;
}

.alert-type {
  font-size: 12px;
  color: #666;
}

.settings-content {
  max-height: 400px;
  overflow-y: auto;
}

.setting-group {
  margin-bottom: 24px;
}

.setting-group h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.color-settings {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.color-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.color-item label {
  font-size: 14px;
  color: #666;
}

@media (max-width: 768px) {
  .chart-toolbar {
    flex-direction: column;
    gap: 12px;
  }

  .toolbar-left,
  .toolbar-center,
  .toolbar-right {
    width: 100%;
    justify-content: center;
  }

  .period-group,
  .drawing-tools {
    flex-wrap: wrap;
  }
}
</style>
