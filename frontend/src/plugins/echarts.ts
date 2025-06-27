/**
 * ECharts 配置
 */
import * as echarts from 'echarts/core'
import {
  BarChart,
  LineChart,
  PieChart,
  ScatterChart,
  CandlestickChart,
  HeatmapChart,
  TreemapChart,
  GaugeChart
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  MarkPointComponent,
  MarkLineComponent,
  ToolboxComponent,
  BrushComponent,
  VisualMapComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

export const setupECharts = () => {
  // 注册必要的组件
  echarts.use([
    // 图表类型
    BarChart,
    LineChart,
    PieChart,
    ScatterChart,
    CandlestickChart,
    HeatmapChart,
    TreemapChart,
    GaugeChart,
    
    // 组件
    TitleComponent,
    TooltipComponent,
    GridComponent,
    LegendComponent,
    DataZoomComponent,
    MarkPointComponent,
    MarkLineComponent,
    ToolboxComponent,
    BrushComponent,
    VisualMapComponent,
    
    // 渲染器
    CanvasRenderer
  ])
}

export { echarts }