<template>
  <div class="order-management">
    <div class="management-header">
      <div class="header-left">
        <el-button-group>
          <el-button :type="activeTab === 'pending' ? 'primary' : 'default'" @click="activeTab = 'pending'">
            待成交 ({{ pendingOrders.length }})
          </el-button>
          <el-button :type="activeTab === 'filled' ? 'primary' : 'default'" @click="activeTab = 'filled'">
            已成交 ({{ filledOrders.length }})
          </el-button>
          <el-button :type="activeTab === 'cancelled' ? 'primary' : 'default'" @click="activeTab = 'cancelled'">
            已撤销 ({{ cancelledOrders.length }})
          </el-button>
        </el-button-group>
      </div>
      <div class="header-right">
        <el-button @click="refreshOrders" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="cancelAllOrders" :disabled="pendingOrders.length === 0">
          全部撤销
        </el-button>
      </div>
    </div>

    <div class="order-table">
      <el-table 
        :data="currentOrders" 
        :loading="loading"
        height="400"
        stripe
      >
        <el-table-column prop="orderNo" label="订单号" width="120" />
        <el-table-column prop="symbol" label="品种" width="100" />
        <el-table-column prop="direction" label="方向" width="60">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'buy' ? 'success' : 'danger'" size="small">
              {{ row.direction === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="orderType" label="类型" width="80">
          <template #default="{ row }">
            {{ getOrderTypeText(row.orderType) }}
          </template>
        </el-table-column>
        <el-table-column prop="price" label="价格" width="80" align="right">
          <template #default="{ row }">
            {{ row.orderType === 'market' ? '市价' : row.price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="80" align="right" />
        <el-table-column prop="filledQuantity" label="已成交" width="80" align="right" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="委托时间" width="140">
          <template #default="{ row }">
            {{ formatTime(row.createTime) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'pending'"
              type="primary" 
              size="small"
              @click="modifyOrder(row)"
            >
              修改
            </el-button>
            <el-button 
              v-if="row.status === 'pending'"
              type="danger" 
              size="small"
              @click="cancelOrder(row)"
            >
              撤销
            </el-button>
            <el-button 
              v-if="row.status === 'filled'"
              type="info" 
              size="small"
              @click="viewOrderDetail(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 修改订单对话框 -->
    <el-dialog
      v-model="modifyDialogVisible"
      title="修改订单"
      width="400px"
      @close="resetModifyForm"
    >
      <el-form :model="modifyForm" :rules="modifyRules" ref="modifyFormRef" label-width="80px">
        <el-form-item label="订单号">
          <el-input v-model="modifyForm.orderNo" disabled />
        </el-form-item>
        <el-form-item label="品种">
          <el-input v-model="modifyForm.symbol" disabled />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number
            v-model="modifyForm.price"
            :precision="2"
            :step="0.01"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number
            v-model="modifyForm.quantity"
            :precision="0"
            :step="100"
            :min="100"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modifyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmModify" :loading="modifying">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- 订单详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="订单详情"
      width="600px"
    >
      <div class="order-detail" v-if="selectedOrder">
        <div class="detail-section">
          <h4>基本信息</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">订单号:</span>
              <span class="value">{{ selectedOrder.orderNo }}</span>
            </div>
            <div class="detail-item">
              <span class="label">品种:</span>
              <span class="value">{{ selectedOrder.symbol }}</span>
            </div>
            <div class="detail-item">
              <span class="label">方向:</span>
              <span class="value">{{ selectedOrder.direction === 'buy' ? '买入' : '卖出' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">类型:</span>
              <span class="value">{{ getOrderTypeText(selectedOrder.orderType) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">委托价格:</span>
              <span class="value">{{ selectedOrder.price.toFixed(2) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">委托数量:</span>
              <span class="value">{{ selectedOrder.quantity }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>成交信息</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">已成交数量:</span>
              <span class="value">{{ selectedOrder.filledQuantity }}</span>
            </div>
            <div class="detail-item">
              <span class="label">平均成交价:</span>
              <span class="value">{{ selectedOrder.avgPrice?.toFixed(2) || '--' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">成交金额:</span>
              <span class="value">{{ selectedOrder.filledAmount?.toFixed(2) || '--' }}</span>
            </div>
            <div class="detail-item">
              <span class="label">手续费:</span>
              <span class="value">{{ selectedOrder.commission?.toFixed(2) || '--' }}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>时间信息</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">委托时间:</span>
              <span class="value">{{ formatTime(selectedOrder.createTime) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">更新时间:</span>
              <span class="value">{{ formatTime(selectedOrder.updateTime) }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'

interface Order {
  orderNo: string
  symbol: string
  direction: 'buy' | 'sell'
  orderType: 'limit' | 'market' | 'stop' | 'takeProfit'
  price: number
  quantity: number
  filledQuantity: number
  status: 'pending' | 'filled' | 'cancelled' | 'partiallyFilled'
  createTime: string
  updateTime: string
  avgPrice?: number
  filledAmount?: number
  commission?: number
}

interface ModifyForm {
  orderNo: string
  symbol: string
  price: number
  quantity: number
}

const activeTab = ref<'pending' | 'filled' | 'cancelled'>('pending')
const loading = ref(false)
const modifying = ref(false)
const modifyDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const selectedOrder = ref<Order | null>(null)
const modifyFormRef = ref<FormInstance>()

// 模拟订单数据
const orders = ref<Order[]>([
  {
    orderNo: 'ORD001',
    symbol: 'IF2312',
    direction: 'buy',
    orderType: 'limit',
    price: 3850.0,
    quantity: 200,
    filledQuantity: 100,
    status: 'partiallyFilled',
    createTime: '2024-01-15 09:30:00',
    updateTime: '2024-01-15 09:35:00',
    avgPrice: 3849.5,
    filledAmount: 384950,
    commission: 15.4
  },
  {
    orderNo: 'ORD002',
    symbol: 'IC2312',
    direction: 'sell',
    orderType: 'market',
    price: 0,
    quantity: 100,
    filledQuantity: 100,
    status: 'filled',
    createTime: '2024-01-15 10:15:00',
    updateTime: '2024-01-15 10:15:30',
    avgPrice: 5420.2,
    filledAmount: 542020,
    commission: 21.68
  },
  {
    orderNo: 'ORD003',
    symbol: 'IH2312',
    direction: 'buy',
    orderType: 'limit',
    price: 2680.0,
    quantity: 300,
    filledQuantity: 0,
    status: 'cancelled',
    createTime: '2024-01-15 11:00:00',
    updateTime: '2024-01-15 11:30:00'
  }
])

const modifyForm = reactive<ModifyForm>({
  orderNo: '',
  symbol: '',
  price: 0,
  quantity: 0
})

const modifyRules = {
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }]
}

// 计算属性
const pendingOrders = computed(() => {
  return orders.value.filter(order => order.status === 'pending' || order.status === 'partiallyFilled')
})

const filledOrders = computed(() => {
  return orders.value.filter(order => order.status === 'filled')
})

const cancelledOrders = computed(() => {
  return orders.value.filter(order => order.status === 'cancelled')
})

const currentOrders = computed(() => {
  switch (activeTab.value) {
    case 'pending':
      return pendingOrders.value
    case 'filled':
      return filledOrders.value
    case 'cancelled':
      return cancelledOrders.value
    default:
      return []
  }
})

// 获取订单类型文本
const getOrderTypeText = (type: string): string => {
  const types = {
    limit: '限价',
    market: '市价',
    stop: '止损',
    takeProfit: '止盈'
  }
  return types[type] || type
}

// 获取状态类型
const getStatusType = (status: string): string => {
  const types = {
    pending: 'warning',
    filled: 'success',
    cancelled: 'info',
    partiallyFilled: 'primary'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string): string => {
  const texts = {
    pending: '待成交',
    filled: '已成交',
    cancelled: '已撤销',
    partiallyFilled: '部分成交'
  }
  return texts[status] || status
}

// 格式化时间
const formatTime = (time: string): string => {
  return new Date(time).toLocaleString('zh-CN')
}

// 刷新订单
const refreshOrders = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('订单刷新成功')
  } catch (error) {
    ElMessage.error('订单刷新失败')
  } finally {
    loading.value = false
  }
}

// 撤销所有订单
const cancelAllOrders = async () => {
  try {
    await ElMessageBox.confirm('确定要撤销所有待成交订单吗？', '确认撤销', {
      type: 'warning'
    })
    
    loading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 更新订单状态
    orders.value.forEach(order => {
      if (order.status === 'pending' || order.status === 'partiallyFilled') {
        order.status = 'cancelled'
        order.updateTime = new Date().toISOString()
      }
    })
    
    ElMessage.success('所有订单已撤销')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('撤销失败')
    }
  } finally {
    loading.value = false
  }
}

// 修改订单
const modifyOrder = (order: Order) => {
  modifyForm.orderNo = order.orderNo
  modifyForm.symbol = order.symbol
  modifyForm.price = order.price
  modifyForm.quantity = order.quantity
  modifyDialogVisible.value = true
}

// 确认修改
const confirmModify = async () => {
  if (!modifyFormRef.value) return
  
  try {
    const valid = await modifyFormRef.value.validate()
    if (!valid) return
    
    modifying.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 更新订单
    const order = orders.value.find(o => o.orderNo === modifyForm.orderNo)
    if (order) {
      order.price = modifyForm.price
      order.quantity = modifyForm.quantity
      order.updateTime = new Date().toISOString()
    }
    
    ElMessage.success('订单修改成功')
    modifyDialogVisible.value = false
  } catch (error) {
    ElMessage.error('订单修改失败')
  } finally {
    modifying.value = false
  }
}

// 撤销订单
const cancelOrder = async (order: Order) => {
  try {
    await ElMessageBox.confirm(`确定要撤销订单 ${order.orderNo} 吗？`, '确认撤销', {
      type: 'warning'
    })
    
    loading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 更新订单状态
    order.status = 'cancelled'
    order.updateTime = new Date().toISOString()
    
    ElMessage.success('订单已撤销')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('撤销失败')
    }
  } finally {
    loading.value = false
  }
}

// 查看订单详情
const viewOrderDetail = (order: Order) => {
  selectedOrder.value = order
  detailDialogVisible.value = true
}

// 重置修改表单
const resetModifyForm = () => {
  modifyForm.orderNo = ''
  modifyForm.symbol = ''
  modifyForm.price = 0
  modifyForm.quantity = 0
}

// 初始化
onMounted(() => {
  refreshOrders()
})
</script>

<style scoped>
.order-management {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.management-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.header-right {
  display: flex;
  gap: 8px;
}

.order-table {
  margin-top: 16px;
}

.order-detail {
  padding: 16px 0;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 8px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.detail-item .label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.detail-item .value {
  font-size: 14px;
  color: #303133;
}

@media (max-width: 768px) {
  .management-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style> 