<template>
  <div class="asset-trend-chart">
    <div ref="chartContainer" :style="{ height: heightPx }"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as echarts from 'echarts'

interface TrendData {
  date: string
  value: number
}

type HeightType = number | string

interface Props {
  data: TrendData[]
  height?: HeightType
}

const props = withDefaults(defineProps<Props>(), {
  height: 300
})

const heightPx = computed(() => {
  if (typeof props.height === 'number') return `${props.height}px`
  if (props.height.endsWith('px')) return props.height
  return `${parseInt(props.height as string, 10)}px`
})

const chartContainer = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const initChart = async () => {
  if (!chartContainer.value) return
  
  await nextTick()
  
  chart = echarts.init(chartContainer.value)
  
  const option = {
    title: {
      text: '资产趋势',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: echarts.TooltipComponentFormatterCallbackParams) => {
        if (!Array.isArray(params) || params.length === 0) return ''
        const data = params[0]
        return `${data?.axisValue || ''}<br/>资产总值: ¥${data?.value?.toLocaleString() || ''}`
      }
    },
    xAxis: {
      type: 'category',
      data: props.data.map(item => item.date),
      axisLine: {
        lineStyle: {
          color: '#e8e8e8'
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => `¥${(value / 10000).toFixed(0)}万`
      },
      axisLine: {
        lineStyle: {
          color: '#e8e8e8'
        }
      },
      splitLine: {
        lineStyle: {
          color: '#f0f0f0'
        }
      }
    },
    series: [
      {
        name: '资产总值',
        type: 'line',
        data: props.data.map(item => item.value),
        smooth: true,
        lineStyle: {
          color: '#409EFF',
          width: 3
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ]
          }
        },
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: {
          color: '#409EFF'
        }
      }
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }
  
  chart.setOption(option)
}

const updateChart = () => {
  if (!chart) return
  
  const option = {
    xAxis: {
      data: props.data.map(item => item.date)
    },
    series: [
      {
        data: props.data.map(item => item.value)
      }
    ]
  }
  
  chart.setOption(option)
}

watch(() => props.data, updateChart, { deep: true })

const handleResize = () => {
  chart?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.asset-trend-chart {
  width: 100%;
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>