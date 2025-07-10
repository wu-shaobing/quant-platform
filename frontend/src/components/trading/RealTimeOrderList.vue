<template>
  <div class="real-time-order-list">
    <div class="list-header">
      <h3>实时订单</h3>
      <div class="connection-status">
        <el-tag 
          :type="connectionStatusType" 
          size="small"
          effect="dark"
        >
          {{ connectionStatusText }}
        </el-tag>
      </div>
    </div>
    
    <div class="filter-bar">
      <el-select 
        v-model="filterStatus" 
        placeholder="订单状态" 
        size="small"
        style="width: 120px"
        @change="handleFilterChange"
      >
        <el-option label="全部" value="" />
        <el-option label="待提交" value="pending" />
        <el-option label="已提交" value="submitted" />
        <el-option label="部分成交" value="partial_filled" />
        <el-option label="全部成交" value="all_filled" />
        <el-option label="已撤销" value="cancelled" />
        <el-option label="已拒绝" value="rejected" />
      </el-select>
      
      <el-input
        v-model="filterSymbol"
        placeholder="股票代码"
        size="small"
        style="width: 120px; margin-left: 8px"
        clearable
        @input="handleFilterChange"
      />
      
      <el-button 
        size="small" 
        @click="refreshOrders"
        :loading="loading"
        style="margin-left: 8px"
      >
        刷新
      </el-button>
    </div>
    
    <el-table
      :data="filteredOrders"
      size="small"
      height="400"
      :loading="loading"
      @row-click="handleRowClick"
    >
      <el-table-column prop="order_id" label="订单号" width="120" />
      
      <el-table-column prop="symbol" label="代码" width="80" />
      
      <el-table-column label="方向" width="60">
        <template #default="{ row }">
          <el-tag 
            :type="row.side === 'buy' ? 'danger' : 'success'" 
            size="small"
          >
            {{ row.side === 'buy' ? '买入' : '卖出' }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column label="类型" width="80">
        <template #default="{ row }">
          {{ getOrderTypeText(row.order_type) }}
        </template>
      </el-table-column>
      
      <el-table-column prop="price" label="价格" width="80">
        <template #default="{ row }">
          {{ row.order_type === 'market' ? '市价' : formatPrice(row.price) }}
        </template>
      </el-table-column>
      
      <el-table-column prop="quantity" label="数量" width="80" />
      
      <el-table-column prop="traded" label="成交" width="80">
        <template #default="{ row }">
          {{ row.traded || 0 }}
        </template>
      </el-table-column>
      
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag 
            :type="getStatusTagType(row.status)" 
            size="small"
          >
            {{ getOrderStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="order_time" label="时间" width="120">
        <template #default="{ row }">
          {{ formatTime(row.order_time) }}
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="canCancelOrder(row.status)"
            type="text"
            size="small"
            @click.stop="handleCancelOrder(row)"
            :loading="cancellingOrders.has(row.order_id)"
          >
            撤单
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
    
    <!-- 订单详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="订单详情"
      width="600px"
    >
      <OrderDetailPanel 
        v-if="selectedOrder"
        :order="selectedOrder"
        @cancel="handleCancelOrder"
        @modify="handleModifyOrder"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useWebSocket } from '@/composables/useWebSocket'
import { useTradingStore } from '@/stores/modules/trading'
import { formatPrice, formatTime } from '@/utils/formatters'
import OrderDetailPanel from './OrderDetailPanel.vue'
import type { Order } from '@/types/trading'

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
const filterStatus = ref('')
const filterSymbol = ref('')
const cancellingOrders = ref(new Set<string>())
const detailDialogVisible = ref(false)
const selectedOrder = ref<Order | null>(null)

// 计算属性
const connectionStatusType = computed(() => {
  return isConnected.value ? 'success' : 'danger'
})

const connectionStatusText = computed(() => {
  return isConnected.value ? '已连接' : '未连接'
})

const filteredOrders = computed(() => {
  let orders = tradingStore.orders
  
  if (filterStatus.value) {
    orders = orders.filter(order => order.status === filterStatus.value)
  }
  
  if (filterSymbol.value) {
    orders = orders.filter(order => 
      order.symbol.toLowerCase().includes(filterSymbol.value.toLowerCase())
    )
  }
  
  return orders.sort((a, b) => 
    new Date(b.order_time).getTime() - new Date(a.order_time).getTime()
  )
})

// 方法
const getOrderTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    'limit': '限价',
    'market': '市价',
    'stop': '止损',
    'stop-profit': '止盈'
  }
  return typeMap[type] || type
}

const getOrderStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '待提交',
    'submitting': '提交中',
    'submitted': '已提交',
    'partial_filled': '部分成交',
    'all_filled': '全部成交',
    'cancelled': '已撤销',
    'rejected': '已拒绝'
  }
  return statusMap[status] || status
}

const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    'pending': 'info',
    'submitting': 'warning',
    'submitted': 'primary',
    'partial_filled': 'warning',
    'all_filled': 'success',
    'cancelled': 'info',
    'rejected': 'danger'
  }
  return typeMap[status] || 'info'
}

const canCancelOrder = (status: string) => {
  return ['pending', 'submitting', 'submitted', 'partial_filled'].includes(status)
}

const handleFilterChange = () => {
  // 过滤条件改变时的处理
}

const refreshOrders = async () => {
  loading.value = true
  try {
    await tradingStore.fetchOrders()
  } catch (error) {
    ElMessage.error('刷新订单失败')
  } finally {
    loading.value = false
  }
}

const handleRowClick = (row: Order) => {
  selectedOrder.value = row
  detailDialogVisible.value = true
}

const handleCancelOrder = async (order: Order) => {
  try {
    await ElMessageBox.confirm(
      `确定要撤销订单 ${order.order_id} 吗？`,
      '撤销确认',
      {
        confirmButtonText: '确定撤销',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    cancellingOrders.value.add(order.order_id)
    
    // 通过WebSocket发送撤单请求
    if (isConnected.value) {
      send({
        type: 'cancel_order',
        order_id: order.order_id
      })
    } else {
      // 如果WebSocket未连接，使用HTTP API
      await tradingStore.cancelOrder(order.order_id)
      cancellingOrders.value.delete(order.order_id)
    }
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('撤单失败')
      cancellingOrders.value.delete(order.order_id)
    }
  }
}

const handleModifyOrder = (order: Order) => {
  // 修改订单逻辑
  ElMessage.info('修改订单功能开发中')
}

const handleViewDetail = (order: Order) => {
  selectedOrder.value = order
  detailDialogVisible.value = true
}

// WebSocket事件处理
const setupWebSocketHandlers = () => {
  // 订单状态更新
  on('order_update', (orderData: any) => {
    tradingStore.updateOrder(orderData)
    
    // 移除撤单loading状态
    if (orderData.status === 'cancelled') {
      cancellingOrders.value.delete(orderData.order_id)
    }
  })
  
  // 撤单结果
  on('order_cancel_result', (result: any) => {
    if (result.success) {
      ElMessage.success('撤单成功')
    } else {
      ElMessage.error(result.message || '撤单失败')
    }
    
    // 移除loading状态
    const orderId = result.order_id
    if (orderId) {
      cancellingOrders.value.delete(orderId)
    }
  })
  
  // 连接建立时订阅订单更新
  on('connected', () => {
    send({
      type: 'subscribe_orders'
    })
  })
}

// 生命周期
onMounted(() => {
  setupWebSocketHandlers()
  refreshOrders()
})

onUnmounted(() => {
  disconnect()
})
</script>

<style scoped>
.real-time-order-list {
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

.filter-bar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.el-table {
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
}
</style>
