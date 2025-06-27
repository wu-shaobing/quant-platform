<template>
  <div class="component-showcase">
    <div class="showcase-header">
      <h1>组件展示中心</h1>
      <p>展示量化投资平台的核心组件和功能</p>
    </div>

    <!-- 组件导航 -->
    <div class="showcase-nav">
      <el-tabs v-model="activeTab" type="card">
        <el-tab-pane label="图表组件" name="charts">
          <div class="component-section">
            <!-- K线图展示 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>K线图组件</h3>
                <p>专业的股票K线图表，支持多种技术指标</p>
              </div>
              <div class="demo-content">
                <KLineChart
                  :symbol="selectedSymbol"
                  :symbol-name="selectedSymbolName"
                  height="400px"
                  :show-toolbar="true"
                  @period-change="handlePeriodChange"
                  @data-update="handleDataUpdate"
                />
              </div>
              <div class="demo-controls">
                <el-select v-model="selectedSymbol" placeholder="选择股票">
                  <el-option
                    v-for="stock in demoStocks"
                    :key="stock.symbol"
                    :label="`${stock.symbol} - ${stock.name}`"
                    :value="stock.symbol"
                  />
                </el-select>
              </div>
            </div>

            <!-- 深度图展示 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>深度图组件</h3>
                <p>实时显示买卖盘深度数据</p>
              </div>
              <div class="demo-content">
                <DepthChart
                  :symbol="selectedSymbol"
                  :height="300"
                  :data="depthData"
                />
              </div>
            </div>

            <!-- 资产趋势图 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>资产趋势图</h3>
                <p>展示投资组合资产变化趋势</p>
              </div>
              <div class="demo-content">
                <AssetTrendChart
                  :data="assetTrendData"
                  :height="300"
                />
              </div>
            </div>

            <!-- 持仓饼图 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>持仓分布饼图</h3>
                <p>直观展示投资组合的持仓分布</p>
              </div>
              <div class="demo-content">
                <PositionPieChart
                  :data="positionData"
                  :height="300"
                />
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="交易组件" name="trading">
          <div class="component-section">
            <!-- 交易表单 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>交易下单表单</h3>
                <p>专业的股票交易下单界面</p>
              </div>
              <div class="demo-content">
                <div class="trading-demo">
                  <OrderForm
                    :default-symbol="selectedSymbol"
                    :quick-trade-mode="true"
                    @submit="handleOrderSubmit"
                    @stock-select="handleStockSelect"
                  />
                </div>
              </div>
            </div>

            <!-- 订单簿 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>订单簿组件</h3>
                <p>实时显示买卖盘数据</p>
              </div>
              <div class="demo-content">
                <OrderBook
                  :symbol="selectedSymbol"
                  :data="orderBookData"
                  @order-click="handleOrderClick"
                />
              </div>
            </div>

            <!-- 持仓列表 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>持仓管理</h3>
                <p>管理和监控当前持仓</p>
              </div>
              <div class="demo-content">
                <PositionList
                  :positions="positionList"
                  @sell="handleSellPosition"
                  @view-detail="handleViewPositionDetail"
                />
              </div>
            </div>

            <!-- 快速下单 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>快速下单</h3>
                <p>一键快速交易功能</p>
              </div>
              <div class="demo-content">
                <QuickOrderForm
                  :symbol="selectedSymbol"
                  :preset-amounts="[1000, 5000, 10000, 50000]"
                  @quick-order="handleQuickOrder"
                />
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="数据组件" name="data">
          <div class="component-section">
            <!-- 虚拟表格 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>虚拟滚动表格</h3>
                <p>高性能大数据表格组件</p>
              </div>
              <div class="demo-content">
                <VirtualTable
                  :data="largeDataSet"
                  :columns="tableColumns"
                  :height="400"
                  :row-height="50"
                  @row-click="handleRowClick"
                />
              </div>
              <div class="demo-controls">
                <el-button @click="generateLargeData">生成大量数据 ({{ largeDataSet.length }} 条)</el-button>
                <el-button @click="clearData">清空数据</el-button>
              </div>
            </div>

            <!-- 股票卡片 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>股票信息卡片</h3>
                <p>展示股票基本信息和实时行情</p>
              </div>
              <div class="demo-content">
                <div class="stock-cards-grid">
                  <StockCard
                    v-for="stock in demoStocks"
                    :key="stock.symbol"
                    :stock="stock"
                    @click="handleStockCardClick"
                    @add-to-watchlist="handleAddToWatchlist"
                  />
                </div>
              </div>
            </div>

            <!-- 指标卡片 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>指标展示卡片</h3>
                <p>关键指标的可视化展示</p>
              </div>
              <div class="demo-content">
                <div class="metrics-grid">
                  <MetricCard
                    v-for="metric in demoMetrics"
                    :key="metric.id"
                    :title="metric.title"
                    :value="metric.value"
                    :change="metric.change"
                    :change-percent="metric.changePercent"
                    :trend="metric.trend"
                    :icon="metric.icon"
                  />
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="回测组件" name="backtest">
          <div class="component-section">
            <!-- 回测表单 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>回测配置表单</h3>
                <p>设置回测参数和策略配置</p>
              </div>
              <div class="demo-content">
                <BacktestForm
                  @submit="handleBacktestSubmit"
                  @strategy-change="handleStrategyChange"
                />
              </div>
            </div>

            <!-- 策略卡片 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>策略展示卡片</h3>
                <p>展示策略信息和性能指标</p>
              </div>
              <div class="demo-content">
                <div class="strategy-cards-grid">
                  <StrategyCard
                    v-for="strategy in demoStrategies"
                    :key="strategy.id"
                    :strategy="strategy"
                    @run="handleRunStrategy"
                    @edit="handleEditStrategy"
                    @delete="handleDeleteStrategy"
                  />
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="通用组件" name="common">
          <div class="component-section">
            <!-- 按钮组件 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>自定义按钮组件</h3>
                <p>各种样式和状态的按钮</p>
              </div>
              <div class="demo-content">
                <div class="button-demo">
                  <AppButton type="primary" @click="showMessage('Primary')">
                    主要按钮
                  </AppButton>
                  <AppButton type="success" @click="showMessage('Success')">
                    成功按钮
                  </AppButton>
                  <AppButton type="warning" @click="showMessage('Warning')">
                    警告按钮
                  </AppButton>
                  <AppButton type="danger" @click="showMessage('Danger')">
                    危险按钮
                  </AppButton>
                  <AppButton type="info" @click="showMessage('Info')">
                    信息按钮
                  </AppButton>
                  <AppButton loading @click="showMessage('Loading')">
                    加载按钮
                  </AppButton>
                </div>
              </div>
            </div>

            <!-- 卡片组件 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>自定义卡片组件</h3>
                <p>各种样式的卡片容器</p>
              </div>
              <div class="demo-content">
                <div class="card-demo">
                  <AppCard title="基础卡片" class="demo-card-item">
                    <p>这是一个基础的卡片组件，包含标题和内容区域。</p>
                  </AppCard>
                  
                  <AppCard title="带操作的卡片" class="demo-card-item">
                    <template #extra>
                      <el-button size="small" text>更多</el-button>
                    </template>
                    <p>这是一个带有额外操作按钮的卡片。</p>
                  </AppCard>
                  
                  <AppCard shadow="hover" class="demo-card-item">
                    <template #header>
                      <div class="card-header">
                        <span>悬停阴影卡片</span>
                        <el-tag size="small">新</el-tag>
                      </div>
                    </template>
                    <p>鼠标悬停时显示阴影效果的卡片。</p>
                  </AppCard>
                </div>
              </div>
            </div>

            <!-- 模态框组件 -->
            <div class="demo-card">
              <div class="demo-header">
                <h3>自定义模态框</h3>
                <p>各种类型的模态框和对话框</p>
              </div>
              <div class="demo-content">
                <div class="modal-demo">
                  <el-button @click="showBasicModal">基础模态框</el-button>
                  <el-button @click="showFormModal">表单模态框</el-button>
                  <el-button @click="showConfirmModal">确认对话框</el-button>
                  <el-button @click="showFullscreenModal">全屏模态框</el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 模态框实例 -->
    <AppModal
      v-model="modalVisible"
      :title="modalTitle"
      :width="modalWidth"
      :fullscreen="modalFullscreen"
      @confirm="handleModalConfirm"
      @cancel="handleModalCancel"
    >
      <div v-if="modalType === 'basic'">
        <p>这是一个基础的模态框内容。</p>
        <p>可以在这里放置任何内容。</p>
      </div>
      
      <div v-else-if="modalType === 'form'">
        <el-form :model="modalForm" label-width="80px">
          <el-form-item label="名称">
            <el-input v-model="modalForm.name" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="modalForm.description" type="textarea" />
          </el-form-item>
        </el-form>
      </div>
      
      <div v-else-if="modalType === 'confirm'">
        <p>确定要执行此操作吗？</p>
        <p>此操作不可撤销。</p>
      </div>
      
      <div v-else-if="modalType === 'fullscreen'">
        <h2>全屏模态框</h2>
        <p>这是一个全屏显示的模态框。</p>
        <div class="fullscreen-content">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="content-section">
                <h3>左侧内容</h3>
                <p>这里可以放置图表、表格等复杂内容。</p>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="content-section">
                <h3>右侧内容</h3>
                <p>这里可以放置表单、控制面板等。</p>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </AppModal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 导入组件
import KLineChart from '@/components/charts/KLineChart/index.vue'
import DepthChart from '@/components/charts/DepthChart/index.vue'
import AssetTrendChart from '@/components/charts/AssetTrendChart.vue'
import PositionPieChart from '@/components/charts/PositionPieChart.vue'
import OrderForm from '@/components/trading/OrderForm/index.vue'
import OrderBook from '@/components/trading/OrderBook.vue'
import PositionList from '@/components/trading/PositionList.vue'
import QuickOrderForm from '@/components/trading/QuickOrderForm.vue'
import VirtualTable from '@/components/common/VirtualTable/index.vue'
import StockCard from '@/components/market/StockCard.vue'
import MetricCard from '@/components/widgets/MetricCard.vue'
import BacktestForm from '@/components/backtest/BacktestForm.vue'
import StrategyCard from '@/components/strategy/StrategyCard/StrategyCard.vue'
import AppButton from '@/components/common/AppButton/index.vue'
import AppCard from '@/components/common/AppCard/index.vue'
import AppModal from '@/components/common/AppModal/index.vue'

// 状态管理
const activeTab = ref('charts')
const selectedSymbol = ref('000001')
const selectedSymbolName = ref('平安银行')

// 模态框状态
const modalVisible = ref(false)
const modalTitle = ref('')
const modalWidth = ref('600px')
const modalFullscreen = ref(false)
const modalType = ref('basic')
const modalForm = reactive({
  name: '',
  description: ''
})

// 演示数据
const demoStocks = ref([
  {
    symbol: '000001',
    name: '平安银行',
    currentPrice: 12.85,
    change: 0.15,
    changePercent: 1.18,
    volume: 125896547,
    turnover: 1618754123.45,
    high: 12.96,
    low: 12.68,
    open: 12.70
  },
  {
    symbol: '000002',
    name: '万科A',
    currentPrice: 18.45,
    change: -0.25,
    changePercent: -1.34,
    volume: 89654321,
    turnover: 1654789123.67,
    high: 18.78,
    low: 18.32,
    open: 18.65
  },
  {
    symbol: '600036',
    name: '招商银行',
    currentPrice: 45.67,
    change: 0.78,
    changePercent: 1.74,
    volume: 67891234,
    turnover: 3098765432.11,
    high: 45.89,
    low: 44.56,
    open: 44.89
  }
])

const demoMetrics = ref([
  {
    id: 1,
    title: '总资产',
    value: 1250000,
    change: 15000,
    changePercent: 1.22,
    trend: 'up',
    icon: 'Money'
  },
  {
    id: 2,
    title: '今日盈亏',
    value: 8500,
    change: 8500,
    changePercent: 0.68,
    trend: 'up',
    icon: 'TrendCharts'
  },
  {
    id: 3,
    title: '持仓市值',
    value: 980000,
    change: -2300,
    changePercent: -0.23,
    trend: 'down',
    icon: 'PieChart'
  },
  {
    id: 4,
    title: '可用资金',
    value: 270000,
    change: 17300,
    changePercent: 6.84,
    trend: 'up',
    icon: 'Wallet'
  }
])

const demoStrategies = ref([
  {
    id: 1,
    name: '双均线策略',
    description: '基于5日和20日均线的交叉策略',
    totalReturn: 15.68,
    annualReturn: 12.45,
    maxDrawdown: -8.32,
    sharpeRatio: 1.85,
    winRate: 0.68,
    status: 'running'
  },
  {
    id: 2,
    name: 'RSI反转策略',
    description: '基于RSI指标的超买超卖反转策略',
    totalReturn: 22.34,
    annualReturn: 18.76,
    maxDrawdown: -12.45,
    sharpeRatio: 2.12,
    winRate: 0.72,
    status: 'stopped'
  }
])

// 大数据集
const largeDataSet = ref([])
const tableColumns = ref([
  { key: 'symbol', title: '股票代码', width: 100 },
  { key: 'name', title: '股票名称', width: 150 },
  { key: 'price', title: '当前价格', width: 100 },
  { key: 'change', title: '涨跌幅', width: 100 },
  { key: 'volume', title: '成交量', width: 120 },
  { key: 'turnover', title: '成交额', width: 150 }
])

// 其他演示数据
const depthData = ref({
  bids: [
    { price: 12.84, volume: 15600 },
    { price: 12.83, volume: 23400 },
    { price: 12.82, volume: 18900 },
    { price: 12.81, volume: 31200 },
    { price: 12.80, volume: 45600 }
  ],
  asks: [
    { price: 12.85, volume: 12300 },
    { price: 12.86, volume: 19800 },
    { price: 12.87, volume: 27600 },
    { price: 12.88, volume: 15900 },
    { price: 12.89, volume: 33400 }
  ]
})

const orderBookData = ref({
  bids: [
    { price: 12.84, volume: 15600, orders: 156 },
    { price: 12.83, volume: 23400, orders: 234 },
    { price: 12.82, volume: 18900, orders: 189 }
  ],
  asks: [
    { price: 12.85, volume: 12300, orders: 123 },
    { price: 12.86, volume: 19800, orders: 198 },
    { price: 12.87, volume: 27600, orders: 276 }
  ]
})

const positionList = ref([
  {
    symbol: '000001',
    name: '平安银行',
    quantity: 1000,
    availableQuantity: 1000,
    avgPrice: 12.30,
    currentPrice: 12.85,
    marketValue: 12850,
    unrealizedPnl: 550,
    unrealizedPnlPercent: 4.47
  },
  {
    symbol: '600036',
    name: '招商银行',
    quantity: 500,
    availableQuantity: 500,
    avgPrice: 46.20,
    currentPrice: 45.67,
    marketValue: 22835,
    unrealizedPnl: -265,
    unrealizedPnlPercent: -1.15
  }
])

const assetTrendData = ref([
  { date: '2024-01-01', value: 1000000 },
  { date: '2024-01-02', value: 1008500 },
  { date: '2024-01-03', value: 995600 },
  { date: '2024-01-04', value: 1012300 },
  { date: '2024-01-05', value: 1025600 },
  { date: '2024-01-06', value: 1018900 },
  { date: '2024-01-07', value: 1034500 }
])

const positionData = ref([
  { name: '平安银行', value: 12850, percent: 52.1 },
  { name: '招商银行', value: 22835, percent: 47.9 }
])

// 方法
const generateLargeData = () => {
  const data = []
  for (let i = 0; i < 10000; i++) {
    data.push({
      symbol: `${String(i).padStart(6, '0')}`,
      name: `股票${i}`,
      price: (Math.random() * 100 + 10).toFixed(2),
      change: ((Math.random() - 0.5) * 10).toFixed(2),
      volume: Math.floor(Math.random() * 1000000),
      turnover: (Math.random() * 10000000).toFixed(2)
    })
  }
  largeDataSet.value = data
  ElMessage.success(`已生成 ${data.length} 条数据`)
}

const clearData = () => {
  largeDataSet.value = []
  ElMessage.info('数据已清空')
}

const showMessage = (type: string) => {
  ElMessage.success(`点击了 ${type} 按钮`)
}

const showBasicModal = () => {
  modalType.value = 'basic'
  modalTitle.value = '基础模态框'
  modalWidth.value = '600px'
  modalFullscreen.value = false
  modalVisible.value = true
}

const showFormModal = () => {
  modalType.value = 'form'
  modalTitle.value = '表单模态框'
  modalWidth.value = '600px'
  modalFullscreen.value = false
  modalForm.name = ''
  modalForm.description = ''
  modalVisible.value = true
}

const showConfirmModal = () => {
  modalType.value = 'confirm'
  modalTitle.value = '确认操作'
  modalWidth.value = '400px'
  modalFullscreen.value = false
  modalVisible.value = true
}

const showFullscreenModal = () => {
  modalType.value = 'fullscreen'
  modalTitle.value = '全屏模态框'
  modalWidth.value = '90%'
  modalFullscreen.value = true
  modalVisible.value = true
}

const handleModalConfirm = () => {
  ElMessage.success('模态框确认操作')
  modalVisible.value = false
}

const handleModalCancel = () => {
  modalVisible.value = false
}

// 事件处理
const handlePeriodChange = (period: string) => {
  ElMessage.info(`切换到 ${period} 周期`)
}

const handleDataUpdate = (data: any) => {
  console.log('K线数据更新:', data)
}

const handleOrderSubmit = (orderData: any) => {
  ElMessage.success(`订单提交成功: ${JSON.stringify(orderData)}`)
}

const handleStockSelect = (stock: any) => {
  selectedSymbol.value = stock.symbol
  selectedSymbolName.value = stock.name
  ElMessage.info(`选择股票: ${stock.name}`)
}

const handleOrderClick = (order: any) => {
  ElMessage.info(`点击订单: 价格 ${order.price}, 数量 ${order.volume}`)
}

const handleSellPosition = (position: any) => {
  ElMessage.warning(`卖出持仓: ${position.name}`)
}

const handleViewPositionDetail = (position: any) => {
  ElMessage.info(`查看持仓详情: ${position.name}`)
}

const handleQuickOrder = (orderData: any) => {
  ElMessage.success(`快速下单: ${JSON.stringify(orderData)}`)
}

const handleRowClick = (row: any) => {
  ElMessage.info(`点击行: ${row.name}`)
}

const handleStockCardClick = (stock: any) => {
  selectedSymbol.value = stock.symbol
  selectedSymbolName.value = stock.name
  ElMessage.info(`选择股票卡片: ${stock.name}`)
}

const handleAddToWatchlist = (stock: any) => {
  ElMessage.success(`添加到自选股: ${stock.name}`)
}

const handleBacktestSubmit = (config: any) => {
  ElMessage.success(`回测配置提交: ${JSON.stringify(config)}`)
}

const handleStrategyChange = (strategy: any) => {
  ElMessage.info(`策略变更: ${strategy.name}`)
}

const handleRunStrategy = (strategy: any) => {
  ElMessage.success(`运行策略: ${strategy.name}`)
}

const handleEditStrategy = (strategy: any) => {
  ElMessage.info(`编辑策略: ${strategy.name}`)
}

const handleDeleteStrategy = (strategy: any) => {
  ElMessageBox.confirm(`确定要删除策略 "${strategy.name}" 吗？`, '确认删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success(`删除策略: ${strategy.name}`)
  }).catch(() => {
    ElMessage.info('取消删除')
  })
}

// 初始化
onMounted(() => {
  generateLargeData()
})
</script>

<style scoped>
.component-showcase {
  padding: 20px;
  background: #f5f5f5;
  min-height: 100vh;
}

.showcase-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 40px 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.showcase-header h1 {
  font-size: 32px;
  color: #333;
  margin: 0 0 10px 0;
}

.showcase-header p {
  font-size: 16px;
  color: #666;
  margin: 0;
}

.showcase-nav {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.component-section {
  padding: 20px 0;
}

.demo-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 1px solid #e8e8e8;
}

.demo-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.demo-header h3 {
  font-size: 18px;
  color: #333;
  margin: 0 0 8px 0;
}

.demo-header p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.demo-content {
  margin-bottom: 16px;
}

.demo-controls {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 12px;
  align-items: center;
}

.trading-demo {
  max-width: 400px;
}

.stock-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
}

.strategy-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.button-demo {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.card-demo {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.demo-card-item {
  min-height: 120px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-demo {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.fullscreen-content {
  margin-top: 20px;
}

.content-section {
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
  min-height: 200px;
}

.content-section h3 {
  margin-top: 0;
  color: #333;
}

@media (max-width: 768px) {
  .component-showcase {
    padding: 10px;
  }
  
  .demo-card {
    padding: 16px;
  }
  
  .stock-cards-grid,
  .metrics-grid,
  .strategy-cards-grid,
  .card-demo {
    grid-template-columns: 1fr;
  }
  
  .button-demo,
  .modal-demo {
    flex-direction: column;
  }
  
  .demo-controls {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>