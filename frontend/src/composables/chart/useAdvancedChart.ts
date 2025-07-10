/**
 * 高级图表组合函数
 * 支持高级交互功能、绘图工具、技术分析等
 */

import { ref, computed, onMounted, onUnmounted, watch, type Ref } from 'vue'
import * as echarts from 'echarts'
import { useEventListener } from '@/composables/core/useEventListener'
import { useKeyboardShortcuts } from '@/composables/keyboard/useKeyboardShortcuts'
import { useLocalStorage } from '@/composables/core/useLocalStorage'
import type { KLinePoint } from '@/utils/indicators/technical'

export interface DrawingTool {
  id: string
  type: 'line' | 'rect' | 'circle' | 'text' | 'fibonacci' | 'trendline'
  name: string
  icon: string
  cursor: string
}

export interface DrawingElement {
  id: string
  type: DrawingTool['type']
  points: Array<{ x: number; y: number; timestamp: number; price: number }>
  style: {
    color: string
    lineWidth: number
    lineDash?: number[]
    text?: string
    fontSize?: number
  }
  visible: boolean
  locked: boolean
  created: number
}

export interface ChartSettings {
  theme: 'light' | 'dark'
  gridLines: boolean
  crosshair: boolean
  priceLabels: boolean
  volumeChart: boolean
  indicatorPanels: number
  candleStyle: 'candle' | 'bar' | 'line'
  colors: {
    up: string
    down: string
    background: string
    grid: string
    text: string
  }
}

export interface AlertLevel {
  id: string
  price: number
  type: 'support' | 'resistance' | 'target'
  message: string
  enabled: boolean
  triggered: boolean
  created: number
}

export function useAdvancedChart(container: Ref<HTMLElement | undefined>) {
  // 图表实例
  const chart = ref<echarts.ECharts | null>(null)

  // 图表状态
  const isInitialized = ref(false)
  const isLoading = ref(false)
  const isDrawing = ref(false)
  const isDragging = ref(false)
  const isSelecting = ref(false)

  // 当前工具
  const currentTool = ref<DrawingTool | null>(null)
  const selectedElements = ref<string[]>([])

  // 绘图元素
  const drawingElements = ref<DrawingElement[]>([])
  const tempElement = ref<DrawingElement | null>(null)

  // 价格提醒
  const alertLevels = ref<AlertLevel[]>([])

  // 图表设置
  const chartSettings = ref<ChartSettings>({
    theme: 'light',
    gridLines: true,
    crosshair: true,
    priceLabels: true,
    volumeChart: true,
    indicatorPanels: 2,
    candleStyle: 'candle',
    colors: {
      up: '#26a69a',
      down: '#ef5350',
      background: '#ffffff',
      grid: '#e0e0e0',
      text: '#333333'
    }
  })

  // 可用绘图工具
  const drawingTools: DrawingTool[] = [
    {
      id: 'line',
      type: 'line',
      name: '直线',
      icon: 'line-chart',
      cursor: 'crosshair'
    },
    {
      id: 'trendline',
      type: 'trendline',
      name: '趋势线',
      icon: 'trending-up',
      cursor: 'crosshair'
    },
    {
      id: 'rect',
      type: 'rect',
      name: '矩形',
      icon: 'square',
      cursor: 'crosshair'
    },
    {
      id: 'circle',
      type: 'circle',
      name: '圆形',
      icon: 'circle',
      cursor: 'crosshair'
    },
    {
      id: 'fibonacci',
      type: 'fibonacci',
      name: '斐波那契回调',
      icon: 'git-merge',
      cursor: 'crosshair'
    },
    {
      id: 'text',
      type: 'text',
      name: '文本',
      icon: 'type',
      cursor: 'text'
    }
  ]

  // 键盘快捷键
  const shortcuts = {
    'Delete': () => deleteSelectedElements(),
    'Escape': () => clearSelection(),
    'Ctrl+A': () => selectAllElements(),
    'Ctrl+C': () => copySelectedElements(),
    'Ctrl+V': () => pasteElements(),
    'Ctrl+Z': () => undo(),
    'Ctrl+Y': () => redo(),
    'Ctrl+S': () => saveChart(),
    'F11': () => toggleFullscreen()
  }

  // 历史记录
  const history = ref<Array<{ elements: DrawingElement[]; alerts: AlertLevel[] }>>([])
  const historyIndex = ref(-1)
  const maxHistorySize = 50

  // 计算属性
  const canUndo = computed(() => historyIndex.value > 0)
  const canRedo = computed(() => historyIndex.value < history.value.length - 1)
  const hasSelection = computed(() => selectedElements.value.length > 0)

  // 初始化图表
  const initChart = async () => {
    if (!container.value || isInitialized.value) return

    try {
      chart.value = echarts.init(container.value, chartSettings.value.theme)
      isInitialized.value = true

      // 绑定事件
      bindChartEvents()

      // 应用设置
      applyChartSettings()

      console.log('高级图表初始化成功')
    } catch (error) {
      console.error('图表初始化失败:', error)
    }
  }

  // 绑定图表事件
  const bindChartEvents = () => {
    if (!chart.value) return

    // 鼠标事件
    chart.value.on('mousedown', handleMouseDown)
    chart.value.on('mousemove', handleMouseMove)
    chart.value.on('mouseup', handleMouseUp)
    chart.value.on('click', handleClick)
    chart.value.on('dblclick', handleDoubleClick)

    // 缩放事件
    chart.value.on('datazoom', handleDataZoom)

    // 选择事件
    chart.value.on('selectchanged', handleSelectChanged)
  }

  // 鼠标按下事件
  const handleMouseDown = (params: any) => {
    if (!currentTool.value) return

    const point = getChartPoint(params.event.offsetX, params.event.offsetY)
    if (!point) return

    isDrawing.value = true

    // 开始绘制新元素
    tempElement.value = {
      id: generateId(),
      type: currentTool.value.type,
      points: [point],
      style: getDefaultStyle(currentTool.value.type),
      visible: true,
      locked: false,
      created: Date.now()
    }
  }

  // 鼠标移动事件
  const handleMouseMove = (params: any) => {
    if (!isDrawing.value || !tempElement.value) return

    const point = getChartPoint(params.event.offsetX, params.event.offsetY)
    if (!point) return

    // 更新临时元素
    if (tempElement.value.points.length === 1) {
      tempElement.value.points.push(point)
    } else {
      tempElement.value.points[1] = point
    }

    // 重绘图表
    updateChart()
  }

  // 鼠标释放事件
  const handleMouseUp = (params: any) => {
    if (!isDrawing.value || !tempElement.value) return

    isDrawing.value = false

    // 完成绘制
    if (tempElement.value.points.length >= 2) {
      drawingElements.value.push({ ...tempElement.value })
      saveToHistory()
    }

    tempElement.value = null
    updateChart()
  }

  // 点击事件
  const handleClick = (params: any) => {
    if (currentTool.value) return

    // 选择元素
    const elementId = getElementAtPoint(params.event.offsetX, params.event.offsetY)
    if (elementId) {
      if (params.event.ctrlKey) {
        toggleElementSelection(elementId)
      } else {
        selectElement(elementId)
      }
    } else {
      clearSelection()
    }
  }

  // 双击事件
  const handleDoubleClick = (params: any) => {
    const elementId = getElementAtPoint(params.event.offsetX, params.event.offsetY)
    if (elementId) {
      editElement(elementId)
    }
  }

  // 数据缩放事件
  const handleDataZoom = (params: any) => {
    // 重新计算绘图元素位置
    updateDrawingElementsPosition()
  }

  // 选择变化事件
  const handleSelectChanged = (params: any) => {
    // 处理批量选择
  }

  // 获取图表坐标点
  const getChartPoint = (x: number, y: number) => {
    if (!chart.value) return null

    const pointInPixel = [x, y]
    const pointInGrid = chart.value.convertFromPixel('grid', pointInPixel)

    if (!pointInGrid) return null

    return {
      x,
      y,
      timestamp: pointInGrid[0],
      price: pointInGrid[1]
    }
  }

  // 获取指定位置的元素
  const getElementAtPoint = (x: number, y: number): string | null => {
    // 实现元素碰撞检测
    for (const element of drawingElements.value) {
      if (isPointInElement(x, y, element)) {
        return element.id
      }
    }
    return null
  }

  // 检查点是否在元素内
  const isPointInElement = (x: number, y: number, element: DrawingElement): boolean => {
    // 根据元素类型实现不同的碰撞检测逻辑
    switch (element.type) {
      case 'line':
      case 'trendline':
        return isPointNearLine(x, y, element.points)
      case 'rect':
        return isPointInRect(x, y, element.points)
      case 'circle':
        return isPointInCircle(x, y, element.points)
      default:
        return false
    }
  }

  // 点是否接近直线
  const isPointNearLine = (x: number, y: number, points: any[]): boolean => {
    if (points.length < 2) return false

    const threshold = 5 // 像素阈值
    const [p1, p2] = points

    // 计算点到直线的距离
    const distance = pointToLineDistance(x, y, p1.x, p1.y, p2.x, p2.y)
    return distance <= threshold
  }

  // 点到直线距离
  const pointToLineDistance = (px: number, py: number, x1: number, y1: number, x2: number, y2: number): number => {
    const A = px - x1
    const B = py - y1
    const C = x2 - x1
    const D = y2 - y1

    const dot = A * C + B * D
    const lenSq = C * C + D * D

    if (lenSq === 0) return Math.sqrt(A * A + B * B)

    const param = dot / lenSq

    let xx: number, yy: number

    if (param < 0) {
      xx = x1
      yy = y1
    } else if (param > 1) {
      xx = x2
      yy = y2
    } else {
      xx = x1 + param * C
      yy = y1 + param * D
    }

    const dx = px - xx
    const dy = py - yy

    return Math.sqrt(dx * dx + dy * dy)
  }

  // 点是否在矩形内
  const isPointInRect = (x: number, y: number, points: any[]): boolean => {
    if (points.length < 2) return false

    const [p1, p2] = points
    const minX = Math.min(p1.x, p2.x)
    const maxX = Math.max(p1.x, p2.x)
    const minY = Math.min(p1.y, p2.y)
    const maxY = Math.max(p1.y, p2.y)

    return x >= minX && x <= maxX && y >= minY && y <= maxY
  }

  // 点是否在圆内
  const isPointInCircle = (x: number, y: number, points: any[]): boolean => {
    if (points.length < 2) return false

    const [center, edge] = points
    const radius = Math.sqrt(
      Math.pow(edge.x - center.x, 2) + Math.pow(edge.y - center.y, 2)
    )

    const distance = Math.sqrt(
      Math.pow(x - center.x, 2) + Math.pow(y - center.y, 2)
    )

    return distance <= radius
  }

  // 选择工具
  const selectTool = (tool: DrawingTool | null) => {
    currentTool.value = tool
    clearSelection()

    // 更新鼠标样式
    if (container.value) {
      container.value.style.cursor = tool?.cursor || 'default'
    }
  }

  // 选择元素
  const selectElement = (elementId: string) => {
    selectedElements.value = [elementId]
  }

  // 切换元素选择状态
  const toggleElementSelection = (elementId: string) => {
    const index = selectedElements.value.indexOf(elementId)
    if (index > -1) {
      selectedElements.value.splice(index, 1)
    } else {
      selectedElements.value.push(elementId)
    }
  }

  // 清除选择
  const clearSelection = () => {
    selectedElements.value = []
  }

  // 选择所有元素
  const selectAllElements = () => {
    selectedElements.value = drawingElements.value.map(el => el.id)
  }

  // 删除选中元素
  const deleteSelectedElements = () => {
    drawingElements.value = drawingElements.value.filter(
      el => !selectedElements.value.includes(el.id)
    )
    clearSelection()
    saveToHistory()
    updateChart()
  }

  // 复制选中元素
  const copySelectedElements = () => {
    const selectedEls = drawingElements.value.filter(
      el => selectedElements.value.includes(el.id)
    )

    // 保存到剪贴板
    localStorage.setItem('chart-clipboard', JSON.stringify(selectedEls))
  }

  // 粘贴元素
  const pasteElements = () => {
    const clipboardData = localStorage.getItem('chart-clipboard')
    if (!clipboardData) return

    try {
      const elements: DrawingElement[] = JSON.parse(clipboardData)
      const offset = 20 // 像素偏移

      const newElements = elements.map(el => ({
        ...el,
        id: generateId(),
        points: el.points.map(p => ({ ...p, x: p.x + offset, y: p.y + offset })),
        created: Date.now()
      }))

      drawingElements.value.push(...newElements)
      selectedElements.value = newElements.map(el => el.id)
      saveToHistory()
      updateChart()
    } catch (error) {
      console.error('粘贴失败:', error)
    }
  }

  // 编辑元素
  const editElement = (elementId: string) => {
    const element = drawingElements.value.find(el => el.id === elementId)
    if (!element) return

    // 打开编辑对话框
    // TODO: 实现编辑对话框
  }

  // 获取默认样式
  const getDefaultStyle = (type: DrawingTool['type']) => {
    const baseStyle = {
      color: chartSettings.value.colors.text,
      lineWidth: 2
    }

    switch (type) {
      case 'line':
      case 'trendline':
        return baseStyle
      case 'rect':
        return { ...baseStyle, fill: 'transparent' }
      case 'circle':
        return { ...baseStyle, fill: 'transparent' }
      case 'fibonacci':
        return { ...baseStyle, lineDash: [5, 5] }
      case 'text':
        return { ...baseStyle, fontSize: 14, text: '文本' }
      default:
        return baseStyle
    }
  }

  // 生成唯一ID
  const generateId = (): string => {
    return `element_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  // 保存到历史记录
  const saveToHistory = () => {
    // 移除后续历史记录
    history.value = history.value.slice(0, historyIndex.value + 1)

    // 添加新状态
    history.value.push({
      elements: JSON.parse(JSON.stringify(drawingElements.value)),
      alerts: JSON.parse(JSON.stringify(alertLevels.value))
    })

    // 限制历史记录大小
    if (history.value.length > maxHistorySize) {
      history.value.shift()
    } else {
      historyIndex.value++
    }
  }

  // 撤销
  const undo = () => {
    if (!canUndo.value) return

    historyIndex.value--
    const state = history.value[historyIndex.value]

    drawingElements.value = JSON.parse(JSON.stringify(state.elements))
    alertLevels.value = JSON.parse(JSON.stringify(state.alerts))

    updateChart()
  }

  // 重做
  const redo = () => {
    if (!canRedo.value) return

    historyIndex.value++
    const state = history.value[historyIndex.value]

    drawingElements.value = JSON.parse(JSON.stringify(state.elements))
    alertLevels.value = JSON.parse(JSON.stringify(state.alerts))

    updateChart()
  }

  // 更新图表
  const updateChart = () => {
    if (!chart.value) return

    // 更新图表配置，包含绘图元素
    const option = buildChartOption()
    chart.value.setOption(option, true)
  }

  // 构建图表配置
  const buildChartOption = () => {
    // 基础配置
    const option: any = {
      // ... 基础图表配置
    }

    // 添加绘图元素
    addDrawingElementsToOption(option)

    // 添加价格提醒线
    addAlertLevelsToOption(option)

    return option
  }

  // 添加绘图元素到图表配置
  const addDrawingElementsToOption = (option: any) => {
    const markLines: any[] = []
    const markAreas: any[] = []
    const markPoints: any[] = []

    // 处理所有绘图元素
    for (const element of drawingElements.value) {
      if (!element.visible) continue

      switch (element.type) {
        case 'line':
        case 'trendline':
          markLines.push(createLineMarkup(element))
          break
        case 'rect':
          markAreas.push(createRectMarkup(element))
          break
        case 'circle':
          markPoints.push(createCircleMarkup(element))
          break
        case 'fibonacci':
          markLines.push(...createFibonacciMarkup(element))
          break
        case 'text':
          markPoints.push(createTextMarkup(element))
          break
      }
    }

    // 添加到图表配置
    if (option.series && option.series[0]) {
      option.series[0].markLine = { data: markLines }
      option.series[0].markArea = { data: markAreas }
      option.series[0].markPoint = { data: markPoints }
    }
  }

  // 创建直线标记
  const createLineMarkup = (element: DrawingElement) => {
    const [start, end] = element.points
    return {
      lineStyle: {
        color: element.style.color,
        width: element.style.lineWidth,
        type: element.style.lineDash ? 'dashed' : 'solid'
      },
      data: [
        { coord: [start.timestamp, start.price] },
        { coord: [end.timestamp, end.price] }
      ]
    }
  }

  // 创建矩形标记
  const createRectMarkup = (element: DrawingElement) => {
    const [start, end] = element.points
    return {
      itemStyle: {
        color: 'transparent',
        borderColor: element.style.color,
        borderWidth: element.style.lineWidth
      },
      data: [
        [
          { coord: [start.timestamp, start.price] },
          { coord: [end.timestamp, end.price] }
        ]
      ]
    }
  }

  // 创建圆形标记
  const createCircleMarkup = (element: DrawingElement) => {
    const [center] = element.points
    return {
      coord: [center.timestamp, center.price],
      symbol: 'circle',
      symbolSize: 20,
      itemStyle: {
        color: 'transparent',
        borderColor: element.style.color,
        borderWidth: element.style.lineWidth
      }
    }
  }

  // 创建斐波那契标记
  const createFibonacciMarkup = (element: DrawingElement) => {
    const [start, end] = element.points
    const priceRange = end.price - start.price
    const timeRange = end.timestamp - start.timestamp

    const fibLevels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]

    return fibLevels.map(level => ({
      lineStyle: {
        color: element.style.color,
        width: 1,
        type: 'dashed'
      },
      label: {
        formatter: `${(level * 100).toFixed(1)}%`
      },
      data: [
        { coord: [start.timestamp, start.price + priceRange * level] },
        { coord: [end.timestamp, start.price + priceRange * level] }
      ]
    }))
  }

  // 创建文本标记
  const createTextMarkup = (element: DrawingElement) => {
    const [point] = element.points
    return {
      coord: [point.timestamp, point.price],
      label: {
        formatter: element.style.text || '文本',
        fontSize: element.style.fontSize || 14,
        color: element.style.color
      }
    }
  }

  // 添加价格提醒线
  const addAlertLevelsToOption = (option: any) => {
    const alertLines = alertLevels.value
      .filter(alert => alert.enabled && !alert.triggered)
      .map(alert => ({
        yAxis: alert.price,
        lineStyle: {
          color: getAlertColor(alert.type),
          width: 2,
          type: 'dashed'
        },
        label: {
          formatter: `${alert.type}: ${alert.price}`,
          position: 'end'
        }
      }))

    if (option.series && option.series[0]) {
      option.series[0].markLine = option.series[0].markLine || {}
      option.series[0].markLine.data = [
        ...(option.series[0].markLine.data || []),
        ...alertLines
      ]
    }
  }

  // 获取提醒颜色
  const getAlertColor = (type: AlertLevel['type']): string => {
    switch (type) {
      case 'support':
        return '#4CAF50'
      case 'resistance':
        return '#F44336'
      case 'target':
        return '#FF9800'
      default:
        return '#2196F3'
    }
  }

  // 更新绘图元素位置
  const updateDrawingElementsPosition = () => {
    // 当图表缩放时，重新计算绘图元素的像素位置
    for (const element of drawingElements.value) {
      for (const point of element.points) {
        if (chart.value) {
          const pixelPoint = chart.value.convertToPixel('grid', [point.timestamp, point.price])
          if (pixelPoint) {
            point.x = pixelPoint[0]
            point.y = pixelPoint[1]
          }
        }
      }
    }
  }

  // 应用图表设置
  const applyChartSettings = () => {
    if (!chart.value) return

    // 应用主题
    chart.value.dispose()
    chart.value = echarts.init(container.value!, chartSettings.value.theme)
    bindChartEvents()

    // 重新渲染
    updateChart()
  }

  // 保存图表
  const saveChart = () => {
    const chartData = {
      elements: drawingElements.value,
      alerts: alertLevels.value,
      settings: chartSettings.value,
      timestamp: Date.now()
    }

    // 保存到本地存储或服务器
    localStorage.setItem('saved-chart', JSON.stringify(chartData))

    console.log('图表已保存')
  }

  // 加载图表
  const loadChart = () => {
    const savedData = localStorage.getItem('saved-chart')
    if (!savedData) return

    try {
      const chartData = JSON.parse(savedData)

      drawingElements.value = chartData.elements || []
      alertLevels.value = chartData.alerts || []
      chartSettings.value = { ...chartSettings.value, ...chartData.settings }

      updateChart()
      console.log('图表已加载')
    } catch (error) {
      console.error('加载图表失败:', error)
    }
  }

  // 切换全屏
  const toggleFullscreen = () => {
    if (!container.value) return

    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      container.value.requestFullscreen()
    }
  }

  // 导出图表
  const exportChart = (format: 'png' | 'jpeg' | 'svg' = 'png') => {
    if (!chart.value) return

    const url = chart.value.getDataURL({
      type: format,
      pixelRatio: 2,
      backgroundColor: chartSettings.value.colors.background
    })

    // 下载图片
    const link = document.createElement('a')
    link.download = `chart_${Date.now()}.${format}`
    link.href = url
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // 添加价格提醒
  const addAlertLevel = (price: number, type: AlertLevel['type'], message: string) => {
    const alert: AlertLevel = {
      id: generateId(),
      price,
      type,
      message,
      enabled: true,
      triggered: false,
      created: Date.now()
    }

    alertLevels.value.push(alert)
    saveToHistory()
    updateChart()
  }

  // 移除价格提醒
  const removeAlertLevel = (alertId: string) => {
    alertLevels.value = alertLevels.value.filter(alert => alert.id !== alertId)
    saveToHistory()
    updateChart()
  }

  // 检查价格提醒
  const checkAlertLevels = (currentPrice: number) => {
    for (const alert of alertLevels.value) {
      if (!alert.enabled || alert.triggered) continue

      const triggered = Math.abs(currentPrice - alert.price) < 0.01 // 1分钱容差

      if (triggered) {
        alert.triggered = true

        // 触发提醒事件
        console.log(`价格提醒触发: ${alert.message}`)

        // 可以在这里添加通知逻辑
        // showNotification(alert.message)
      }
    }
  }

  // 设置键盘快捷键
  // useKeyboardShortcuts(shortcuts)

  // 监听窗口大小变化
  useEventListener(window, 'resize', () => {
    if (chart.value) {
      chart.value.resize()
    }
  })

  // 组件挂载时初始化
  onMounted(() => {
    initChart()
    loadChart()
  })

  // 组件卸载时清理
  onUnmounted(() => {
    if (chart.value) {
      chart.value.dispose()
    }
  })

  return {
    // 状态
    chart,
    isInitialized,
    isLoading,
    isDrawing,
    isDragging,
    isSelecting,

    // 工具和元素
    currentTool,
    drawingTools,
    drawingElements,
    selectedElements,
    alertLevels,

    // 设置
    chartSettings,

    // 历史记录
    canUndo,
    canRedo,
    hasSelection,

    // 方法
    initChart,
    updateChart,
    selectTool,
    selectElement,
    clearSelection,
    selectAllElements,
    deleteSelectedElements,
    copySelectedElements,
    pasteElements,
    editElement,
    undo,
    redo,
    saveChart,
    loadChart,
    exportChart,
    toggleFullscreen,
    addAlertLevel,
    removeAlertLevel,
    checkAlertLevels,
    applyChartSettings
  }
}
