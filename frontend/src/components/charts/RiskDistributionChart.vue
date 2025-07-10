<template>
  <div class="risk-distribution-chart" :style="{ height }">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useChart } from '@/composables/chart/useChart'

interface ChartData {
  name: string
  value: number
}

interface Props {
  data: ChartData[]
  chartType?: 'pie' | 'bar'
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  chartType: 'pie',
  height: '300px'
})

const chartRef = ref<HTMLElement>()
const { initChart, updateChart, resizeChart, disposeChart } = useChart()

let chartInstance: any = null

const riskColors = ['#f56c6c', '#e6a23c', '#409EFF', '#67c23a']

const initRiskDistributionChart = () => {
  if (!chartRef.value) return

  let option: any

  if (props.chartType === 'pie') {
    option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
        textStyle: {
          fontSize: 12
        }
      },
      series: [
        {
          name: '风险分布',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['60%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 4,
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
              fontSize: 16,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: props.data.map((item, index) => ({
            ...item,
            itemStyle: {
              color: riskColors[index % riskColors.length]
            }
          }))
        }
      ]
    }
  } else {
    option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: props.data.map(item => item.name),
        axisLabel: {
          fontSize: 12,
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          fontSize: 12,
          formatter: '{value}%'
        }
      },
      series: [
        {
          name: '风险占比',
          type: 'bar',
          data: props.data.map((item, index) => ({
            value: item.value,
            itemStyle: {
              color: riskColors[index % riskColors.length]
            }
          })),
          barWidth: '60%',
          itemStyle: {
            borderRadius: [4, 4, 0, 0]
          }
        }
      ]
    }
  }

  chartInstance = initChart(chartRef.value, option)
}

const updateRiskDistributionChart = () => {
  if (!chartInstance) return

  // 重新初始化图表以切换类型
  disposeChart(chartInstance)
  initRiskDistributionChart()
}

// 监听数据和图表类型变化
watch(() => props.data, updateRiskDistributionChart, { deep: true })
watch(() => props.chartType, updateRiskDistributionChart)

onMounted(() => {
  initRiskDistributionChart()

  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    if (chartInstance) {
      resizeChart(chartInstance)
    }
  })
})

onUnmounted(() => {
  if (chartInstance) {
    disposeChart(chartInstance)
  }
  window.removeEventListener('resize', () => {})
})
</script>

<style scoped>
.risk-distribution-chart {
  width: 100%;
}

.chart-container {
  width: 100%;
  height: 100%;
}
</style>
