<template>
  <div class="trading-terminal">
    <!-- 顶部工具栏 -->
    <div class="terminal-header">
      <div class="symbol-selector">
        <el-autocomplete
          v-model="selectedSymbol"
          :fetch-suggestions="searchStocks"
          placeholder="搜索股票代码或名称"
          style="width: 300px"
          @select="handleSymbolSelect"
        >
          <template #default="{ item }">
            <div class="stock-suggestion">
              <span class="stock-code">{{ item.symbol }}</span>
              <span class="stock-name">{{ item.name }}</span>
              <span class="stock-price" :class="getPriceClass(item.changePercent)">
                {{ formatPrice(item.currentPrice) }}
              </span>
            </div>
          </template>
        </el-autocomplete>
      </div>
      
      <div class="terminal-actions">
        <el-button-group>
          <el-button 
            :type="layout === 'standard' ? 'primary' : 'default'"
            @click="layout = 'standard'"
          >
            标准布局
          </el-button>
          <el-button 
            :type="layout === 'professional' ? 'primary' : 'default'"
            @click="layout = 'professional'"
          >
            专业布局
          </el-button>
        </el-button-group>
        
        <el-button @click="toggleFullscreen">
          <el-icon><FullScreen /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="terminal-content" :class="`layout-${layout}`">
      <!-- 左侧：图表区域 -->
      <div class="chart-section">
        <div class="chart-container">
          <KLineChart
            v-if="currentStock"
            :symbol="currentStock.symbol"
            :symbol-name="currentStock.name"
            height="400px"
            @period-change="handlePeriodChange"
            @data-update="handleChartDataUpdate"
          />
          <div v-else class="chart-placeholder">
            <el-empty description="请选择股票查看图表" />
          </div>
        </div>
        
        <!-- 图表下方的市场信息 -->
        <div class="market-info-tabs">
          <el-tabs v-model="activeMarketTab" type="card">
            <el-tab-pane label="盘口" name="orderbook">
              <OrderBook 
                v-if="currentStock"
                :symbol="currentStock.symbol"
                :height="200"
              />
            </el-tab-pane>
            
            <el-tab-pane label="成交明细" name="trades">
              <div class="trade-details">
                <div class="trade-header">
                  <span>时间</span>
                  <span>价格</span>
                  <span>数量</span>
                  <span>方向</span>
                </div>
                <div class="trade-list">
                  <div 
                    v-for="trade in recentTrades" 
                    :key="trade.id"
                    class="trade-item"
                  >
                    <span class="trade-time">{{ formatTime(trade.timestamp) }}</span>
                    <span 
                      class="trade-price"
                      :class="getPriceClass(trade.changePercent)"
                    >
                      {{ formatPrice(trade.price) }}
                    </span>
                    <span class="trade-volume">{{ formatVolume(trade.volume) }}</span>
                    <span 
                      class="trade-direction"
                      :class="trade.direction === 'buy' ? 'text-red-500' : 'text-green-500'"
                    >
                      {{ trade.direction === 'buy' ? '买' : '卖' }}
                    </span>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            
            <el-tab-pane label="资金流向" name="moneyflow">
              <div class="money-flow">
                <div class="flow-summary">
                  <div class="flow-item">
                    <span class="flow-label">主力净流入</span>
                    <span class="flow-value text-red-500">+1.23亿</span>
                  </div>
                  <div class="flow-item">
                    <span class="flow-label">超大单净流入</span>
                    <span class="flow-value text-red-500">+0.85亿</span>
                  </div>
                  <div class="flow-item">
                    <span class="flow-label">大单净流入</span>
                    <span class="flow-value text-red-500">+0.38亿</span>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>

      <!-- 右侧：交易和信息区域 -->
      <div class="trading-section">
        <!-- 股票信息卡片 -->
        <div v-if="currentStock" class="stock-info-card">
          <div class="stock-header">
            <div class="stock-basic">
              <h3 class="stock-name">{{ currentStock.name }}</h3>
              <span class="stock-code">{{ currentStock.symbol }}</span>
            </div>
            <div class="stock-status">
              <span class="trading-status">{{ getTradingStatus() }}</span>
            </div>
          </div>
          
          <div class="stock-price">
            <div class="current-price">
              <span 
                class="price-value"
                :class="getPriceClass(currentQuote?.changePercent || 0)"
              >
                {{ formatPrice(currentQuote?.price || 0) }}
              </span>
              <span 
                class="price-change"
                :class="getPriceClass(currentQuote?.changePercent || 0)"
              >
                {{ formatChange(currentQuote?.change || 0, currentQuote?.changePercent || 0) }}
              </span>
            </div>
            
            <div class="price-range">
              <div class="range-item">
                <span class="range-label">今开</span>
                <span class="range-value">{{ formatPrice(currentQuote?.open || 0) }}</span>
              </div>
              <div class="range-item">
                <span class="range-label">最高</span>
                <span class="range-value text-red-500">{{ formatPrice(currentQuote?.high || 0) }}</span>
              </div>
              <div class="range-item">
                <span class="range-label">最低</span>
                <span class="range-value text-green-500">{{ formatPrice(currentQuote?.low || 0) }}</span>
              </div>
              <div class="range-item">
                <span class="range-label">昨收</span>
                <span class="range-value">{{ formatPrice(currentQuote?.close || 0) }}</span>
              </div>
              <div class="range-item">
                <span class="range-label">成交量</span>
                <span class="range-value">{{ formatVolume(currentQuote?.volume || 0) }}</span>
              </div>
              <div class="range-item">
                <span class="range-label">成交额</span>
                <span class="range-value">{{ formatAmount(currentQuote?.amount || 0) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 交易表单 -->
        <div class="order-form-section">
          <OrderForm
            :default-symbol="currentStock?.symbol"
            @submit="handleOrderSubmit"
            @stock-select="handleStockSelect"
          />
        </div>

        <!-- 交易信息标签页 -->
        <div class="trading-tabs">
          <el-tabs v-model="activeTradingTab" type="card">
            <el-tab-pane label="持仓" name="positions">
              <PositionList 
                :show-actions="true"
                @position-click="handlePositionClick"
              />
            </el-tab-pane>
            
            <el-tab-pane label="委托" name="orders">
              <div class="orders-section">
                <div class="orders-header">
                  <el-radio-group v-model="orderFilter" size="small">
                    <el-radio-button value="all">全部</el-radio-button>
                    <el-radio-button value="pending">待成交</el-radio-button>
                    <el-radio-button value="filled">已成交</el-radio-button>
                  </el-radio-group>
                  
                  <el-button 
                    size="small" 
                    type="danger"
                    @click="cancelAllOrders"
                    :disabled="!hasPendingOrders"
                  >
                    全部撤单
                  </el-button>
                </div>
                
                <div class="orders-list">
                  <div class="order-header">
                    <span>股票</span>
                    <span>方向</span>
                    <span>数量</span>
                    <span>价格</span>
                    <span>状态</span>
                    <span>操作</span>
                  </div>
                  
                  <div 
                    v-for="order in filteredOrders" 
                    :key="order.id"
                    class="order-item"
                  >
                    <span class="order-symbol">{{ order.symbol }}</span>
                    <span 
                      class="order-side"
                      :class="order.side === 'buy' ? 'text-red-500' : 'text-green-500'"
                    >
                      {{ order.side === 'buy' ? '买入' : '卖出' }}
                    </span>
                    <span class="order-quantity">{{ order.quantity }}</span>
                    <span class="order-price">{{ formatPrice(order.price || 0) }}</span>
                    <span class="order-status">
                      <el-tag 
                        :type="getOrderStatusType(order.status)"
                        size="small"
                      >
                        {{ getOrderStatusText(order.status) }}
                      </el-tag>
                    </span>
                    <span class="order-actions">
                      <el-button
                        v-if="order.status === 'pending'"
                        size="small"
                        type="danger"
                        text
                        @click="cancelOrder(order.id)"
                      >
                        撤单
                      </el-button>
                    </span>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            
            <el-tab-pane label="成交" name="trades">
              <div class="trades-section">
                <div class="trades-header">
                  <el-date-picker
                    v-model="tradeDate"
                    type="date"
                    placeholder="选择日期"
                    size="small"
                    @change="fetchTrades"
                  />
                </div>
                
                <div class="trades-list">
                  <div class="trade-header">
                    <span>时间</span>
                    <span>股票</span>
                    <span>方向</span>
                    <span>数量</span>
                    <span>价格</span>
                    <span>金额</span>
                  </div>
                  
                  <div 
                    v-for="trade in userTrades" 
                    :key="trade.id"
                    class="trade-item"
                  >
                    <span class="trade-time">{{ formatTime(trade.timestamp) }}</span>
                    <span class="trade-symbol">{{ trade.symbol }}</span>
                    <span 
                      class="trade-side"
                      :class="trade.side === 'buy' ? 'text-red-500' : 'text-green-500'"
                    >
                      {{ trade.side === 'buy' ? '买入' : '卖出' }}
                    </span>
                    <span class="trade-quantity">{{ trade.quantity }}</span>
                    <span class="trade-price">{{ formatPrice(trade.price) }}</span>
                    <span class="trade-amount">{{ formatCurrency(trade.amount) }}</span>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <div class="terminal-footer">
      <div class="connection-status">
        <el-icon 
          :class="marketStore.connected ? 'text-green-500' : 'text-red-500'"
        >
          <Connection />
        </el-icon>
        <span>{{ marketStore.connected ? '已连接' : '未连接' }}</span>
      </div>
      
      <div class="account-summary">
        <span>总资产: {{ formatCurrency(tradingStore.account.totalAssets) }}</span>
        <span>可用资金: {{ formatCurrency(tradingStore.account.availableCash) }}</span>
        <span 
          class="profit"
          :class="getPriceClass(tradingStore.account.dailyProfitPercent)"
        >
          今日盈亏: {{ formatChange(tradingStore.account.dailyProfit, tradingStore.account.dailyProfitPercent) }}
        </span>
      </div>
      
      <div class="market-time">
        <span>{{ currentTime }}</span>
        <span>{{ getMarketStatus() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { FullScreen, Connection } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import KLineChart from '@/components/charts/KLineChart/index.vue'
import OrderForm from '@/components/trading/OrderForm/index.vue'
import OrderBook from '@/components/trading/OrderBook.vue'
import PositionList from '@/components/trading/PositionList.vue'
import { useMarketStore } from '@/stores/modules/market'
import { useTradingStore } from '@/stores/modules/trading'
import { useFullscreen } from '@/composables/core/useFullscreen'
import { formatPrice, formatCurrency, formatVolume, formatAmount, formatChange, formatTime } from '@/utils/formatters'
import type { StockInfo } from '@/types/market'
import type { TradeRecord, OrderSubmitData } from '@/types/trading'

// Stores
const marketStore = useMarketStore()
const tradingStore = useTradingStore()

// 全屏控制
const { toggle: toggleFullscreen } = useFullscreen()

// 响应式状态
const selectedSymbol = ref('')
const currentStock = ref<StockInfo | null>(null)
const layout = ref<'standard' | 'professional'>('standard')
const activeMarketTab = ref('orderbook')
const activeTradingTab = ref('positions')
const orderFilter = ref('all')
const tradeDate = ref(new Date())
const currentTime = ref('')

// 模拟数据
const recentTrades = ref([
  { id: '1', timestamp: Date.now(), price: 12.58, volume: 1000, direction: 'buy', changePercent: 1.2 },
  { id: '2', timestamp: Date.now() - 1000, price: 12.57, volume: 500, direction: 'sell', changePercent: -0.1 }
])

const userTrades = ref<TradeRecord[]>([])

// 计算属性
const currentQuote = computed(() => {
  if (!currentStock.value) return null
  return marketStore.getQuote(currentStock.value.symbol)
})

const filteredOrders = computed(() => {
  let orders = tradingStore.orders
  
  if (orderFilter.value === 'pending') {
    orders = orders.filter(order => order.status === 'pending')
  } else if (orderFilter.value === 'filled') {
    orders = orders.filter(order => order.status === 'filled')
  }
  
  return orders
})

const hasPendingOrders = computed(() => {
  return tradingStore.orders.some(order => order.status === 'pending')
})

// 方法
const searchStocks = async (queryString: string, cb: (results: StockInfo[]) => void) => {
  if (!queryString) {
    cb([])
    return
  }
  
  try {
    const results = await marketStore.searchStocks(queryString)
    cb(results)
  } catch (_error) {
    console.error('搜索股票失败:', _error)
    cb([])
  }
}

const handleSymbolSelect = async (item: StockInfo) => {
  currentStock.value = item
  selectedSymbol.value = `${item.symbol} ${item.name}`
  
  // 设置为市场store的选中股票
  await marketStore.setSelectedStock(item)
}

const handleStockSelect = (stock: StockInfo) => {
  handleSymbolSelect(stock)
}

const handlePositionClick = (position: { symbol: string; [key: string]: unknown }) => {
  // 点击持仓时切换到对应股票
  if (position.symbol !== currentStock.value?.symbol) {
    marketStore.searchStocks(position.symbol).then(results => {
      if (results.length > 0) {
        handleSymbolSelect(results[0])
      }
    })
  }
}

const handleOrderSubmit = async (orderData: OrderSubmitData) => {
  try {
    await tradingStore.submitOrder(orderData)
    ElMessage.success('订单提交成功')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '订单提交失败')
  }
}

const handlePeriodChange = (period: string) => {
  console.log('时间周期变更:', period)
}

const handleChartDataUpdate = (data: Record<string, unknown>) => {
  console.log('图表数据更新:', data)
}

const cancelOrder = async (orderId: string) => {
  try {
    await ElMessageBox.confirm('确定要撤销这个订单吗？', '确认撤单', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await tradingStore.cancelOrder(orderId)
    ElMessage.success('订单撤销成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error instanceof Error ? error.message : '撤销订单失败')
    }
  }
}

const cancelAllOrders = async () => {
  try {
    await ElMessageBox.confirm('确定要撤销所有待成交订单吗？', '确认撤单', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const pendingOrderIds = tradingStore.orders
      .filter(order => order.status === 'pending')
      .map(order => order.id)
    
    await tradingStore.cancelMultipleOrders(pendingOrderIds)
    ElMessage.success('所有订单撤销成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error instanceof Error ? error.message : '撤销订单失败')
    }
  }
}

const fetchTrades = async () => {
  try {
    const dateStr = tradeDate.value.toISOString().split('T')[0]
    await tradingStore.fetchTrades({ startDate: dateStr, endDate: dateStr })
    userTrades.value = tradingStore.trades
  } catch {
    ElMessage.error('获取成交记录失败')
  }
}

const getPriceClass = (changePercent: number) => {
  if (changePercent > 0) return 'text-red-500'
  if (changePercent < 0) return 'text-green-500'
  return 'text-gray-500'
}

const getTradingStatus = () => {
  const now = new Date()
  const hour = now.getHours()
  const minute = now.getMinutes()
  const time = hour * 100 + minute
  
  if (time >= 930 && time <= 1130) return '上午交易'
  if (time >= 1300 && time <= 1500) return '下午交易'
  if (time >= 1500 && time <= 1700) return '盘后交易'
  return '休市'
}

const getMarketStatus = () => {
  return getTradingStatus()
}

const getOrderStatusType = (status: string) => {
  const types: Record<string, string> = {
    pending: 'warning',
    filled: 'success',
    cancelled: 'info',
    partial: 'primary'
  }
  return types[status] || 'info'
}

const getOrderStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '待成交',
    filled: '已成交',
    cancelled: '已撤销',
    partial: '部分成交'
  }
  return texts[status] || status
}

// 更新当前时间
const updateTime = () => {
  currentTime.value = new Date().toLocaleTimeString('zh-CN')
}

// 开始数据自动刷新
const startDataRefresh = () => {
  // 每3秒刷新一次数据
  const refreshInterval = setInterval(async () => {
    if (!document.hidden) { // 页面可见时才刷新
      try {
        await Promise.all([
          tradingStore.fetchAccount(),
          tradingStore.fetchPositions(),
          tradingStore.fetchOrders()
        ])
      } catch (error) {
        console.error('数据刷新失败:', error)
      }
    }
  }, 3000)
  
  // 页面卸载时清理定时器
  onUnmounted(() => {
    clearInterval(refreshInterval)
  })
}

// 生命周期
onMounted(async () => {
  try {
    // 初始化数据
    await Promise.all([
      marketStore.initialize(),
      tradingStore.initialize(),
      tradingStore.fetchAccount(),
      tradingStore.fetchPositions(),
      tradingStore.fetchOrders()
    ])
    
    // 获取成交记录
    await fetchTrades()
    
    // 设置定时更新
    startDataRefresh()
    
    // 启动时间更新
    updateTime()
    const timeInterval = setInterval(updateTime, 1000)
    
    onUnmounted(() => {
      clearInterval(timeInterval)
    })
    
  } catch (error) {
    ElMessage.error('初始化失败')
    console.error('交易终端初始化失败:', error)
  }
})

// 监听当前股票变化，更新实时行情
watch(currentStock, (newStock, oldStock) => {
  if (oldStock) {
    marketStore.unsubscribeQuote(oldStock.symbol)
  }
  
  if (newStock) {
    marketStore.subscribeQuote(newStock.symbol)
  }
}, { immediate: true })
</script>

<style scoped>
.trading-terminal {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.symbol-selector {
  flex: 1;
  max-width: 400px;
}

.stock-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.stock-code {
  font-weight: 600;
  color: #333;
}

.stock-name {
  color: #666;
  margin-left: 8px;
}

.stock-price {
  font-weight: 600;
}

.terminal-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.terminal-content {
  display: flex;
  flex: 1;
  gap: 16px;
  padding: 16px;
  min-height: 0;
}

.layout-standard .chart-section {
  flex: 2;
}

.layout-standard .trading-section {
  flex: 1;
  min-width: 400px;
}

.layout-professional .chart-section {
  flex: 3;
}

.layout-professional .trading-section {
  flex: 1;
  min-width: 350px;
}

.chart-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chart-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chart-placeholder {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.market-info-tabs {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.trade-details {
  padding: 16px;
}

.trade-header {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #e8e8e8;
  font-weight: 600;
  color: #666;
}

.trade-list {
  max-height: 200px;
  overflow-y: auto;
}

.trade-item {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.money-flow {
  padding: 16px;
}

.flow-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.flow-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.flow-label {
  color: #666;
}

.flow-value {
  font-weight: 600;
}

.trading-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stock-info-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.stock-basic h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.stock-code {
  color: #666;
  font-size: 14px;
}

.trading-status {
  font-size: 12px;
  color: #666;
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
}

.stock-price {
  margin-bottom: 16px;
}

.current-price {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}

.price-value {
  font-size: 24px;
  font-weight: 600;
}

.price-change {
  font-size: 16px;
  font-weight: 500;
}

.price-range {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.range-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 14px;
}

.range-label {
  color: #666;
}

.range-value {
  font-weight: 500;
}

.order-form-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.trading-tabs {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  flex: 1;
  min-height: 0;
}

.orders-section,
.trades-section {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.orders-header,
.trades-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.orders-list,
.trades-list {
  flex: 1;
  overflow-y: auto;
}

.order-header,
.trade-header {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #e8e8e8;
  font-weight: 600;
  color: #666;
  font-size: 14px;
}

.order-item,
.trade-item {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
  align-items: center;
}

.terminal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: white;
  border-top: 1px solid #e8e8e8;
  font-size: 14px;
}

.connection-status,
.account-summary,
.market-time {
  display: flex;
  align-items: center;
  gap: 8px;
}

.account-summary {
  gap: 16px;
}

.profit {
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .terminal-content {
    flex-direction: column;
  }
  
  .layout-standard .chart-section,
  .layout-professional .chart-section {
    flex: none;
  }
  
  .layout-standard .trading-section,
  .layout-professional .trading-section {
    flex: none;
    min-width: auto;
  }
}

@media (max-width: 768px) {
  .terminal-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .symbol-selector {
    max-width: none;
  }
  
  .terminal-actions {
    justify-content: space-between;
  }
  
  .terminal-content {
    padding: 8px;
  }
  
  .price-range {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .order-header,
  .order-item,
  .trade-header,
  .trade-item {
    grid-template-columns: repeat(3, 1fr);
    font-size: 12px;
  }
  
  .terminal-footer {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  
  .account-summary {
    justify-content: space-between;
    gap: 8px;
  }
}
</style> 