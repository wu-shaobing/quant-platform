<template>
  <div class="real-time-position-list">
    <div class="list-header">
      <h3>实时持仓</h3>
      <div class="summary-info">
        <span>总市值: {{ formatCurrency(totalMarketValue) }}</span>
        <span>总盈亏: 
          <span :class="getPnlClass(totalPnl)">
            {{ formatCurrency(totalPnl) }}
          </span>
        </span>
      </div>
    </div>
    
    <div class="filter-bar">
      <el-input
        v-model="filterSymbol"
        placeholder="股票代码"
        size="small"
        style="width: 120px"
        clearable
        @input="handleFilterChange"
      />
      
      <el-select 
        v-model="filterType" 
        placeholder="持仓类型" 
        size="small"
        style="width: 120px; margin-left: 8px"
        @change="handleFilterChange"
      >
        <el-option label="全部" value="" />
        <el-option label="多头" value="long" />
        <el-option label="空头" value="short" />
      </el-select>
      
      <el-button 
        size="small" 
        @click="refreshPositions"
        :loading="loading"
        style="margin-left: 8px"
      >
        刷新
      </el-button>
    </div>
    
    <el-table
      :data="filteredPositions"
      size="small"
      height="400"
      :loading="loading"
      @row-click="handleRowClick"
      :row-class-name="getRowClassName"
    >
      <el-table-column prop="symbol" label="代码" width="80" />
      
      <el-table-column prop="name" label="名称" width="120" />
      
      <el-table-column label="方向" width="60">
        <template #default="{ row }">
          <el-tag 
            :type="row.direction === 'buy' ? 'danger' : 'success'" 
            size="small"
          >
            {{ row.direction === 'buy' ? '多头' : '空头' }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="volume" label="持仓量" width="80" />
      
      <el-table-column prop="available_volume" label="可用" width="80">
        <template #default="{ row }">
          {{ row.available_volume || row.volume }}
        </template>
      </el-table-column>
      
      <el-table-column prop="avg_price" label="成本价" width="80">
        <template #default="{ row }">
          {{ formatPrice(row.avg_price) }}
        </template>
      </el-table-column>
      
      <el-table-column label="现价" width="80">
        <template #default="{ row }">
          <span :class="getPriceClass(row.price_change_percent)">
            {{ formatPrice(row.current_price) }}
          </span>
        </template>
      </el-table-column>
      
      <el-table-column label="市值" width="100">
        <template #default="{ row }">
          {{ formatCurrency(row.market_value) }}
        </template>
      </el-table-column>
      
      <el-table-column label="盈亏" width="100">
        <template #default="{ row }">
          <div :class="getPnlClass(row.unrealized_pnl)">
            <div>{{ formatCurrency(row.unrealized_pnl) }}</div>
            <div class="pnl-percent">
              {{ formatPercent(row.unrealized_pnl_percent) }}
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column label="今日盈亏" width="100">
        <template #default="{ row }">
          <div :class="getPnlClass(row.daily_pnl)">
            <div>{{ formatCurrency(row.daily_pnl) }}</div>
            <div class="pnl-percent">
              {{ formatPercent(row.daily_pnl_percent) }}
            </div>
          </div>
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button
            type="text"
            size="small"
            @click.stop="handleQuickSell(row)"
            :disabled="!row.available_volume || row.available_volume <= 0"
          >
            快速卖出
          </el-button>
          
          <el-button
            type="text"
            size="small"
            @click.stop="handleViewDetail(row)"
          >
            详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 持仓详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="持仓详情"
      width="800px"
    >
      <PositionDetailPanel 
        v-if="selectedPosition"
        :position="selectedPosition"
        @trade="handleTrade"
      />
    </el-dialog>
    
    <!-- 快速交易弹窗 -->
    <el-dialog
      v-model="quickTradeDialogVisible"
      title="快速交易"
      width="400px"
    >
      <QuickOrderForm
        v-if="selectedPosition"
        :default-symbol="selectedPosition.symbol"
        :default-side="'sell'"
        :quick-trade-mode="true"
        @submit="handleQuickTradeSubmit"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useWebSocket } from '@/composables/useWebSocket'
import { useTradingStore } from '@/stores/modules/trading'
import { formatCurrency, formatPrice, formatPercent } from '@/utils/formatters'
import PositionDetailPanel from './PositionDetailPanel.vue'
import QuickOrderForm from './QuickOrderForm.vue'
import type { Position } from '@/types/trading'

// Stores
const tradingStore = useTradingStore()

// WebSocket连接
const {
  isConnected,
  connect,
  disconnect,
  send,
  on,
  off
} = useWebSocket({
  url: `${import.meta.env.VITE_WS_URL}/trading`,
  autoConnect: true
})

// 状态
const loading = ref(false)
const filterSymbol = ref('')
const filterType = ref('')
const detailDialogVisible = ref(false)
const quickTradeDialogVisible = ref(false)
const selectedPosition = ref<Position | null>(null)

// 计算属性
const filteredPositions = computed(() => {
  let positions = tradingStore.positions
  
  if (filterSymbol.value) {
    positions = positions.filter(pos => 
      pos.symbol.toLowerCase().includes(filterSymbol.value.toLowerCase())
    )
  }
  
  if (filterType.value) {
    positions = positions.filter(pos => {
      if (filterType.value === 'long') {
        return pos.direction === 'buy' && pos.volume > 0
      } else if (filterType.value === 'short') {
        return pos.direction === 'sell' && pos.volume > 0
      }
      return true
    })
  }
  
  return positions.filter(pos => pos.volume !== 0)
})

const totalMarketValue = computed(() => {
  return filteredPositions.value.reduce((sum, pos) => sum + (pos.market_value || 0), 0)
})

const totalPnl = computed(() => {
  return filteredPositions.value.reduce((sum, pos) => sum + (pos.unrealized_pnl || 0), 0)
})

// 方法
const getPnlClass = (value: number) => {
  if (value > 0) return 'pnl-positive'
  if (value < 0) return 'pnl-negative'
  return 'pnl-neutral'
}

const getPriceClass = (changePercent: number) => {
  if (changePercent > 0) return 'price-up'
  if (changePercent < 0) return 'price-down'
  return 'price-neutral'
}

const getRowClassName = ({ row }: { row: Position }) => {
  if (row.unrealized_pnl > 0) return 'profit-row'
  if (row.unrealized_pnl < 0) return 'loss-row'
  return ''
}

const handleFilterChange = () => {
  // 过滤条件改变时的处理
}

const refreshPositions = async () => {
  loading.value = true
  try {
    await tradingStore.fetchPositions()
  } catch (error) {
    ElMessage.error('刷新持仓失败')
  } finally {
    loading.value = false
  }
}

const handleRowClick = (row: Position) => {
  selectedPosition.value = row
  detailDialogVisible.value = true
}

const handleQuickSell = (position: Position) => {
  selectedPosition.value = position
  quickTradeDialogVisible.value = true
}

const handleViewDetail = (position: Position) => {
  selectedPosition.value = position
  detailDialogVisible.value = true
}

const handleTrade = (tradeData: any) => {
  // 处理交易请求
  ElMessage.info('交易功能开发中')
}

const handleQuickTradeSubmit = (orderData: any) => {
  quickTradeDialogVisible.value = false
  ElMessage.success('快速交易订单已提交')
}

// WebSocket事件处理
const setupWebSocketHandlers = () => {
  // 持仓更新
  on('position_update', (positionData: any) => {
    tradingStore.updatePosition(positionData)
  })
  
  // 实时行情更新持仓盈亏
  on('tick_update', (tickData: any) => {
    tradingStore.updatePositionPrice(tickData.symbol, tickData.data.price)
  })
  
  // 连接建立时订阅持仓更新
  on('connected', () => {
    send({
      type: 'subscribe_positions'
    })
    
    // 订阅所有持仓股票的实时行情
    const symbols = tradingStore.positions.map(pos => pos.symbol)
    if (symbols.length > 0) {
      send({
        type: 'subscribe_tick',
        symbols
      })
    }
  })
}

// 生命周期
onMounted(() => {
  setupWebSocketHandlers()
  refreshPositions()
})

onUnmounted(() => {
  disconnect()
})
</script>

<style scoped>
.real-time-position-list {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.list-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.summary-info {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #666;
}

.filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.pnl-positive {
  color: #f56c6c;
}

.pnl-negative {
  color: #67c23a;
}

.pnl-neutral {
  color: #909399;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.price-neutral {
  color: #909399;
}

.pnl-percent {
  font-size: 12px;
  opacity: 0.8;
}

:deep(.profit-row) {
  background-color: #fef0f0;
}

:deep(.loss-row) {
  background-color: #f0f9ff;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>
