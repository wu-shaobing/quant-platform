// 全局组件注册文件
import type { App } from 'vue'

// 导入组件
import VirtualTable from './common/VirtualTable/index.vue'
import MetricCard from './widgets/MetricCard.vue'
import KLineChart from './charts/KLineChart/index.vue'
import DepthChart from './charts/DepthChart/index.vue'
import AssetTrendChart from './charts/AssetTrendChart.vue'
import PositionPieChart from './charts/PositionPieChart.vue'
import OrderForm from './trading/OrderForm/index.vue'
import OrderBook from './trading/OrderBook.vue'
import PositionList from './trading/PositionList.vue'
import QuickOrderForm from './trading/QuickOrderForm.vue'
import StockCard from './market/StockCard.vue'
import BacktestForm from './backtest/BacktestForm.vue'
import StrategyCard from './strategy/StrategyCard/StrategyCard.vue'
import AppButton from './common/AppButton/index.vue'
import AppCard from './common/AppCard/index.vue'
import AppModal from './common/AppModal/index.vue'

// 组件映射
const components = {
  VirtualTable,
  MetricCard,
  KLineChart,
  DepthChart,
  AssetTrendChart,
  PositionPieChart,
  OrderForm,
  OrderBook,
  PositionList,
  QuickOrderForm,
  StockCard,
  BacktestForm,
  StrategyCard,
  AppButton,
  AppCard,
  AppModal
}

// 安装插件
export default {
  install(app: App) {
    // 注册全局组件
    Object.entries(components).forEach(([name, component]) => {
      app.component(name, component)
    })
  }
}

// 导出组件以供按需引入
export {
  VirtualTable,
  MetricCard,
  KLineChart,
  DepthChart,
  AssetTrendChart,
  PositionPieChart,
  OrderForm,
  OrderBook,
  PositionList,
  QuickOrderForm,
  StockCard,
  BacktestForm,
  StrategyCard,
  AppButton,
  AppCard,
  AppModal
}