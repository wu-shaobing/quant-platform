<template>
  <div class="position-management">
    <div class="management-header">
      <div class="header-left">
        <h3>持仓管理</h3>
        <el-tag type="info" size="small">
          总持仓: {{ positions.length }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button @click="refreshPositions" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button @click="closeAllPositions" :disabled="positions.length === 0">
          全部平仓
        </el-button>
      </div>
    </div>

    <!-- 持仓汇总 -->
    <div class="position-summary">
      <div class="summary-item">
        <span class="label">总持仓市值</span>
        <span class="value">{{ formatNumber(totalMarketValue) }}</span>
      </div>
      <div class="summary-item">
        <span class="label">浮动盈亏</span>
        <span class="value" :class="totalUnrealizedPnl >= 0 ? 'profit' : 'loss'">
          {{ totalUnrealizedPnl >= 0 ? '+' : '' }}{{ formatNumber(totalUnrealizedPnl) }}
        </span>
      </div>
      <div class="summary-item">
        <span class="label">已实现盈亏</span>
        <span class="value" :class="totalRealizedPnl >= 0 ? 'profit' : 'loss'">
          {{ totalRealizedPnl >= 0 ? '+' : '' }}{{ formatNumber(totalRealizedPnl) }}
        </span>
      </div>
      <div class="summary-item">
        <span class="label">总盈亏</span>
        <span class="value" :class="totalPnl >= 0 ? 'profit' : 'loss'">
          {{ totalPnl >= 0 ? '+' : '' }}{{ formatNumber(totalPnl) }}
        </span>
      </div>
    </div>

    <!-- 持仓表格 -->
    <div class="position-table">
      <el-table 
        :data="positions" 
        :loading="loading"
        height="400"
        stripe
      >
        <el-table-column prop="symbol" label="品种" width="100" />
        <el-table-column prop="direction" label="方向" width="60">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'long' ? 'success' : 'danger'" size="small">
              {{ row.direction === 'long' ? '多' : '空' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="持仓量" width="80" align="right" />
        <el-table-column prop="avgPrice" label="均价" width="80" align="right">
          <template #default="{ row }">
            {{ row.avgPrice.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="currentPrice" label="现价" width="80" align="right">
          <template #default="{ row }">
            {{ row.currentPrice.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="marketValue" label="市值" width="100" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.marketValue) }}
          </template>
        </el-table-column>
        <el-table-column prop="unrealizedPnl" label="浮动盈亏" width="100" align="right">
          <template #default="{ row }">
            <span :class="row.unrealizedPnl >= 0 ? 'profit' : 'loss'">
              {{ row.unrealizedPnl >= 0 ? '+' : '' }}{{ formatNumber(row.unrealizedPnl) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="unrealizedPnlPercent" label="盈亏比例" width="80" align="right">
          <template #default="{ row }">
            <span :class="row.unrealizedPnlPercent >= 0 ? 'profit' : 'loss'">
              {{ row.unrealizedPnlPercent >= 0 ? '+' : '' }}{{ row.unrealizedPnlPercent.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="openTime" label="开仓时间" width="140">
          <template #default="{ row }">
            {{ formatTime(row.openTime) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small"
              @click="partialClose(row)"
            >
              部分平仓
            </el-button>
            <el-button 
              type="danger" 
              size="small"
              @click="closePosition(row)"
            >
              全部平仓
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 部分平仓对话框 -->
    <el-dialog
      v-model="partialCloseDialogVisible"
      title="部分平仓"
      width="400px"
      @close="resetPartialCloseForm"
    >
      <el-form :model="partialCloseForm" :rules="partialCloseRules" ref="partialCloseFormRef" label-width="80px">
        <el-form-item label="品种">
          <el-input v-model="partialCloseForm.symbol" disabled />
        </el-form-item>
        <el-form-item label="方向">
          <el-input v-model="partialCloseForm.direction" disabled />
        </el-form-item>
        <el-form-item label="持仓量">
          <el-input v-model="partialCloseForm.totalQuantity" disabled />
        </el-form-item>
        <el-form-item label="平仓数量" prop="closeQuantity">
          <el-input-number
            v-model="partialCloseForm.closeQuantity"
            :precision="0"
            :step="100"
            :min="100"
            :max="partialCloseForm.totalQuantity"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="平仓类型" prop="closeType">
          <el-select v-model="partialCloseForm.closeType">
            <el-option label="市价平仓" value="market" />
            <el-option label="限价平仓" value="limit" />
          </el-select>
        </el-form-item>
        <el-form-item 
          v-if="partialCloseForm.closeType === 'limit'"
          label="平仓价格" 
          prop="closePrice"
        >
          <el-input-number
            v-model="partialCloseForm.closePrice"
            :precision="2"
            :step="0.01"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="partialCloseDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmPartialClose" :loading="closing">确认平仓</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import type { FormInstance } from 'element-plus'

interface Position {
  id: string
  symbol: string
  direction: 'long' | 'short'
  quantity: number
  avgPrice: number
  currentPrice: number
  marketValue: number
  unrealizedPnl: number
  unrealizedPnlPercent: number
  realizedPnl: number
  openTime: string
}

interface PartialCloseForm {
  symbol: string
  direction: string
  totalQuantity: number
  closeQuantity: number
  closeType: 'market' | 'limit'
  closePrice: number
}

const loading = ref(false)
const closing = ref(false)
const partialCloseDialogVisible = ref(false)
const partialCloseFormRef = ref<FormInstance>()

// 模拟持仓数据
const positions = ref<Position[]>([
  {
    id: 'POS001',
    symbol: 'IF2312',
    direction: 'long',
    quantity: 200,
    avgPrice: 3840.5,
    currentPrice: 3850.2,
    marketValue: 770040,
    unrealizedPnl: 1940,
    unrealizedPnlPercent: 0.25,
    realizedPnl: 0,
    openTime: '2024-01-15 09:30:00'
  },
  {
    id: 'POS002',
    symbol: 'IC2312',
    direction: 'short',
    quantity: 100,
    avgPrice: 5430.0,
    currentPrice: 5420.8,
    marketValue: 542080,
    unrealizedPnl: 920,
    unrealizedPnlPercent: 0.17,
    realizedPnl: 0,
    openTime: '2024-01-15 10:15:00'
  }
])

const partialCloseForm = reactive<PartialCloseForm>({
  symbol: '',
  direction: '',
  totalQuantity: 0,
  closeQuantity: 0,
  closeType: 'market',
  closePrice: 0
})

const partialCloseRules = {
  closeQuantity: [{ required: true, message: '请输入平仓数量', trigger: 'blur' }],
  closeType: [{ required: true, message: '请选择平仓类型', trigger: 'change' }],
  closePrice: [{ required: true, message: '请输入平仓价格', trigger: 'blur' }]
}

// 计算属性
const totalMarketValue = computed(() => {
  return positions.value.reduce((sum, pos) => sum + pos.marketValue, 0)
})

const totalUnrealizedPnl = computed(() => {
  return positions.value.reduce((sum, pos) => sum + pos.unrealizedPnl, 0)
})

const totalRealizedPnl = computed(() => {
  return positions.value.reduce((sum, pos) => sum + pos.realizedPnl, 0)
})

const totalPnl = computed(() => {
  return totalUnrealizedPnl.value + totalRealizedPnl.value
})

// 格式化数字
const formatNumber = (value: number): string => {
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 格式化时间
const formatTime = (time: string): string => {
  return new Date(time).toLocaleString('zh-CN')
}

// 刷新持仓
const refreshPositions = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 更新持仓数据（模拟价格变动）
    positions.value.forEach(pos => {
      const priceChange = (Math.random() - 0.5) * 10
      pos.currentPrice += priceChange
      pos.marketValue = pos.currentPrice * pos.quantity
      
      if (pos.direction === 'long') {
        pos.unrealizedPnl = (pos.currentPrice - pos.avgPrice) * pos.quantity
      } else {
        pos.unrealizedPnl = (pos.avgPrice - pos.currentPrice) * pos.quantity
      }
      
      pos.unrealizedPnlPercent = (pos.unrealizedPnl / (pos.avgPrice * pos.quantity)) * 100
    })
    
    ElMessage.success('持仓刷新成功')
  } catch (error) {
    ElMessage.error('持仓刷新失败')
  } finally {
    loading.value = false
  }
}

// 全部平仓
const closeAllPositions = async () => {
  try {
    await ElMessageBox.confirm('确定要平仓所有持仓吗？', '确认平仓', {
      type: 'warning'
    })
    
    loading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 清空持仓
    positions.value = []
    
    ElMessage.success('所有持仓已平仓')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('平仓失败')
    }
  } finally {
    loading.value = false
  }
}

// 部分平仓
const partialClose = (position: Position) => {
  partialCloseForm.symbol = position.symbol
  partialCloseForm.direction = position.direction === 'long' ? '多头' : '空头'
  partialCloseForm.totalQuantity = position.quantity
  partialCloseForm.closeQuantity = 0
  partialCloseForm.closeType = 'market'
  partialCloseForm.closePrice = position.currentPrice
  partialCloseDialogVisible.value = true
}

// 确认部分平仓
const confirmPartialClose = async () => {
  if (!partialCloseFormRef.value) return
  
  try {
    const valid = await partialCloseFormRef.value.validate()
    if (!valid) return
    
    closing.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 更新持仓
    const position = positions.value.find(p => p.symbol === partialCloseForm.symbol)
    if (position) {
      position.quantity -= partialCloseForm.closeQuantity
      position.marketValue = position.currentPrice * position.quantity
      
      if (position.direction === 'long') {
        position.unrealizedPnl = (position.currentPrice - position.avgPrice) * position.quantity
      } else {
        position.unrealizedPnl = (position.avgPrice - position.currentPrice) * position.quantity
      }
      
      position.unrealizedPnlPercent = (position.unrealizedPnl / (position.avgPrice * position.quantity)) * 100
      
      // 如果数量为0，移除持仓
      if (position.quantity === 0) {
        const index = positions.value.findIndex(p => p.id === position.id)
        positions.value.splice(index, 1)
      }
    }
    
    ElMessage.success('部分平仓成功')
    partialCloseDialogVisible.value = false
  } catch (error) {
    ElMessage.error('部分平仓失败')
  } finally {
    closing.value = false
  }
}

// 全部平仓
const closePosition = async (position: Position) => {
  try {
    await ElMessageBox.confirm(`确定要平仓 ${position.symbol} 的全部持仓吗？`, '确认平仓', {
      type: 'warning'
    })
    
    loading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 移除持仓
    const index = positions.value.findIndex(p => p.id === position.id)
    positions.value.splice(index, 1)
    
    ElMessage.success('持仓已平仓')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('平仓失败')
    }
  } finally {
    loading.value = false
  }
}

// 重置部分平仓表单
const resetPartialCloseForm = () => {
  partialCloseForm.symbol = ''
  partialCloseForm.direction = ''
  partialCloseForm.totalQuantity = 0
  partialCloseForm.closeQuantity = 0
  partialCloseForm.closeType = 'market'
  partialCloseForm.closePrice = 0
}

// 初始化
onMounted(() => {
  refreshPositions()
})
</script>

<style scoped>
.position-management {
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

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.header-right {
  display: flex;
  gap: 8px;
}

.position-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.summary-item .label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.summary-item .value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.summary-item .value.profit {
  color: #f56c6c;
}

.summary-item .value.loss {
  color: #67c23a;
}

.position-table {
  margin-top: 16px;
}

.profit {
  color: #f56c6c;
}

.loss {
  color: #67c23a;
}

@media (max-width: 768px) {
  .management-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .position-summary {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style> 