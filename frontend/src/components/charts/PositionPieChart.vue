<template>
  <div class="position-pie-chart">
    <div ref="chartContainer" :style="{ height: heightPx }"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as echarts from 'echarts'

interface PositionData {
  name: string
  value: number
  percent: number
}

type HeightType = number | string

interface Props {
  data: PositionData[]
  height?: HeightType
}

const props = withDefaults(defineProps<Props>(), {
  height: 300
})

const chartContainer = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const heightPx = computed(() => {
  if (typeof props.height === 'number') return `${props.height}px`
  if (props.height.endsWith('px')) return props.height
  return `${parseInt(props.height as string, 10)}px`
})

const initChart = async () => {
  if (!chartContainer.value) return
  
  await nextTick()
  
  chart = echarts.init(chartContainer.value)
  
  const option = {
    title: {
      text: '持仓分布',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: echarts.TooltipComponentFormatterCallbackParams) => {
        if (Array.isArray(params)) return ''
        return `${params.name}<br/>市值: ¥${params.value?.toLocaleString()}<br/>占比: ${params.percent}%`
      }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        name: '持仓分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: props.data.map((item, index) => ({
          value: item.value,
          name: item.name,
          itemStyle: {
            color: getColor(index)
          }
        }))
      }
    ]
  }
  
  chart.setOption(option)
}

const getColor = (index: number) => {
  const colors = [
    '#409EFF',
    '#67C23A',
    '#E6A23C',
    '#F56C6C',
    '#909399',
    '#5470c6',
    '#91cc75',
    '#fac858',
    '#ee6666',
    '#73c0de'
  ]
  return colors[index % colors.length]
}

const updateChart = () => {
  if (!chart) return
  
  const option = {
    series: [
      {
        data: props.data.map((item, index) => ({
          value: item.value,
          name: item.name,
          itemStyle: {
            color: getColor(index)
          }
        }))
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
.position-pie-chart {
  width: 100%;
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>