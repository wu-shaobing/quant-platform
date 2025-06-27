<template>
  <div class="depth-chart" ref="chartRef"></div>
</template>

<script setup lang="ts" name="DepthChart">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

interface DepthData {
  price: number
  volume: number
  type: 'bid' | 'ask'
}

interface Props {
  data?: DepthData[]
  height?: string | number
  theme?: 'light' | 'dark'
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  height: '400px',
  theme: 'light'
})

const chartRef = ref<HTMLDivElement>()
let chartInstance: echarts.ECharts | null = null

const initChart = async () => {
  if (!chartRef.value) return

  await nextTick()
  
  chartInstance = echarts.init(chartRef.value, props.theme)
  
  const option = {
    title: {
      text: '市场深度',
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: Array<{ axisValue: string; value: number; seriesName: string }>) => {
        const data = params?.[0]
        return `
          <div>
            <div>价格: ¥${data.axisValue}</div>
            <div>数量: ${data.value}</div>
            <div>类型: ${data.seriesName}</div>
          </div>
        `
      }
    },
    legend: {
      data: ['买盘', '卖盘'],
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: [],
      axisLabel: {
        formatter: (value: string) => `¥${value}`
      }
    },
    yAxis: {
      type: 'value',
      name: '累计数量',
      axisLabel: {
        formatter: (value: number) => `${(value / 10000).toFixed(1)}万`
      }
    },
    series: [
      {
        name: '买盘',
        type: 'line',
        data: [],
        smooth: true,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(34, 197, 94, 0.3)' },
              { offset: 1, color: 'rgba(34, 197, 94, 0.1)' }
            ]
          }
        },
        lineStyle: {
          color: '#22c55e',
          width: 2
        },
        itemStyle: {
          color: '#22c55e'
        }
      },
      {
        name: '卖盘',
        type: 'line',
        data: [],
        smooth: true,
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(239, 68, 68, 0.3)' },
              { offset: 1, color: 'rgba(239, 68, 68, 0.1)' }
            ]
          }
        },
        lineStyle: {
          color: '#ef4444',
          width: 2
        },
        itemStyle: {
          color: '#ef4444'
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

const updateChart = () => {
  if (!chartInstance || !props.data?.length) return

  // 分离买盘和卖盘数据
  const bids = props.data.filter(item => item.type === 'bid').sort((a, b) => b.price - a.price)
  const asks = props.data.filter(item => item.type === 'ask').sort((a, b) => a.price - b.price)

  // 计算累计数量
  let bidCumulative = 0
  let askCumulative = 0
  
  const bidData = bids.map(item => {
    bidCumulative += item.volume
    return {
      price: item.price.toFixed(2),
      volume: bidCumulative
    }
  })
  
  const askData = asks.map(item => {
    askCumulative += item.volume
    return {
      price: item.price.toFixed(2),
      volume: askCumulative
    }
  })

  // 合并价格轴数据
  const allPrices = [...bidData.map(d => d.price), ...askData.map(d => d.price)]
    .sort((a, b) => parseFloat(a) - parseFloat(b))
  
  // 为每个价格点填充数据
  const bidSeries = allPrices.map(price => {
    const found = bidData.find(d => d.price === price)
    return found ? found.volume : 0
  })
  
  const askSeries = allPrices.map(price => {
    const found = askData.find(d => d.price === price)
    return found ? found.volume : 0
  })

  chartInstance.setOption({
    xAxis: {
      data: allPrices
    },
    series: [
      {
        data: bidSeries
      },
      {
        data: askSeries
      }
    ]
  })
}

const handleResize = () => {
  chartInstance?.resize()
}

// 监听数据变化
watch(() => props.data, updateChart, { deep: true })
watch(() => props.theme, () => {
  if (chartInstance) {
    chartInstance.dispose()
    initChart()
  }
})

onMounted(() => {
  initChart()
})

onUnmounted(() => {
  if (chartInstance) {
    window.removeEventListener('resize', handleResize)
    chartInstance.dispose()
    chartInstance = null
  }
})

// 暴露方法供父组件调用
defineExpose({
  refresh: updateChart,
  resize: handleResize
})
</script>

<style scoped lang="scss">
.depth-chart {
  width: 100%;
  height: v-bind(height);
  min-height: 300px;
}
</style> 