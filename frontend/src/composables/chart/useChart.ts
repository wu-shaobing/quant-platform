/**
 * 图表管理组合函数
 * 提供通用的图表初始化、更新、销毁等功能
 */

import { ref, onUnmounted, nextTick, type Ref } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { debounce } from 'lodash-es'

export interface UseChartOptions {
  theme?: string | object
  renderer?: 'canvas' | 'svg'
  useDirtyRect?: boolean
  autoResize?: boolean
  resizeDelay?: number
}

export interface UseChartReturn {
  chart: Ref<echarts.ECharts | null>
  loading: Ref<boolean>
  initChart: (container: HTMLElement, options?: UseChartOptions) => Promise<void>
  updateChart: (option: EChartsOption, notMerge?: boolean) => void
  resizeChart: () => void
  showLoading: (text?: string) => void
  hideLoading: () => void
  disposeChart: () => void
  setOption: (option: EChartsOption, notMerge?: boolean) => void
  getInstance: () => echarts.ECharts | null
}

/**
 * 图表管理Hook
 */
export function useChart(options: UseChartOptions = {}): UseChartReturn {
  const chart = ref<echarts.ECharts | null>(null)
  const loading = ref(false)

  const {
    theme = 'light',
    renderer = 'canvas',
    useDirtyRect = true,
    autoResize = true,
    resizeDelay = 200
  } = options

  // 防抖的resize处理
  const debouncedResize = debounce(() => {
    if (chart.value && !chart.value.isDisposed()) {
      chart.value.resize()
    }
  }, resizeDelay)

  /**
   * 初始化图表
   */
  const initChart = async (container: HTMLElement, initOptions?: UseChartOptions): Promise<void> => {
    if (!container) {
      throw new Error('Chart container is required')
    }

    await nextTick()

    // 如果已存在图表实例，先销毁
    if (chart.value) {
      chart.value.dispose()
    }

    const finalOptions = { ...options, ...initOptions }

    chart.value = echarts.init(container, finalOptions.theme || theme, {
      renderer: finalOptions.renderer || renderer,
      useDirtyRect: finalOptions.useDirtyRect ?? useDirtyRect
    })

    // 监听窗口resize
    if (finalOptions.autoResize ?? autoResize) {
      window.addEventListener('resize', debouncedResize)
    }

    // 监听图表事件
    chart.value.on('finished', () => {
      loading.value = false
    })
  }

  /**
   * 更新图表配置
   */
  const updateChart = (option: EChartsOption, notMerge = false): void => {
    if (!chart.value || chart.value.isDisposed()) {
      console.warn('Chart instance is not available')
      return
    }

    loading.value = true

    try {
      chart.value.setOption(option, notMerge)
    } catch (error) {
      console.error('Chart update error:', error)
      loading.value = false
    }
  }

  /**
   * 设置图表配置（别名）
   */
  const setOption = (option: EChartsOption, notMerge = false): void => {
    updateChart(option, notMerge)
  }

  /**
   * 手动触发图表resize
   */
  const resizeChart = (): void => {
    if (chart.value && !chart.value.isDisposed()) {
      chart.value.resize()
    }
  }

  /**
   * 显示加载状态
   */
  const showLoading = (text = '加载中...'): void => {
    if (!chart.value || chart.value.isDisposed()) return

    chart.value.showLoading('default', {
      text,
      color: '#409EFF',
      textColor: '#666',
      maskColor: 'rgba(255, 255, 255, 0.8)',
      zlevel: 0,
      fontSize: 12,
      showSpinner: true,
      spinnerRadius: 10,
      lineWidth: 5
    })
  }

  /**
   * 隐藏加载状态
   */
  const hideLoading = (): void => {
    if (chart.value && !chart.value.isDisposed()) {
      chart.value.hideLoading()
    }
    loading.value = false
  }

  /**
   * 销毁图表
   */
  const disposeChart = (): void => {
    // 移除resize监听
    window.removeEventListener('resize', debouncedResize)

    // 销毁图表实例
    if (chart.value && !chart.value.isDisposed()) {
      chart.value.dispose()
    }

    chart.value = null
    loading.value = false
  }

  /**
   * 获取图表实例
   */
  const getInstance = (): echarts.ECharts | null => {
    return chart.value
  }

  // 组件卸载时自动清理
  onUnmounted(() => {
    disposeChart()
  })

  return {
    chart,
    loading,
    initChart,
    updateChart,
    resizeChart,
    showLoading,
    hideLoading,
    disposeChart,
    setOption,
    getInstance
  }
}

/**
 * 图表主题管理
 */
export function useChartTheme() {
  const currentTheme = ref<string>('light')

  const themes = {
    light: {
      backgroundColor: '#ffffff',
      textStyle: {
        color: '#333333'
      },
      grid: {
        borderColor: '#e8e8e8'
      }
    },
    dark: {
      backgroundColor: '#1a1a1a',
      textStyle: {
        color: '#ffffff'
      },
      grid: {
        borderColor: '#404040'
      }
    }
  } as const

  const setTheme = (theme: keyof typeof themes) => {
    currentTheme.value = theme
  }

  const getThemeConfig = (theme?: string) => {
    return themes[theme as keyof typeof themes] || themes[currentTheme.value as keyof typeof themes] || themes.light
  }

  return {
    currentTheme,
    themes,
    setTheme,
    getThemeConfig
  }
}

/**
 * 图表工具函数
 */
export const chartUtils = {
  /**
   * 格式化数值
   */
  formatValue: (value: number, precision = 2): string => {
    if (value >= 1e8) {
      return (value / 1e8).toFixed(precision) + '亿'
    } else if (value >= 1e4) {
      return (value / 1e4).toFixed(precision) + '万'
    }
    return value.toFixed(precision)
  },

  /**
   * 格式化百分比
   */
  formatPercent: (value: number, precision = 2): string => {
    return (value * 100).toFixed(precision) + '%'
  },

  /**
   * 获取颜色
   */
  getColor: (index: number, colors?: string[]): string => {
    const defaultColors = [
      '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
      '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#8b7ec8'
    ]
    const colorArray = colors || defaultColors
    return colorArray[index % colorArray.length]
  },

  /**
   * 生成渐变色
   */
  generateGradient: (color: string, direction = 'vertical'): object => {
    return {
      type: 'linear',
      x: 0,
      y: 0,
      x2: direction === 'horizontal' ? 1 : 0,
      y2: direction === 'vertical' ? 1 : 0,
      colorStops: [
        { offset: 0, color: color + 'ff' },
        { offset: 1, color: color + '00' }
      ]
    }
  }
}

export default useChart