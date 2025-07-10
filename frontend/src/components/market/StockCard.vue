<!--
  股票卡片组件
  展示股票的基本信息和价格变化
-->
<template>
  <div 
    class="stock-card"
    :class="{ 
      'is-selected': selected,
      'is-rising': stock.change > 0,
      'is-falling': stock.change < 0
    }"
    @click="handleClick"
  >
    <!-- 股票基本信息 -->
    <div class="stock-header">
      <div class="stock-info">
        <h3 class="stock-symbol">{{ stock.symbol }}</h3>
        <p class="stock-name">{{ stock.name }}</p>
      </div>
      
      <div class="stock-actions">
        <el-button
          v-if="showActions"
          text
          :icon="isFavorited ? StarFilled : Star"
          :class="{ 'is-favorited': isFavorited }"
          @click.stop="toggleFavorite"
        />
        
        <el-dropdown
          v-if="showActions"
          @command="handleCommand"
          @click.stop
        >
          <el-button text :icon="MoreFilled" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="detail">查看详情</el-dropdown-item>
              <el-dropdown-item command="trade">快速交易</el-dropdown-item>
              <el-dropdown-item command="chart">查看K线</el-dropdown-item>
              <el-dropdown-item command="news">相关资讯</el-dropdown-item>
              <el-dropdown-item divided command="alert">设置预警</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 价格信息 -->
    <div class="price-section">
      <div class="current-price">
        <span class="price-value" :class="getPriceClass()">
          ¥{{ formatPrice(stock.currentPrice) }}
        </span>
        <div class="price-change">
          <span class="change-value" :class="getPriceClass()">
            {{ formatChange(stock.change) }}
          </span>
          <span class="change-percent" :class="getPriceClass()">
            {{ formatPercent(stock.changePercent) }}
          </span>
        </div>
      </div>
      
      <!-- 价格趋势迷你图 -->
      <div v-if="showMiniChart && priceHistory.length > 0" class="mini-chart">
        <canvas
          ref="chartCanvas"
          :width="chartWidth"
          :height="chartHeight"
        />
      </div>
    </div>

    <!-- 详细数据 -->
    <div v-if="showDetails" class="stock-details">
      <div class="detail-row">
        <span class="detail-label">开盘:</span>
        <span class="detail-value">¥{{ formatPrice(stock.openPrice) }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">最高:</span>
        <span class="detail-value price-up">¥{{ formatPrice(stock.high) }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">最低:</span>
        <span class="detail-value price-down">¥{{ formatPrice(stock.low) }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">成交量:</span>
        <span class="detail-value">{{ formatVolume(stock.volume) }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">成交额:</span>
        <span class="detail-value">{{ formatAmount(stock.turnover) }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">振幅:</span>
        <span class="detail-value">{{ formatPercent(calculateAmplitude()) }}</span>
      </div>
    </div>

    <!-- 技术指标 -->
    <div v-if="showIndicators && indicators.length > 0" class="indicators">
      <div
        v-for="indicator in indicators"
        :key="indicator.name"
        class="indicator-item"
      >
        <span class="indicator-name">{{ indicator.name }}:</span>
        <span 
          class="indicator-value"
          :class="getIndicatorClass(indicator.signal)"
        >
          {{ formatIndicatorValue(indicator.value) }}
        </span>
        <el-tag
          :type="getSignalTagType(indicator.signal)"
          size="small"
        >
          {{ getSignalText(indicator.signal) }}
        </el-tag>
      </div>
    </div>

    <!-- 交易状态 -->
    <div class="trading-status">
      <el-tag
        :type="getStatusTagType(stock.status)"
        size="small"
      >
        {{ getStatusText(stock.status) }}
      </el-tag>
      
      <span class="update-time">
        {{ formatTime(stock.timestamp) }}
      </span>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { 
  Star, StarFilled, MoreFilled, Loading 
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { formatPrice, formatPercent, formatTime } from '@/utils/formatters'
import type { QuoteData, TechnicalIndicator } from '@/types/market'

interface Props {
  stock: QuoteData
  selected?: boolean
  showActions?: boolean
  showDetails?: boolean
  showMiniChart?: boolean
  showIndicators?: boolean
  loading?: boolean
  priceHistory?: number[]
  indicators?: TechnicalIndicator[]
}

const props = withDefaults(defineProps<Props>(), {
  selected: false,
  showActions: true,
  showDetails: false,
  showMiniChart: false,
  showIndicators: false,
  loading: false,
  priceHistory: () => [],
  indicators: () => []
})

const emit = defineEmits<{
  (e: 'click', stock: QuoteData): void
  (e: 'favorite', stock: QuoteData, favorited: boolean): void
  (e: 'command', command: string, stock: QuoteData): void
}>()

// 图表相关
const chartCanvas = ref<HTMLCanvasElement>()
const chartWidth = 120
const chartHeight = 40

// 收藏状态
const isFavorited = ref(false)

// 计算属性
const getPriceClass = () => {
  if (props.stock.change > 0) return 'price-up'
  if (props.stock.change < 0) return 'price-down'
  return 'price-neutral'
}

// 格式化变化值
const formatChange = (change: number) => {
  const prefix = change > 0 ? '+' : ''
  return `${prefix}${change.toFixed(2)}`
}

// 格式化成交量
const formatVolume = (volume: number) => {
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(1)}亿`
  } else if (volume >= 10000) {
    return `${(volume / 10000).toFixed(1)}万`
  }
  return volume.toString()
}

// 格式化成交额
const formatAmount = (amount: number) => {
  if (amount >= 100000000) {
    return `${(amount / 100000000).toFixed(2)}亿`
  } else if (amount >= 10000) {
    return `${(amount / 10000).toFixed(2)}万`
  }
  return amount.toFixed(2)
}

// 计算振幅
const calculateAmplitude = () => {
  if (props.stock.previousClose <= 0) return 0
  return ((props.stock.high - props.stock.low) / props.stock.previousClose) * 100
}

// 获取交易状态标签类型
const getStatusTagType = (status: string) => {
  switch (status) {
    case 'trading': return 'success'
    case 'suspended': return 'warning'
    case 'closed': return 'info'
    default: return 'info'
  }
}

// 获取交易状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'trading': return '交易中'
    case 'suspended': return '停牌'
    case 'closed': return '收盘'
    default: return '未知'
  }
}

// 获取信号标签类型
const getSignalTagType = (signal: string) => {
  switch (signal) {
    case 'buy': return 'success'
    case 'sell': return 'danger'
    case 'hold': return 'warning'
    default: return 'info'
  }
}

// 获取信号文本
const getSignalText = (signal: string) => {
  switch (signal) {
    case 'buy': return '买入'
    case 'sell': return '卖出'
    case 'hold': return '持有'
    default: return '-'
  }
}

// 获取指标样式类
const getIndicatorClass = (signal: string) => {
  switch (signal) {
    case 'buy': return 'signal-buy'
    case 'sell': return 'signal-sell'
    default: return 'signal-neutral'
  }
}

// 格式化指标值
const formatIndicatorValue = (value: number | number[]) => {
  if (Array.isArray(value)) {
    return value.map(v => v.toFixed(2)).join(', ')
  }
  return value.toFixed(2)
}

// 绘制迷你图表
const drawMiniChart = () => {
  if (!chartCanvas.value || props.priceHistory.length === 0) return

  const canvas = chartCanvas.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 清空画布
  ctx.clearRect(0, 0, chartWidth, chartHeight)

  const prices = props.priceHistory
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const priceRange = maxPrice - minPrice

  if (priceRange === 0) return

  // 设置样式
  ctx.strokeStyle = props.stock.change >= 0 ? '#f56565' : '#48bb78'
  ctx.lineWidth = 1.5
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'

  // 绘制价格线
  ctx.beginPath()
  prices.forEach((price, index) => {
    const x = (index / (prices.length - 1)) * (chartWidth - 4) + 2
    const y = chartHeight - 2 - ((price - minPrice) / priceRange) * (chartHeight - 4)
    
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  ctx.stroke()

  // 绘制面积填充
  ctx.globalAlpha = 0.1
  ctx.fillStyle = ctx.strokeStyle
  ctx.lineTo(chartWidth - 2, chartHeight - 2)
  ctx.lineTo(2, chartHeight - 2)
  ctx.closePath()
  ctx.fill()
}

// 处理点击事件
const handleClick = () => {
  emit('click', props.stock)
}

// 切换收藏状态
const toggleFavorite = () => {
  isFavorited.value = !isFavorited.value
  emit('favorite', props.stock, isFavorited.value)
  
  ElMessage.success(
    isFavorited.value ? '已添加到自选股' : '已从自选股移除'
  )
}

// 处理下拉菜单命令
const handleCommand = (command: string) => {
  emit('command', command, props.stock)
}

// 监听价格历史变化
watch(() => props.priceHistory, () => {
  if (props.showMiniChart) {
    nextTick(() => {
      drawMiniChart()
    })
  }
}, { deep: true })

// 组件挂载时绘制图表
onMounted(() => {
  if (props.showMiniChart && props.priceHistory.length > 0) {
    nextTick(() => {
      drawMiniChart()
    })
  }
})
</script>

<style scoped>
.stock-card {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.stock-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.stock-card.is-selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.stock-card.is-rising {
  border-left: 4px solid #f56565;
}

.stock-card.is-falling {
  border-left: 4px solid #48bb78;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.stock-info {
  flex: 1;
}

.stock-symbol {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.stock-name {
  margin: 0;
  font-size: 12px;
  color: #666;
  line-height: 1.4;
}

.stock-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.stock-actions .el-button.is-favorited {
  color: #f56565;
}

.price-section {
  margin-bottom: 12px;
}

.current-price {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.price-value {
  font-size: 18px;
  font-weight: 700;
}

.price-change {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.change-value,
.change-percent {
  font-size: 12px;
  font-weight: 600;
}

.price-up {
  color: #f56565;
}

.price-down {
  color: #48bb78;
}

.price-neutral {
  color: #666;
}

.mini-chart {
  margin-top: 8px;
}

.stock-details {
  margin-bottom: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 4px 0;
}

.detail-label {
  font-size: 12px;
  color: #666;
}

.detail-value {
  font-size: 12px;
  font-weight: 500;
  color: #333;
}

.indicators {
  margin-bottom: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.indicator-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 6px 0;
  font-size: 12px;
}

.indicator-name {
  color: #666;
  min-width: 40px;
}

.indicator-value {
  font-weight: 500;
  margin-right: 8px;
}

.signal-buy {
  color: #f56565;
}

.signal-sell {
  color: #48bb78;
}

.signal-neutral {
  color: #666;
}

.trading-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.update-time {
  font-size: 11px;
  color: #999;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.loading-overlay .el-icon {
  font-size: 24px;
  color: #409eff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stock-card {
    padding: 12px;
  }
  
  .stock-symbol {
    font-size: 14px;
  }
  
  .price-value {
    font-size: 16px;
  }
  
  .current-price {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .price-change {
    align-items: flex-start;
  }
}
</style> 